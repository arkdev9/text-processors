from fastapi import APIRouter

from . import scraper

router = APIRouter()

router.include_router(scraper.router, tags=["scraper"])
