from fastapi import APIRouter
from services import chatbot_service

router = APIRouter()

@router.post("/data/insert")
def insert_vectordb(file_path: str):
    return chatbot_service.process_insert_db(file_path)
