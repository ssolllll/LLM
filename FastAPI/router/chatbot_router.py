from fastapi import APIRouter
from services import chatbot_service

from request import ChatbotRequest

chatbot_router = APIRouter()

@chatbot_router.post("/data/insert")
def insert_vectordb(file_path: str):
    return chatbot_service.process_insert_db(file_path)

@chatbot_router.post("/chat")
def get_response(request: ChatbotRequest):
    print(request)
    return None