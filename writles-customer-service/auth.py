from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
    
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
