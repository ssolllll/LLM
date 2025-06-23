from pydantic import BaseModel

class TickerRequest(BaseModel):
    query : str
    limit : int = 5

class ChatbotRequest(BaseModel):
    session_id : str
    question : str

class YoutubeRequest(BaseModel):
    url : str