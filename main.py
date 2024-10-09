from pydantic import BaseModel
from regulations import get_data
from fastapi import FastAPI, Depends, File, UploadFile
import uvicorn
from database import SessionLocal, engine
from glob import glob
from sqlalchemy.orm import Session
from config import settings
from typing import List
import app.database.models.models as models
from embed_files import embed_files, embed_text
from app.database.models.models import Sop, SopSegment, Regulation, RegulationSegment, SopOnRegulation, SopSegmentOnRegulationSegment, Setup
from sqladmin import Admin, ModelView, BaseView, expose
from fastapi_utilities import repeat_every
import xml.etree.ElementTree as ET
from sqlalchemy import text, insert, desc
import tqdm
from datetime import datetime
import requests
from utils.xml_parser import get_branch
import ollama
from fastapi.staticfiles import StaticFiles
from parts import all_parts
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
admin = Admin(app, engine, title='GxPolicy')
app.mount("/static", StaticFiles(directory="static"), name="static")


class SetupView(BaseView):
    name = "Setup"

    @expose("/setup", methods=["GET"])
    async def report_page(self, request):

        with SessionLocal() as db:
            setup = db.query(Setup).first()
            if not setup:
                setup = Setup(parts=[])
                db.add(setup)
                db.commit()
        print(parts)
        return await self.templates.TemplateResponse(request, "setup.html", context={
            "setup": setup,
            "all_parts": all_parts
        })


admin.add_view(SetupView)


class SopAdmin(ModelView, model=Sop):
    name = "Sop"
    page_size = 50

    column_default_sort = [(Sop.has_changed, True)]
    column_list = [Sop.name, Sop.owner, Sop.abstract]
    column_details_exclude_list = [Sop.sops_on_regulations, Sop.url]
    form_excluded_columns = [Sop.segments, Sop.url, Sop.sops_on_regulations]
    column_details_exclude_list = [Sop.segments]
    list_template = 'sops.html'
    details_template = 'sop_details.html'
    edit_template = 'sop_edit.html'


admin.add_view(SopAdmin)


class RegulationAdmin(ModelView, model=Regulation):
    column_list = [Regulation.id, Regulation.name, Regulation.abstract]


admin.add_view(RegulationAdmin)


class SopSegmentAdmin(ModelView, model=SopSegment):
    form_excluded_columns = [SopSegment.embedding, SopSegment.raw_content]


admin.add_view(SopSegmentAdmin)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SetupModel(BaseModel):
    title: str
    parts: List[str]


@app.post("/api/setup/")
def update_setup(setup_input: SetupModel, db: Session = Depends(get_db)):
    setup = db.query(Setup).first()
    if not setup:
        print(setup.parts)
        setup = Setup(parts=[])
    setup.parts = setup_input.parts
    setup.title = setup_input.title
    db.commit()
    print(setup.parts, setup.id)
    return {"success": True}


@app.post("/api/sops/", )
def create_sops(files: List[UploadFile] = File(), db: Session = Depends(get_db)):
    db.execute(text("truncate sops RESTART IDENTITY CASCADE;"))
    db.execute(text("truncate sop_segments  RESTART IDENTITY CASCADE;"))
    db.execute(text("truncate sop_on_regulations restart identity cascade"))
    db.execute(
        text("truncate sop_segment_on_regulation_segment restart identity cascade"))
    db.commit()
    file_names = []
    setup = db.query(Setup).first()
    for file in files:

        file_names.append(file.file)
    embedded_sops = embed_files(files)
    for embedded_sop in embedded_sops:
        sop_model = Sop(
            name=embedded_sop['file_name'], url='', abstract=embedded_sop['abstract'], owner=embedded_sop['owner'])
        db.add(sop_model)
        db.commit()
        for content in embedded_sop['content']:
            segment_model = SopSegment(
                sop_id=sop_model.id, raw_content=content['content'], embedding=content['embedding'])
            db.add(segment_model)
        db.commit()
        query_result = db.execute(text(f"""
                                        SELECT
	                                        regulation_segments.id as regulation_segment_id ,
	                                        sop_segments.id as sop_segment_id,
	                                        (1 - (regulation_segments.embedding <=> sop_segments.embedding)) as cosine_similarity
                                        FROM regulation_segments
                                        JOIN sop_segments on 1=1
                                        WHERE (1 - (regulation_segments.embedding <=> sop_segments.embedding)) > {setup.threshhold}
                                        ORDER BY cosine_similarity desc
                                        """))
    for (regulation_segment_id, sop_segment_id, cosine_similarity) in query_result.fetchall():
        key = f"{regulation_segment_id}_{sop_segment_id}"
        sop_on_regulation_model = SopSegmentOnRegulationSegment(
            sop_segment_id=sop_segment_id, regulation_segment_id=regulation_segment_id, similarity=cosine_similarity)
        db.add(sop_on_regulation_model)
    db.commit()

    return {"success": True}


