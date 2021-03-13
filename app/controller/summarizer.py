import time
import os
import logging
import json
import jwt
import requests
import base64

from fastapi import APIRouter, BackgroundTasks, File, Header, UploadFile
from typing import List, Optional
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from haystack import Document

from ..config import DB_HOST, DB_PORT, DB_PW, DB_USER, ES_CONN_SCHEME, PG
from ..utils.text_processor import get_text_from_file,  get_file_path
from ..utils.transcriber.transcriber import transcribe_summarize_handler, upload_summarize_handler

router = APIRouter()
es = Elasticsearch(["{}://{}:{}".format(ES_CONN_SCHEME, DB_HOST, DB_PORT)],
                   http_auth=(DB_USER, DB_PW), verify_certs=False)

logger = logging.getLogger(__name__)


class SummarizerModel(BaseModel):
    text: str
    ratio: Optional[float] = 0.2


class TranscribeSummarizeModel(BaseModel):
    vid: str
    reg_id: str


class UploadSummarizeModel(BaseModel):
    file_name: str
    file_data: str
    reg_id: str


@router.post("/transcribe-and-summarize")
def transcribe_summarize(request: TranscribeSummarizeModel, background_tasks: BackgroundTasks):
    print(request.vid, request.reg_id)
    background_tasks.add_task(transcribe_summarize_handler,
                              vid=request.vid, reg_id=request.reg_id, ratio=0.5)
    return {'ok': True, 'text': "You're video has been queued for transcription and summarization"}


@router.post("/upload-summarize")
async def upload_summarize(request: UploadSummarizeModel, background_tasks: BackgroundTasks, authorization: Optional[str] = Header(None)):
    try:
        res = requests.get('{}/jwt_secrets?'.format(PG))
        res = json.loads(res.content)
        secret = res[0]['secret']
        print(secret)
        payload = jwt.decode(authorization, secret, algorithms=["HS256"])
        email = payload["email"]
        print(email)
    except Exception as e:
        print(e)
        return {'ok': False}

    name = request.file_name
    ext = name[name.rindex('.')+1:]
    loc_path = get_file_path(name)
    header, encoded = request.file_data.split(",", 1)
    print('header\n{}'.format(header))
    print('data\n{}'.format(encoded[:100]))
    contents = base64.b64decode(encoded)
    with open(loc_path, 'wb') as f:
        f.write(contents)
    text = get_text_from_file(ext, loc_path)
    print(text)
    background_tasks.add_task(upload_summarize_handler, text, request.reg_id)
    return {'ok': True, 'text': 'Summarization for your file has started'}
