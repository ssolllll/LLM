from fastapi import APIRouter, Query, HTTPException
from services.summarize_service import process_youtube_summary, validate_youtube_url
from request.request_model import YoutubeRequest

summarize_router = APIRouter()

@summarize_router.post("/summarize")
async def summarize_youtube(request: YoutubeRequest):
    if not validate_youtube_url(request.url):
        raise HTTPException(status_code=400, detail="올바르지 않은 Youtube URL입니다.")
    
    result = process_youtube_summary(request.url)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result