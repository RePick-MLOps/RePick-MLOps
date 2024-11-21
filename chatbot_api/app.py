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
class QueryRequest(BaseModel):
    query: str

# /chatbot POST 엔드포인트
@app.post("/chatbot")
async def chatbot(request: QueryRequest):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=request.query,
            max_tokens=150,
            temperature=0.7
        )
        return {"response": response["choices"][0]["text"].strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 서버 상태 확인 /ping GET 엔드포인트
@app.get("/ping")
async def ping():
    return {"status": "running"}