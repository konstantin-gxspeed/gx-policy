from fastapi import FastAPI, Depends, File, UploadFile
import uvicorn
from database import SessionLocal, engine
from glob import glob
from sqlalchemy.orm import Session
from config import settings
from typing import List
import app.database.models.models as models
from embed_files import embed_files, embed_text
from app.database.models.models import Sop, SopSegment, Regulation, RegulationSegment,SopOnRegulation
from sqladmin import Admin, ModelView
from fastapi_utilities import repeat_every
import xml.etree.ElementTree as ET
from sqlalchemy import text, insert
import tqdm 
from datetime import datetime
import requests

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
admin = Admin(app, engine, title='GxPolicy')


class SopAdmin(ModelView, model=Sop):
    name= "Sop"
    column_list = [Sop.id, Sop.name]
    column_details_exclude_list = [Sop.sops_on_regulations,Sop.url]
    form_excluded_columns= [Sop.segments, Sop.url, Sop.sops_on_regulations]
    column_details_exclude_list = [Sop.segments]
    list_template='sops.html'
    details_template='sop_details.html'
    edit_template='sop_edit.html'
admin.add_view(SopAdmin)

class RegulationAdmin(ModelView, model=Regulation):
    column_list = [Regulation.id, Regulation.name]

admin.add_view(RegulationAdmin)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/sops/", )
def create_sops(files: List[UploadFile] = File(), db: Session = Depends(get_db)):
    db.execute(text("truncate sops RESTART IDENTITY CASCADE;"))
    db.execute(text("truncate sop_segments  RESTART IDENTITY CASCADE;"))
    db.execute(text("truncate sop_on_regulations restart identity cascade;"))
    db.commit()
    file_names = []

    for file in files:
        
        file_names.append(file.file)
    embedded_sops =  embed_files(files)
    for embedded_sop in embedded_sops:
        sop_model = Sop(name=embedded_sop['file_name'],url='')    
        db.add(sop_model)
        db.commit()
        for content in embedded_sop['content']:
            segment_model = SopSegment(sop_id=sop_model.id, raw_content=content['content'], embedding=content['embedding'])
            db.add(segment_model)
        db.commit()
        query_result = db.execute(text("""
                        SELECT
	                        regulations.id as regulation_id ,
	                        sops.id as sop_id,
	                        (1 - (regulation_segments.embedding <=> sop_segments.embedding)) as cosine_similarity
                        FROM regulations
                        LEFT JOIN regulation_segments ON regulations.id = regulation_segments.regulation_id
                        JOIN sops on 1=1
                        LEFT JOIN sop_segments ON sop_segments.sop_id = sops.id
                        WHERE (1 - (regulation_segments.embedding <=> sop_segments.embedding)) > 0.6
                        ORDER BY cosine_similarity desc
"""))
    sop_reg_dict = {}
    for (regulation_id, sop_id, cosine_similarity) in query_result.fetchall():
        key = f"{regulation_id}_{sop_id}"
        if  key not in sop_reg_dict.keys():
            sop_reg_dict[key]= cosine_similarity
            print(regulation_id, sop_id, cosine_similarity)
            sop_on_regulation_model = SopOnRegulation(regulation_id=regulation_id, sop_id=sop_id, similarity=cosine_similarity)
        db.add(sop_on_regulation_model)
    db.commit()

    return {"success": True} 


title = 21
parts = [11,210,211,300,213,314,606,820,830,1271]
# parts = [11]

from utils.xml_parser import get_branch

@app.on_event('startup')
@repeat_every(seconds=3000)
async def parse_regulations():
    try:
        db = SessionLocal()
        
        titles = requests.get('https://www.ecfr.gov/api/versioner/v1/titles').json()
        # db.execute(text("truncate regulation_segments RESTART IDENTITY CASCADE;"))
        # db.execute(text("truncate regulations  RESTART IDENTITY CASCADE;"))
        # db.commit()
        
        found_title = first(x for x in titles['titles'] if x['number'] == title) 
        latest_issue_date = found_title['latest_issue_date']
        
        
        print(latest_issue_date)
        for part in tqdm.tqdm(parts, desc="reading regulations"): 
            regulations = db.query(Regulation).where(Regulation.title==str(title), Regulation.part==str(part)).all()
            if not len(regulations) or regulations[0].latest_amendment_date < datetime.strptime(latest_issue_date, "%Y-%m-%d").date():
                part_xml = requests.get(f"https://www.ecfr.gov/api/versioner/v1/full/{latest_issue_date}/title-{title}.xml?part={part}")
                
                
                regulation_content = []
                xml_data = part_xml.content    
                if (part_xml.content):
                    tree = ET.fromstring(xml_data)
                    get_branch(tree=tree, regulations=regulation_content)
                for regulation in tqdm.tqdm(regulation_content):
                    regulation_model = Regulation(
                    name=regulation['title'],
                    title=title,
                    part= part,
                    description= regulation['content'],
                    latest_amendment_date=latest_issue_date)
                    try:
                        db.add(regulation_model)
                        db.commit()             
                        if(regulation['content']):
                            regulation_segment_model = RegulationSegment(
                                regulation_id= regulation_model.id, 
                                raw_content= regulation['content'],
                                embedding = embed_text(regulation['content'])
                                )
                            db.add(regulation_segment_model)
                        db.commit()
                    except Exception as e: 
                        print("NE", e )
                    
                    

            
        
        # xml_files = glob('./reg_xmls/*.xml')


       
        # db.commit()
        # for xml_file in xml_files: 
        #     tree = ET.parse(xml_file).getroot()
        #     get_branch(tree=tree, regulations=regulations)
        
        
        # for regulation in tqdm.tqdm(regulations):
        #     regulation_model = Regulation(name=regulation['title'], description= regulation['content'])
        #     try:
        #         db.add(regulation_model)
        #         db.commit()             
        #         if(regulation['content']):
        #             regulation_segment_model = RegulationSegment(
        #                 regulation_id= regulation_model.id, 
        #                 raw_content= regulation['content'],
        #                 embedding = embed_text(regulation['content'])
        #                 )
        #             db.add(regulation_segment_model)
        #     except Exception as e: 
        #         print("NE", e )
        #     db.commit()
        # print("DONE")
        db.close()
    except Exception as e:
        print("EXC",e)
    

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

