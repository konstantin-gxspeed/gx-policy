from tortoise.models import Model
from tortoise import fields
# from tortoise.contrib.pydantic.base import PydanticModel
from tortoise_vector.field import VectorField
from tortoise_vector.expression import CosineSimilarity
from typing import List
# # models.py
# from sqlalchemy import Column, Integer, String, Text,ForeignKey
# from sqlalchemy.orm import mapped_column, DeclarativeBase
# from sqlalchemy.orm import relationship

# from pgvector.sqlalchemy import Vector

# class Base(DeclarativeBase):
#     pass

class Sop(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=256)
    segments = fields.ForeignKeyField('models.SopSegment', related_name='segments')
    
    url = fields.CharField(max_length=256)

class SopSegment(Model):
    id = fields.IntField(pk=True)
    sop_id= fields.IntField()
    
    embedding = VectorField(vector_size=768)

class Regulation(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=256)
    segments = fields.ForeignKeyField('models.RegulationSegment', related_name='segments')
    description = fields.CharField(max_length=256)

class RegulationSegment(Model):
    id = fields.IntField(pk=True)
    regulation_id= fields.IntField()
    embedding = VectorField(vector_size=768)

# class SopSegmentModel(PydanticModel):
#     id: int 
#     sop_id: int

# class SopModel(PydanticModel):
#     id: int
#     name: str
#     segments: List[SopSegmentModel]
#     url: str

# class RegulationSegmentModel(PydanticModel):
#     id: int 
#     sop_id: int

# class SopModel(PydanticModel):
#     id: int
#     name: str
#     segments: List[RegulationSegmentModel]
#     url: str


# class Sop(Base):
#     __tablename__ = 'sops'
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, index=True)
#     segments = relationship("SopSegment", back_populates="sop")
    
#     url = Column(Text)

# class SopSegment(Base):
#     __tablename__ = 'sop_segments'
#     id = Column(Integer, primary_key=True, index=True)
#     sop_id= Column(Integer, ForeignKey('sops.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
#     sop = relationship("Sop")
#     embedding = mapped_column(Vector(dim=768))

# class Regulation(Base):
#     __tablename__ = 'regulations'
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, index=True)
#     description = Column(Text)

# class RegulationSegment(Base):
#     __tablename__ = 'regulation_segments'
#     id = Column(Integer, primary_key=True, index=True)
#     regulation_id= Column(Integer, ForeignKey('regulations.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

#     embedding = mapped_column(Vector(dim=768))
