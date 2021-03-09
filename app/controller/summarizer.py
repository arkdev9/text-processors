from typing import List, Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, BackgroundTasks
from haystack import Document
from pydantic import BaseModel

from ..config import DB_HOST, DB_PORT, DB_PW, DB_USER, ES_CONN_SCHEME
from ..utils.transcriber.transcriber import (transcribe_handler_ext_summarize)

router = APIRouter()
es = Elasticsearch(["{}://{}:{}".format(ES_CONN_SCHEME, DB_HOST, DB_PORT)],
                   http_auth=(DB_USER, DB_PW), verify_certs=False)
import logging
import os
import time

logger = logging.getLogger(__name__)

# sumamrizer_path = os.path.join(
#     os.getenv("MODEL_BASE_PATH", "app/models/"), "nlp/sshleifer/distilbart-cnn-12-6"
# )
# logger.info("USING SUMMARIZER FROM "+sumamrizer_path)
# summarizer = Summarizer()


class SummarizerModel(BaseModel):
    text: str
    ratio: Optional[float] = 0.2
    
# @router.post("/summarize")
# def summarize(request: SummarizerModel):
#     start = time.time()
#     DOCS = []
#     doc = request.text
#     total_words = len(doc.split())
#     DOCS.append(Document(text=str(doc)))
#     response = summarizer.predict(documents=DOCS, min_length=int(total_words*request.ratio), max_length=int(total_words * min(1,request.ratio+0.05)))
#     response[0].time=(time.time()-start)
#     return response[0]



class TranscribeExtModel(BaseModel):
    vid: str
    reg_id: str

@router.post("/transcribe-and-summarize")
def transcribe_ext(request: TranscribeExtModel, background_tasks: BackgroundTasks):
    print(request.vid, request.reg_id)
    background_tasks.add_task(transcribe_handler_ext_summarize,vid=request.vid, reg_id=request.reg_id,ratio=0.5)
    return {'ok': True, 'text': "You're video has been queued for transcription"}
