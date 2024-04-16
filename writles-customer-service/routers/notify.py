from fastapi import APIRouter, Security, Response, Depends
from auth import check_key
import firebase_admin
from firebase_admin import credentials, messaging
from auth import validateToken
import os
from models.NotifyReq import NotifyReq
from models.user import TokenObj
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler


cred = credentials.Certificate(os.path.join(os.getcwd(), ".firebase/writles-firebase-adminsdk-k0iuf-87189d6328.json"))
firebase_admin.initialize_app(cred)


router=APIRouter(prefix="/notification")


@router.post("/notify",dependencies=[Security(check_key)])
async def notify(response:Response,item: NotifyReq):

    print("in here")
    # orj irsen tsag
    now = datetime.now()
    
    if item.date is None:
        input_time=now
    else :
        input_time = datetime.strptime(item.date, '%Y-%m-%d %H:%M:%S')

    if now >= input_time:
        print("vnen")
        resp=sendPush(item.title, item.body,item.token, item.obj)
        success = resp.success_count

        if success == 1 :
            return resp
        else :
            exception=(resp.responses[0]).exception.cause.reason
            status=(resp.responses[0]).exception.http_response.status_code

            response.status_code = status
            response.headers["Content-Type"] = "application/json; charset=utf-8"
            return exception
    else:
        scheduler = BackgroundScheduler()
        scheduler.add_job(schedulePush, 'date',args=[item.title, item.body,item.token, item.obj],run_date=input_time)
        scheduler.start()
        return "scheduled"
    



def schedulePush(title, msg, device_token, dataObject=None):
    res=sendPush(title,msg, device_token,dataObject)
    print("sucess")


def sendPush(title, msg, device_token, dataObject=None):
    data_dict = dataObject.dict() if dataObject else None

    print(data_dict)

    data={}
    if data_dict is not None:
        if data_dict['body'] is not None:
            data['body']=data_dict['body']
        if data_dict['title'] is not None:
            data['title']=data_dict['title']
        
        
        message=messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=msg
        ),
        data=data,
        tokens=device_token,
        android=messaging.AndroidConfig(
            priority='high'
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(
                        title=title,
                        body=msg
                    ),
                    content_available=True

                )   
            ),
            headers={'apns-priority': '10'} 
        )
    )
        
    else :
        message=messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=msg
        ),
        tokens=device_token,
        android=messaging.AndroidConfig(
            priority='high'
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(
                        title=title,
                        body=msg
                    ),
                    content_available=True
                )   
            ),
            headers={'apns-priority': '10'} 
        )
    )

    response = messaging.send_multicast(message)
    print(response)
    return response


def my_job():
    print("This is a one-time job!")

@router.post("/check")
async def postUser(response:Response, token: TokenObj = Depends(validateToken)):
    return {"success":"ok"}