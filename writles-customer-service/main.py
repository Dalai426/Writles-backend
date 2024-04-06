from fastapi import FastAPI, HTTPException, status
from routers import notify, user

app=FastAPI()


app.include_router(notify.router)
app.include_router(user.router)

@app.get('/')
def index():
    return 'hey'
