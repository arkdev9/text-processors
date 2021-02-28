from fastapi import BackgroundTasks, APIRouter
from pydantic import BaseModel

from ..utils.transcriber.transcriber import transcribe_handler

router = APIRouter()


class TranscribeModel(BaseModel):
    vid: str


@router.post("/transcribe")
def transcribe(request: TranscribeModel, background_tasks: BackgroundTasks):
    text = transcribe_handler(request.vid)
    if text == "FUCK":
        return {"ok": False, "text": "Transcription failed"}
    else:
        return {"ok": True, "text": text}
