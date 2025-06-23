import logging

import uvicorn
from fastapi import FastAPI

from router.chatbot_router import chatbot_router
from router.finance_assistant import finance_router
from router.summarize_router import summarize_router

logger = logging.getLogger("main")

app = FastAPI()

app.include_router(chatbot_router)
app.include_router(finance_router)
app.include_router(summarize_router)

if __name__ == "__main__":
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=9000
        )
    except Exception as e:
        logger.error(e)