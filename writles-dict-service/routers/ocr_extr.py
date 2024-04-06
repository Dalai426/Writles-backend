from fastapi import APIRouter, UploadFile, Security, HTTPException,Response
from auth import check_key
import pytesseract
import numpy as np
import cv2

pytesseract.pytesseract.tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe'

router=APIRouter(prefix="/ocr")

ALLOWED_EXTENSIONS = {'png', 'webp', 'bmp', 'jpg', 'jpeg'}

@router.post("/extract",dependencies=[Security(check_key)])
async def ocr(img: UploadFile | None = None):
    if not img:
        raise HTTPException(status_code=400, detail="Өөө, Файл ирсэнгүй шүү !!")
    else:
        if img and allowed_file(img.filename):
            contents = await img.read()
            nparr = np.fromstring(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            try :
                str_result=pytesseract.image_to_string(img, lang="mon", config="--psm 6 --oem 1")
                return Response(content=str_result, media_type="text/html; charset=utf-8")
            except Exception as e:
                print(e)
                raise HTTPException(status_code=500, detail="Зургаас танихад алдаа гарлаа !!")
        else:
            raise HTTPException(status_code=400, detail="Өөө, Файлын төрөл таарахгүй байна !!")



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS