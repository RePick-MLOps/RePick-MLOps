from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import socket
import json
import logging

host = "127.0.0.1"
port = 8000

app = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 요청 본문 데이터 모델 정의
class QueryRequest(BaseModel):
    query: str

# 소켓을 통해 질문에 대한 답변을 받는 함수
def get_answer(query: str) -> str:
    try:
        mySocket = socket.socket()
        mySocket.connect((host, port))

        json_data = {
            'Query': query
            }
        message = json.dumps(json_data)
        mySocket.send(message.encode())

        data = mySocket.recv(2048).decode()
        ret_data = json.loads(data)

        mySocket.close()

        if 'response' not in ret_data:
            raise ValueError("Invalid response format")

        return ret_data['response']
    except Exception as ex:
        raise Exception(f"Socket Error: {ex}")

# /chatbot POST 엔드포인트
@app.post("/chatbot")
async def query(request: QueryRequest):
    try:
        # 사용자의 query를 받아 답변을 반환
        ret = get_answer(query=request.query)
        return {"response": ret}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(ex)}")

# 서버 상태 확인 /ping GET 엔드포인트
@app.get("/ping")
async def ping():
    return {"status": "running"}