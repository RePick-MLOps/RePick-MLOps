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
async def query(request: QueryRequest):
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": request.query}
            ],
            max_tokens=100
        )
        logging.info(f"OpenAI response: {response}")
        return {"response": response.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 서버 상태 확인 /ping GET 엔드포인트
@app.get("/ping")
async def ping():
    return {"status": "running"}