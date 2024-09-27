from sqlalchemy import Column, Integer, String, Text,ForeignKey, Date, Float,UniqueConstraint
from sqlalchemy.orm import mapped_column, DeclarativeBase,relationship,backref
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass


class SopOnRegulation(Base):
    __tablename__ = 'sop_on_regulations'
    id = Column(Integer, primary_key=True, index=True)
    sop_id= Column(Integer, ForeignKey('sops.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    regulation_id = Column( Integer, ForeignKey('regulations.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    similarity = Column(Float(precision=2), index=True)
    sop = relationship("Sop", lazy='joined')
    regulation = relationship("Regulation",  lazy="joined")
    UniqueConstraint('sop_id', 'regulation_id', name='sop_regulation_unique')
    def normalize(self):
        return float("{:.2f}".format(self.similarity))
    def normalize_value(self):
        normalized_value =  (self.similarity - 0.5) / 0.5
        return float("{:.2f}".format(normalized_value))
    def color(self):
        
        red = int(255 * (1 -self.normalize()))
        green = int(255 * self.normalize()) 
        
        # Return the color as a hex string
        return f'#{red:02x}{green:02x}00'
    
class Sop(Base):
    __tablename__ = 'sops'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    segments = relationship("SopSegment", back_populates="sop")
    sops_on_regulations = relationship("SopOnRegulation", back_populates="sop", lazy="joined")
    url = Column(Text)

class SopSegment(Base):
    __tablename__ = 'sop_segments'
    id = Column(Integer, primary_key=True, index=True)
    sop_id= Column(Integer, ForeignKey('sops.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    sop = relationship("Sop")
    raw_content = Column(String)
    embedding = mapped_column(Vector(dim=768))

class Regulation(Base):
    __tablename__ = 'regulations'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    title= Column(String, index=True)
    part = Column(String, index=True)
    sops_on_regulations = relationship("SopOnRegulation", back_populates="regulation")
    description = Column(Text)
    latest_amendment_date = Column(Date)

class RegulationSegment(Base):
    __tablename__ = 'regulation_segments'
    id = Column(Integer, primary_key=True, index=True)
    raw_content = Column(String)
    regulation_id= Column(Integer, ForeignKey('regulations.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    regulation = relationship("Regulation")
    embedding = mapped_column(Vector(dim=768))
