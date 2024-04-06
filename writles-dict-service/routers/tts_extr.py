from fastapi import APIRouter, Security, Query, HTTPException 
from fastapi.responses import StreamingResponse
from auth import check_key
import re
import wave
import contextlib
import numpy as np
import onnxruntime as ort
import io
import os
from typing import Annotated


_pad = '_'
_punctuation = '!\'(),.:;? '
_special = '-'
# _letters = 'АБВГДЕЁЖЗИЙКЛМНОӨПРСТУҮФХЦЧШЪЫЬЭЮЯабвгдеёжзийклмноөпрстуүфхцчшъыьэюя'
_letters = 'абвгдеёжзийклмноөпрстуүфхцчшъыьэюя'
_symbols = [_pad] + list(_special) + list(_punctuation) + list(_letters)
_symbol_to_id = {s: i for i, s in enumerate(_symbols)}
_whitespace_re = re.compile(r'\s+')


# Гар утас, Atom CPU-тэй компьютер зэрэг чадал хязгаарлагдмал төхөөрөмжүүдэд ашиглаж
# болох аудио спектрограммаас яриа үүсгэх (vocoder) жижиг хэмжээний загвар
# onnx_models/female2_vocoderv3.onnx тус тус агуулна



tts_onnx_female3 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s.onnx' % "female3"))
vocoder_onnx_female3 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s_vocoderv3.onnx' % "female3"))

tts_onnx_female1 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s.onnx' % "female1"))
vocoder_onnx_female1 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s_vocoderv3.onnx' % "female1"))

tts_onnx_female2 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s.onnx' % "female2"))
vocoder_onnx_female2 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s_vocoderv3.onnx' % "female2"))

tts_onnx_male1 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s.onnx' % "male1"))
vocoder_onnx_male1 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s_vocoderv3.onnx' % "male1"))

tts_onnx_male2 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s.onnx' % "male2"))
vocoder_onnx_male2 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s_vocoderv3.onnx' % "male2"))

tts_onnx_male3 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s.onnx' % "male3"))
vocoder_onnx_male3 = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'onnx_models', '%s_vocoderv3.onnx' % "male3"))
print("dalai")

router=APIRouter(prefix="/tts")

@router.get("/extract",dependencies=[Security(check_key)])
async def tts(voice:str=Query(None), text:str=Query(None)):

    if voice is None:
        voice="female3"
    
    if text is None:
        raise HTTPException(status_code=400, detail="Өөө, Текстээ мартчихжээ !!!")
    
    text=text.lower().strip()

    if len(text)==0:
        raise HTTPException(status_code=400, detail="Өөө, Текстээ мартчихжээ !!!")
    
    is_containing_char = False
    for c in text:
        if c in _letters:
            is_containing_char = True
            break
    if not is_containing_char:
        raise HTTPException(status_code=400, detail="Өөө, Таны текст тэмдэгт агуулаагүй байна !!!")
    
    if text[-1] not in ['.', '?', '!']:
        text += '.'

    
    seq = _text_to_sequence(text)
    print(seq)
    text_lengths = np.array([len(seq)], dtype=np.int64)
    seq = np.array([seq], dtype=np.int64)

    if voice=="female1":
        mel = await _run_onnx(tts_onnx_female1, [seq, text_lengths, np.array(1.0, dtype=np.float32)])
        audio = (await _run_onnx(vocoder_onnx_female1, [mel]))[0, 0, :]
    elif voice=="female2":
        mel = await _run_onnx(tts_onnx_female2, [seq, text_lengths, np.array(1.0, dtype=np.float32)])
        audio = (await _run_onnx(vocoder_onnx_female2, [mel]))[0, 0, :]
    elif voice=="male1":
        mel = await _run_onnx(tts_onnx_male1, [seq, text_lengths, np.array(1.0, dtype=np.float32)])
        audio = (await _run_onnx(vocoder_onnx_male1, [mel]))[0, 0, :]
    elif voice=="male2":
        mel = await _run_onnx(tts_onnx_male2, [seq, text_lengths, np.array(1.0, dtype=np.float32)])
        audio = (await _run_onnx(vocoder_onnx_male2, [mel]))[0, 0, :]
    elif voice=="male3":
        mel = await _run_onnx(tts_onnx_male3, [seq, text_lengths, np.array(1.0, dtype=np.float32)])
        audio = ( await _run_onnx(vocoder_onnx_male3, [mel]))[0, 0, :]
    else :
        mel = await _run_onnx(tts_onnx_female3, [seq, text_lengths, np.array(1.0, dtype=np.float32)])
        audio = (await _run_onnx(vocoder_onnx_female3, [mel]))[0, 0, :]
    
    audio = (32767 * audio).astype(dtype=np.int16)
    
    wav_file = io.BytesIO()
    _save_wav(wav_file, audio)
    wav_file.seek(0)

    return StreamingResponse(io.BytesIO(wav_file.getvalue()), media_type="audio/wav")



def _should_keep_symbol(s):
    # TODO: do i really need this?
    return s in _symbol_to_id and s != '_'


def _text_to_sequence(text):
    text = text.lower()
    text = re.sub(_whitespace_re, ' ', text)
    return [_symbol_to_id[s] for s in text if _should_keep_symbol(s)]


async def _run_onnx(ort_session, input_vals):
    ort_inputs = {name.name: val for name, val in zip(ort_session.get_inputs(), input_vals)}
    ort_outs = ort_session.run(None, ort_inputs)
    print(len(ort_outs[0]))
    return ort_outs[0]


def _save_wav(filename, samples, framerate=22050):
    with contextlib.closing(wave.open(filename, "wb")) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(samples.tobytes())