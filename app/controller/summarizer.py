from fastapi import BackgroundTasks, APIRouter
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from haystack import Document
from typing import List, Optional

from ..config import DB_HOST, DB_PORT, DB_USER, DB_PW, ES_CONN_SCHEME
from ..utils.summarizer import Summarizer
router = APIRouter()
es = Elasticsearch(["{}://{}:{}".format(ES_CONN_SCHEME, DB_HOST, DB_PORT)],
                   http_auth=(DB_USER, DB_PW), verify_certs=False)
import os
import time
import logging
logger = logging.getLogger(__name__)

sumamrizer_path = os.path.join(
    os.getenv("MODEL_BASE_PATH", "app/models/"), "nlp/sshleifer/distilbart-cnn-12-6"
)
logger.info("USING SUMMARIZER FROM "+sumamrizer_path)
summarizer = Summarizer()


class SummarizerModel(BaseModel):
    text: str
    ratio: Optional[float] = 0.2
    
@router.post("/summarize")
def summarize(request: SummarizerModel):
    start = time.time()
    DOCS = []
    doc = request.text
    total_words = len(doc.split())
    DOCS.append(Document(text=str(doc)))
    response = summarizer.predict(documents=DOCS, min_length=int(total_words*request.ratio), max_length=int(total_words * min(1,request.ratio+0.05)))
    response[0].time=(time.time()-start)
    return response[0]
