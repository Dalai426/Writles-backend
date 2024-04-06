from pymongo import MongoClient



CONNECTION_STRING = "mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+1.10.6"
client = MongoClient(CONNECTION_STRING)
db=client.writless
collection_name=client["writless"]