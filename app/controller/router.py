from fastapi import APIRouter

from . import scraper
from . import transcriber

router = APIRouter()

router.include_router(scraper.router, tags=["scraper"])
router.include_router(transcriber.router, tags=["transcriber"])
