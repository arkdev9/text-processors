from fastapi import BackgroundTasks, APIRouter
from pydantic import BaseModel

from ..utils.transcriber.transcriber import transcribe_handler, transcribe_handler_ext
from ..utils.transcriber.utils import get_video_duration

# YT API KEY = AIzaSyBTR1FSGH1Rptk0kAtzeABPFeIvJ3NhFyM

router = APIRouter()


class TranscribeModel(BaseModel):
    vid: str


class TranscribeExtModel(BaseModel):
    vid: str
    reg_id: str


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
    background_tasks.add_task(transcribe_handler_ext,
                              vid=request.vid, reg_id=request.reg_id)
    return {'ok': True, 'text': "You're video has been queued for transcription"}
