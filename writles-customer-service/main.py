from fastapi import FastAPI, HTTPException, status
from routers import notify

app=FastAPI()


app.include_router(notify.router)

@app.get('/')
def index():
    return 'hey'
