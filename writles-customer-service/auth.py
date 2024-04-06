from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
from jwt import ExpiredSignatureError
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from models.user import TokenObj
import os
from dotenv import load_dotenv
load_dotenv()

jwtkey=os.getenv("JWT_SECRET_KEY")
algorithm=os.getenv("ALGORITHM")

API_KEY = os.getenv("API_KEY")


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauthScheme=OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def validateToken(token: Optional[str] = Depends(oauthScheme)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Өөө, Хэрэглэгчийн нэвтрэх мэдээлэл хэрэгтэй !!!"
        )

    try:
        payload = jwt.decode(token, jwtkey, algorithms=[algorithm])
        id: str = payload.get("_id")

        if id is None:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Өөө, Хэрэглэгчийн мэдээлэл дутуу !!!")
        
        print(payload)
        return TokenObj(id=str(payload.get("_id")),username = payload.get("username"), name=payload.get("name"), device_token=payload.get("device_token"))    
    except jwt.JWTError as e:
        error = e.__class__.__name__
        if error == 'ExpiredSignatureError':
             raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Өөө, Токен хаагдсан байна !!!",
            headers={"WWW-Authenticate": "Bearer"})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Өөө, Алдаатай хүсэлт байна !!!",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    
    
async def check_key(api_key: str = Security(api_key_header)):  
    
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Өөө, API KEY хэрэгтэйшдээ !!!"
        )

    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Өөө, Буруу API KEY байна !!!"
        )
