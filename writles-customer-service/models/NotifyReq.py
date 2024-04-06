from pydantic import BaseModel
from typing import List



class Eh(BaseModel):
    title: str | None = None 
    body: str  | None = None 
    
class NotifyReq(BaseModel):
    title: str
    body: str
    obj : Eh | None = None
    token : List[str]
    date:str | None = None
