from fastapi import APIRouter, Query,status, BackgroundTasks, Depends, Response, Security
from auth import validateToken, check_key
from jose import jwt
from schemas.schemas import groupEntity, userListEntity, userMapEntity, userEntity, groupListEntity
from db_config import collection_name
from models.user import User, GroupReq, AuthReq, TokenObj, ChangePass
from utils.passwd import hash_password, verify_password
import utils.email as email
from datetime import datetime, timedelta
import pyotp
from bson import ObjectId
from cryptography.fernet import Fernet
from dotenv import load_dotenv
load_dotenv()
import os


key = os.getenv("ENCRYPTION_KEY")
jwtkey=os.getenv("JWT_SECRET_KEY")
algorithm=os.getenv("ALGORITHM")

router=APIRouter(prefix="/user")


@router.post('/login')
async def login(response: Response ,user:AuthReq):
    if user.device_token is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': 'Өөө, Хэрэглэгчийн device-ийн мэдээлэл дутуу !!!'}
    
    if user.username is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail':"Өөө, Хэрэглэгчийн нэр дутуу !!!"}
    
    if user.password is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': 'Өөө, Нууц үг буруу байна !!!'}


    
    group=groupEntity(collection_name.group.find_one({"username":user.username.lower()}))
    print(group )
    if not group:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': 'Өөө, Нэвтрэх нэр эсвэл нууц үг буруу байна !!!'}
    
    
    if not verify_password(user.password, group["password"]):
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': 'Өөө, Нууц үг буруу байна !!!'}

    
    
    finded_users=collection_name.user.find({"group":group["id"]})
    users=userMapEntity(finded_users)
    if user.device_token not in users:
        data={"_id": group["id"], "username": group["username"],"name":None, "device_token":user.device_token}
        expire=datetime.utcnow()+timedelta(days=30)
        data.update({"exp":expire})
        encoded_jwt=jwt.encode(data, jwtkey, algorithm=algorithm)
        return {'status': 'required register','users':list(users.values()), 'access_token': encoded_jwt}

    data={"_id": group["id"], "username": group["username"],"name":users[user.device_token]["name"], "device_token":user.device_token}

    expire=datetime.utcnow()+timedelta(days=30)
    data.update({"exp":expire})
    encoded_jwt=jwt.encode(data, jwtkey, algorithm=algorithm)
    
    return {'status': 'success', 'access_token': encoded_jwt}

    
    

@router.post("/add")
async def postUser(response:Response,user: User,token: TokenObj = Depends(validateToken)):

    if user.device_token is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': 'Өөө, Хэрэглэгчийн device-ийн мэдээлэл дутуу !!!'}
    
    if user.name is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': "Өөө, Хэрэглэгчийн нэр дутуу !!!"}
    
    query = {"$and": [{"name": user.name}, {"group": token.id}]}
    result = userListEntity(collection_name.user.find(query))

    if result:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': "Өөө, Хэрэглэгчийн та энэ ангид бүртгэлтэй байна !!!"}
        
    
    quer = {"$and": [{"device_token": user.device_token}, {"group": token.id}]}
    res = userListEntity(collection_name.user.find(quer))

    if res:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': "Өөө, Бүртгэлтэй төхөөрөмж байна !!!"}
  

    new_user_data = dict(user)
    new_user_data["group"]=token.id
    new_user_id = collection_name.user.insert_one(new_user_data).inserted_id
    new_user_data["_id"] = str(new_user_id)
    # todo logout old token

    data={"_id": token.id, "username": token.username,"name":new_user_data["name"], "device_token":new_user_data["device_token"]}

    expire=datetime.utcnow()+timedelta(days=30)
    data.update({"exp":expire})
    encoded_jwt=jwt.encode(data, jwtkey, algorithm=algorithm)
    return {"newuser":new_user_data, "accesstoken":encoded_jwt}

@router.post("/update")
async def postUser(response:Response,user:User,token: TokenObj = Depends(validateToken)):


    update_fields = {
    }

    if token.device_token is not None:
        update_fields["device_token"]=token.device_token


    if user.gmail is not None:
        update_fields["gmail"]=user.gmail 

    
    if user.name is not None:
        query = {"$and": [{"name": user.name}, {"group": token.id}]}
        result = userListEntity(collection_name.user.find(query))
        if result:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.headers["Content-Type"] = "application/json; charset=utf-8"
            return {'detail': "Өөө, Хэрэглэгчийн нэр ангид бүртгэлтэй байна !!!"}
        else :
            update_fields["name"]=user.name

    res=collection_name.user.update_one(
        filter = {"$and": [{"_id":ObjectId(user.id)}, {"group": token.id}]},
        update={"$set": update_fields}
    )


    modified_count = res.modified_count
    if modified_count==0 :
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': 'Өөө, Хэрэглэгчийн мэдээлэл шинэчлэгдсэнгүй !!!'}
    
    if user.name is not None:
        name=user.name
    else :
        name=token.name

    data={"_id": token.id, "username": token.username,"name":name, "device_token":token.device_token}
    expire=datetime.utcnow()+timedelta(days=30)
    data.update({"exp":expire})
    encoded_jwt=jwt.encode(data, jwtkey, algorithm=algorithm)
    return {"accesstoken":encoded_jwt}
    

