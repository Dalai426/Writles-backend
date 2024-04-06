from pydantic import BaseModel
from typing import List


class User(BaseModel):
    id:str | None = None
    gmail:str | None = None
    name:str | None = None 
    device_token:str | None = None

class Group(BaseModel):
    id: str
    users : List[str]
    username : str 
    password : str


class GroupReq(BaseModel):
    username : str 
    password : str

class AuthReq(BaseModel):
    username:str=None
    password:str=None
    device_token:str=None


class TokenObj(BaseModel):
    id: str
    username: str
    name:str | None=None
    device_token:str



