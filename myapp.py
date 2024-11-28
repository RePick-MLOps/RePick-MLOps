from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
import logging

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 요청 본문 데이터 모델 정의
class SendMessageRequest(BaseModel):
    query: str

# POST /api/v1/chat/sendMessage 엔드포인트
@app.post("/api/v1/chat/sendMessage")
async def send_message(request: SendMessageRequest):
    try:
        logging.info(f"Received message: {request.query}")

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": request.query}
            ],
            max_tokens=100
        )

        logging.info(f"Processed response: {response.choices[0].message.content.strip()}")
        return {
            "status": "success",
            "response": response.choices[0].message.content.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /api/v1/chat/getResponse 엔드포인트
@app.get("/api/v1/chat/getResponse")
async def get_response():
    return {"status": "This endpoint is unnecessary without session management"}

# 서버 상태 확인 /ping GET 엔드포인트
@app.get("/ping")
async def ping():
    return {"status": "running"}