@router.post("/signup")
async def postUser(response:Response,group: GroupReq, user:User):
      
    if user.device_token is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': 'Өөө, Хэрэглэгчийн device-ийн мэдээлэл дутуу !!!'}

        
    if user.name is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': 'Өөө, Хэрэглэгчийн нэр дутуу !!!'}
       
    if group.username is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': "Өөө, Нэвтрэх нэр дутуу !!!"}
  
    if group.password is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': "Өөө, Нууц үгээ оруулаарай !!!"}
    
    
    group.username=group.username.lower()
    find=collection_name.group.find_one({"username":group.username.lower()})
    bef=collection_name.user.find_one({"$and": [{"name": user.name}, {"gmail": user.gmail}]})
    if find :
        if bef :
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.headers["Content-Type"] = "application/json; charset=utf-8"
            return {'detail': "Өөө, Та энэ ангид бүртгэлтэй байна. Нууц үгээ мартсан бол сэргээгээд дахин оролдоорой !!!"}
        else :
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.headers["Content-Type"] = "application/json; charset=utf-8"
            return {'detail': "Өөө, Нэвтрэх нэр давхацсан байна !!!"}
  
    
    group.password=hash_password(group.password)
    new_group_data = dict(group)
    new_group_id = collection_name.group.insert_one(new_group_data).inserted_id
    del new_group_data["password"]
    new_group_data["_id"] = str(new_group_id)

    new_user_data = dict(user)
    new_user_data["group"]=str(new_group_id)
    new_user_id = collection_name.user.insert_one(new_user_data).inserted_id
    new_user_data["_id"] = str(new_user_id)

    data={"_id":new_group_data["_id"] , "username":new_group_data["username"] ,"name":new_user_data["name"], "device_token":new_user_data["device_token"]}
    expire=datetime.utcnow()+timedelta(days=30)
    data.update({"exp":expire})
    encoded_jwt=jwt.encode(data, jwtkey, algorithm=algorithm)

    return {"group":new_group_data,"user":new_user_data, "accesstoken":encoded_jwt}


@router.get("/getusers")
async def getUsers(response:Response, token: TokenObj = Depends(validateToken)):
    users=userListEntity(collection_name.user.find({"group":token.id}))
    return users


@router.get("/getuser")
async def getUser(response:Response, token: TokenObj = Depends(validateToken)):
    users=userEntity(collection_name.user.find_one({"group":token.id, "device_token":token.device_token}))
    return users


@router.get("/getgroups")
async def getGroups(response:Response, gmail:str=Query):

    pipeline = [
    {"$match": {"gmail": gmail}},
    {"$addFields": {
        "groupId": {"$toObjectId": "$group"}
    }},
    {"$lookup": {
        "from": "group",
        "let": {"groupId": "$groupId"},
        "pipeline": [
            {"$match": {"$expr": {"$eq": ["$_id", "$$groupId"]}}}
        ],
        "as": "group"
    }},
    {"$unwind": "$group"},
    {"$project": {
        "_id": "$group._id",
        "username": "$group.username"
    }},
     {"$group": {
        "_id": "$_id",  
        "username": {"$first": "$username"}  
    }}
    ]

    groups = groupListEntity(list(collection_name.user.aggregate(pipeline)))
    return groups


@router.post("/delete")
async def delUser(response:Response, id:str=Query(), token: TokenObj = Depends(validateToken)):
    try:
        collection_name.user.delete_one({"_id":ObjectId(id)})
    finally:
        users=userListEntity(collection_name.user.find({"group":token.id}))
        return users

@router.post('/otp')
async def senotp(response:Response,background_tasks: BackgroundTasks,gmail:str=Query()):
    try:
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        otp = totp.now()

        background_tasks.add_task(email.send,[gmail], subject="Writles баталгаажуулалт", text=F"Writles email хаяг баталгаажуулах код :\n{otp}")
     
        # otp to bytes
        message = otp.encode()
        cipher = Fernet(key.encode())
        encrypted_message = cipher.encrypt(message)

        return {"otp" : encrypted_message}
    except Exception as error:
        print(error)
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': "Өөө, Otp илгээхэд алдаа гарлаа !!!"}
    


@router.post("/update-password",dependencies=[Security(check_key)])
async def notify(response:Response,req:ChangePass):
    if req.newPassword is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': "Өөө, Нууц үгээ оруулаарай !!!"}
    
    req.newPassword=hash_password(req.newPassword)
    res=collection_name.group.update_one(
        filter = {"_id":ObjectId(req.userId)},
        update={"$set": {
            "password":req.newPassword
        }}
    )

    modified_count = res.modified_count
    if modified_count==0 :
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return {'detail': 'Өөө, Амжилтгүй !!!'}
    
    return "success"