title = 21
parts = [11, 210, 211, 300, 213, 314, 606, 820, 830, 1271]
parts = [11, 210]


@app.on_event('startup')
@repeat_every(seconds=3000)
async def parse_regulations():
    try:
        db = SessionLocal()
        titles = requests.get(
            'https://www.ecfr.gov/api/versioner/v1/titles').json()
        # db.execute(text("truncate regulation_segments RESTART IDENTITY CASCADE;"))
        # db.execute(text("truncate regulations  RESTART IDENTITY CASCADE;"))
        # db.commit()

        found_title = first(
            x for x in titles['titles'] if x['number'] == title)
        latest_issue_date = found_title['latest_issue_date']

        for part in tqdm.tqdm(parts, desc="reading regulations"):
            regulation = db.query(Regulation).where(Regulation.title == str(title), Regulation.part == str(
                part)).order_by(desc(Regulation.latest_amendment_date)).first()

            if not regulation:
                reg_data = get_data(title=title, part=part,
                                    latest_issue_date=latest_issue_date)
                regulation_model = Regulation(
                    title=title,
                    part=part,
                    latest_amendment_date=latest_issue_date,
                    name=reg_data['reg_title'],
                    abstract=reg_data['abstract'],
                )
                db.add(regulation_model)
                db.commit()
                for regulation in tqdm.tqdm(reg_data["regulation_content"], desc=f'Regulation Segment for {title}:{part}'):
                    try:
                        if (regulation['content']):
                            regulation_segment_model = RegulationSegment(
                                regulation_id=regulation_model.id,
                                raw_content=regulation['content'],
                                name=regulation['title'],
                                embedding=embed_text(regulation['content'])
                            )
                            db.add(regulation_segment_model)
                        db.commit()
                    except Exception as e:
                        print("NE", e)
            else:
                regulation_model = regulation
                if regulation_model.latest_amendment_date < datetime.strptime(latest_issue_date, "%Y-%m-%d").date():
                    reg_data = get_data(
                        title=title, part=part, latest_issue_date=latest_issue_date)
                    regulation_model.abstract = reg_data['abstract']
                    # regulation_model.latest_amendment_date = latest_issue_date
                    db.commit()
                    changed = False
                    for regulation in tqdm.tqdm(reg_data["regulation_content"], desc=f'Regulation Segment for {part}'):
                        found_segment = db.query(RegulationSegment).where(
                            RegulationSegment.name == regulation['title']
                        ).first()
                        print("FS", found_segment)
                        if not found_segment:
                            print("NOT FOUND ")
                            changed = True
                            if regulation['content']:
                                regulation_segment_model = RegulationSegment(
                                    regulation_id=regulation_model.id,
                                    raw_content=regulation['content'],
                                    name=regulation['title'],
                                    embedding=embed_text(regulation['content'])
                                )
                                db.add(regulation_segment_model)
                                found_segment = regulation_segment_model

                        elif found_segment.raw_content == regulation['content']:
                            print("FOUND")
                            changed = False
                        else:
                            print("CHANGED")
                            changed = True
                            found_segment.raw_content = regulation['content']
                            found_segment.embedding = embed_text(
                                regulation['content'])
                            found_segment.has_changed = True

                        if changed and found_segment:

                            for ssors in found_segment.sop_segments_on_regulation_segments:
                                ssors.sop_segment.has_changed = True
                        db.commit()

                else:
                    print("DOES NOT NEED UPDATE", part)

            # if not regulation or regulation.latest_amendment_date < datetime.strptime(latest_issue_date, "%Y-%m-%d").date():
            #     part_xml = requests.get(f"https://www.ecfr.gov/api/versioner/v1/full/{latest_issue_date}/title-{title}.xml?part={part}")

            #     regulation_content = []
            #     xml_data = part_xml.content

            #     if (part_xml.content):
            #         tree = ET.fromstring(xml_data)
            #         raw_string =  ET.tostring(tree, encoding='utf-8', method='text')
            #         abstract = ollama.generate(model='llama3',prompt= f'only output actual result and Give me abstract for this file {raw_string}')['response'].rsplit('**Abstract:**')[-1]

            #         get_branch(tree=tree, regulations=regulation_content)
            #         reg_title = tree.find('HEAD').text
            #         regulation_model = Regulation(
            #             name=reg_title,
            #             title=title,
            #             abstract=abstract,
            #             part= part,
            #             description= raw_string,
            #             latest_amendment_date=latest_issue_date)
            #         db.add(regulation_model)
            #         db.commit()

        db.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("EXC", e)


if __name__ == '__main__':
    uvicorn.run(
        app=f"main:app",
        host='localhost',
        port=settings.PORT,
        reload=True,
        use_colors=True,
        workers=2
    )


def first(iterable, default=None):
    for item in iterable:
        return item
    return default
