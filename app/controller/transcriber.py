from fastapi import BackgroundTasks, APIRouter
from pydantic import BaseModel
from elasticsearch import Elasticsearch

from ..config import DB_HOST, DB_PORT, DB_USER, DB_PW, ES_CONN_SCHEME
from ..utils.transcriber.transcriber import transcribe_handler, transcribe_handler_ext
from ..utils.transcriber.utils import get_video_duration

router = APIRouter()
es = Elasticsearch(["{}://{}:{}".format(ES_CONN_SCHEME, DB_HOST, DB_PORT)],
                   http_auth=(DB_USER, DB_PW), verify_certs=False)


class TranscribeModel(BaseModel):
    vid: str


class TranscribeExtModel(BaseModel):
    vid: str
    reg_id: str


class GetDocumentModel(BaseModel):
    document_id: str


@router.post("/transcribe")
def transcribe(request: TranscribeModel):
    duration = get_video_duration(request.vid)
    if duration > 120:
        return {'ok': False, 'text': "Video duration is too long, limit is 120 seconds"}

    text = transcribe_handler(request.vid)
    if text == "FUCK":
        return {"ok": False, "text": "Transcription failed"}
    else:
        return {"ok": True, "text": text}


@router.post("/transcribe-ext")
def transcribe_ext(request: TranscribeExtModel, background_tasks: BackgroundTasks):
    print(request.vid, request.reg_id)
    background_tasks.add_task(transcribe_handler_ext,
                              vid=request.vid, reg_id=request.reg_id)
    return {'ok': True, 'text': "You're video has been queued for transcription"}


@router.post('/get-document')
def get_document(request: GetDocumentModel):
    resp = es.search(
    index="webextension",
    body={
        "query": {
            "match": {
                "source_id":request.document_id
            }
        }
    })
    documents = resp["hits"]["hits"]
    resp_doc = {"_source":{"text":"","summary":""}}
    for doc in documents:
        if "summary" in  doc["_source"].keys():
            resp_doc["_source"]["summary"]+=doc["_source"]["summary"]
        resp_doc["_source"]["text"]+=doc["_source"]["text"]
    return {"resp":resp_doc}