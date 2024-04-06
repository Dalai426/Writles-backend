def userEntity(item) -> dict:
    return {
        "id":str(item["_id"]),
        "name":item["name"],
        "gmail":item["gmail"],
        "device_token":item["device_token"]
    }

def userListEntity(users) -> list:
    return [userEntity(user) for user in users]

def userMapEntity(items) -> list:
    map={}
    for i in items:
        user=userEntity(i)
        map[user["device_token"]]=user
    return map

def groupEntity(item) -> dict:
    if item is None:
        return {}
    else:
        return {
            "id":str(item["_id"]),
            "username":item["username"],
            "password":item["password"],     
        }