from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List
from dotenv import load_dotenv
load_dotenv()
import os

mail = os.getenv("EMAIL")
password = os.getenv("PASSWORD")



conf = ConnectionConfig(
    MAIL_USERNAME = mail,
    MAIL_PASSWORD = password,
    MAIL_FROM = mail,
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send(email: List[EmailStr], subject:str, text: str):
    try:
        message = MessageSchema(
            subject=subject,
            recipients=email,
            body=text,
            subtype=MessageType.plain
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as error:
        print("mail hudlaa2")
    
    return True