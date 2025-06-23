from fastapi import APIRouter
from services import chatbot_service

from request import ChatbotRequest

finance_router = APIRouter()

@finance_router.post("/youtube/summarize")
def summarize_ytube(request):

    ## youtube to text


    ## text to summarize
    """
    llm summarize text
    """


    return response
