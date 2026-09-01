from pydantic import BaseModel,ConfigDict,Field
class InstitutionCreate(BaseModel):
    name:str=Field(min_length=2,max_length=200);short_name:str=Field(min_length=2,max_length=30);location:str=Field(min_length=2,max_length=200);description:str|None=None;research_areas:list[str]=Field(default_factory=list);website:str|None=None
class InstitutionUpdate(BaseModel):
    name:str|None=None;short_name:str|None=None;location:str|None=None;description:str|None=None;research_areas:list[str]|None=None;website:str|None=None
class InstitutionResponse(InstitutionCreate):
    id:int;researcher_count:int=0;publication_count:int=0;source:str|None=None;source_url:str|None=None
    model_config=ConfigDict(from_attributes=True)
