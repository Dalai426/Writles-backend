from pydantic import BaseModel
from typing import List



class Eh(BaseModel):
    title: str | None = None 
    body: str
    
class NotifyReq(BaseModel):
    title: str
    body: str
    obj : Eh
    token : List[str]
