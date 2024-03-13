from fastapi import APIRouter, Security, HTTPException,status
from auth import check_key
import firebase_admin
from firebase_admin import credentials, messaging
import os
from models.NotifyReq import NotifyReq




cred = credentials.Certificate(os.path.join(os.getcwd(), ".firebase/writles-firebase-adminsdk-k0iuf-87189d6328.json"))
firebase_admin.initialize_app(cred)


router=APIRouter(prefix="/user")

@router.post("/notify",dependencies=[Security(check_key)])
async def notify(item: NotifyReq):
    resp=sendPush(item.title, item.body,item.token, item.obj)
    success = resp.success_count

    if success == 1 :
        return resp
    else :
        exception=(resp.responses[0]).exception.cause.reason
        status=(resp.responses[0]).exception.http_response.status_code
        raise HTTPException(
            status_code=status,
            detail=exception
        )

def sendPush(title, msg, device_token, dataObject=None):
    
    data_dict = dataObject.dict() if dataObject else None

    message=messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=msg
        ),
        data=data_dict,
        tokens=device_token
    )


    response = messaging.send_multicast(message)
    print(response)
    return response