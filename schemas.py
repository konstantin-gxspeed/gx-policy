# schemas.py
from pydantic import BaseModel

class SOPBase(BaseModel):
    title: str
    content: str

class SOPCreate(SOPBase):
    pass

class SOP(SOPBase):
    id: int

    class Config:
        from_attributes = True

class RegulationBase(BaseModel):
    name: str
    description: str

class RegulationCreate(RegulationBase):
    pass

class Regulation(RegulationBase):
    id: int

    class Config:
        from_attributes = True


