from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from react_agent.models.executor.executor import agent_executor
import uvicorn

app = FastAPI(title="RePick Chat API")


class ChatRequest(BaseModel):
    message: str
    chat_history: list = []  # 선택적 채팅 기록


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # 벡터 DB 경로 설정
        db_path = r"C:\Users\user\Desktop\RePick-MLOps\data\vectordb"

        # 에이전트 실행
        response = agent_executor(db_path=db_path).invoke(
            {"input": request.message, "chat_history": request.chat_history}
        )

        return ChatResponse(response=response["output"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("app.api.chat_api:app", host="0.0.0.0", port=8000, reload=True)
