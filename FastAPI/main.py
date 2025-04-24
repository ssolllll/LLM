import logging

import uvicorn
from fastapi import FastAPI

from router.chatbot_router import router

logger = logging.getLogger("main")

app = FastAPI()

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

if __name__ == "__main__":
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=9000
        )
    except Exception as e:
        logger.error(e)