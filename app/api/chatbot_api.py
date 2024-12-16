import sys
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import asyncio

from chatbot.models.chatbot import chatbot

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# 로거 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="RePick Chatbot API")

# Pydantic 모델 정의
class SendMessageRequest(BaseModel):
    request: str

class ChatResponse(BaseModel):
    response: str

# QA Chain 초기화
qa_chain = chatbot()

# ThreadPoolExecutor 초기화
executor = ThreadPoolExecutor(max_workers=10)

async def invoke_chatbot(request: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, qa_chain.invoke, request)

@app.post("/api/v1/chat/sendMessage", response_model=ChatResponse)
async def send_message(request: SendMessageRequest):
    try:
        logger.info(f"Received chat request: {request}")
        response = await invoke_chatbot(request.request)
        logger.info(f"Generated response: {response}")
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ping")
async def ping():
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api.chatbot_api:app", host="0.0.0.0", port=8000, reload=True)
