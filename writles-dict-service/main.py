from fastapi import FastAPI, HTTPException, status
from routers import tts_extr, ocr_extr

app=FastAPI()

app.include_router(tts_extr.router)
app.include_router(ocr_extr.router)


@app.get('/')
def index():
    return 'hey'

@app.get('/err')
async def bat():
    raise HTTPException(status_code=400, detail="Item not")