from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Float, UniqueConstraint, Boolean,JSON
from sqlalchemy.orm import mapped_column, DeclarativeBase, relationship, backref
from pgvector.sqlalchemy import Vector
import json


class Base(DeclarativeBase):
    pass


class Setup(Base):
    __tablename__ = 'setups'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Integer)
    parts = Column(JSON)

class SopOnRegulation(Base):
    __tablename__ = 'sop_on_regulations'
    id = Column(Integer, primary_key=True, index=True)
    sop_id = Column(Integer, ForeignKey(
        'sops.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    regulation_id = Column(Integer, ForeignKey(
        'regulations.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    similarity = Column(Float(precision=2), index=True)
    sop = relationship("Sop", lazy='joined')
    regulation = relationship("Regulation",  lazy="joined")
    UniqueConstraint('sop_id', 'regulation_id', name='sop_regulation_unique')

    def normalize(self):
        return float("{:.2f}".format(self.similarity))

    def normalize_value(self):
        normalized_value = (self.similarity - 0.5) / 0.5
        return float("{:.2f}".format(normalized_value))

    def color(self):

        red = int(255 * (1 - self.normalize()))
        green = int(255 * self.normalize())

        return f'#{red:02x}{green:02x}00'


class SopSegmentOnRegulationSegment(Base):
    __tablename__ = 'sop_segment_on_regulation_segment'
    id = Column(Integer, primary_key=True, index=True)
    sop_segment_id = Column(Integer, ForeignKey(
        'sop_segments.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    regulation_segment_id = Column(Integer, ForeignKey(
        'regulation_segments.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    similarity = Column(Float(precision=2), index=True)
    sop_segment = relationship("SopSegment", lazy='joined')
    regulation_segment = relationship("RegulationSegment",  lazy="joined")
    UniqueConstraint('sop_segment_id', 'regulation_segment_id',
                     name='sop_regulation_unique')

    def normalize(self):
        return float("{:.2f}".format(self.similarity))

    def normalize_value(self):
        normalized_value = (self.similarity - 0.5) / 0.5
        return float("{:.2f}".format(normalized_value))

    def color(self):

        red = int(255 * (1 - self.normalize()))
        green = int(255 * self.normalize())

        return f'#{red:02x}{green:02x}00'


class Sop(Base):
    __tablename__ = 'sops'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    abstract = Column(String)
    owner = Column(String)
    segments = relationship("SopSegment", back_populates="sop", lazy="joined")
    sops_on_regulations = relationship(
        "SopOnRegulation", back_populates="sop", lazy="joined")
    url = Column(Text)
    has_changed = Column(Boolean)

    @property
    def requires_attention(self):
        return any(map(lambda segment: segment.has_changed, self.segments))


class SopSegment(Base):
    __tablename__ = 'sop_segments'
    id = Column(Integer, primary_key=True, index=True)
    sop_id = Column(Integer, ForeignKey(
        'sops.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    sop = relationship("Sop")
    sop_segments_on_regulation_segments = relationship(
        "SopSegmentOnRegulationSegment", back_populates="sop_segment", lazy="joined")

    raw_content = Column(String)
    embedding = mapped_column(Vector(dim=768))

    has_changed = Column(Boolean, default=False)


class Regulation(Base):
    __tablename__ = 'regulations'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    title = Column(String, index=True)
    abstract = Column(String)
    part = Column(String, index=True)
    sops_on_regulations = relationship(
        "SopOnRegulation", back_populates="regulation", lazy="joined")
    regulation_segments = relationship(
        "RegulationSegment", back_populates="regulation", lazy="joined")
    description = Column(Text)
    latest_amendment_date = Column(Date)


class RegulationSegment(Base):
    __tablename__ = 'regulation_segments'
    id = Column(Integer, primary_key=True, index=True)
    raw_content = Column(String)
    name = Column(String)
    regulation_id = Column(Integer, ForeignKey(
        'regulations.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    regulation = relationship("Regulation")
    sop_segments_on_regulation_segments = relationship(
        "SopSegmentOnRegulationSegment", back_populates="regulation_segment", lazy="joined")

    embedding = mapped_column(Vector(dim=768))
    has_changed = Column(Boolean)

    def __repr__(self) -> str:

        return json.dumps({
            "name": self.name,
            "id": self.id,
            "regulation_id": self.regulation_id
        })
