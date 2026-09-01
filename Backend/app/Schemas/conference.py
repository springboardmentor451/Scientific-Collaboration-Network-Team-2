from datetime import datetime
from pydantic import BaseModel,ConfigDict,Field
class ConferenceCreate(BaseModel):
    title:str=Field(min_length=2,max_length=300);topic:str=Field(min_length=2,max_length=250);description:str|None=None;location:str=Field(min_length=2,max_length=200);starts_at:datetime;ends_at:datetime|None=None;registration_url:str|None=None;is_open:bool=True
class ConferenceUpdate(BaseModel):
    title:str|None=None;topic:str|None=None;description:str|None=None;location:str|None=None;starts_at:datetime|None=None;ends_at:datetime|None=None;registration_url:str|None=None;is_open:bool|None=None
class ConferenceResponse(ConferenceCreate):
    id:int;participant_count:int=0;is_registered:bool=False
    model_config=ConfigDict(from_attributes=True)
