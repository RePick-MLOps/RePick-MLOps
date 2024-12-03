from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from models.executor import agent_executor
from chat_history import ChatHistoryManager  # ChatHistoryManager import
import uvicorn

app = FastAPI(title="RePick Chat API")

# ChatHistoryManager 인스턴스 생성
history_manager = ChatHistoryManager()


class ChatRequest(BaseModel):
    message: str
    chat_history: list = []


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # db_path 설정
        db_path = r"C:\Users\user\Desktop\RePick-MLOps\data\vectordb"

        # 에이전트 실행 및 채팅 기록 추가
        agent = agent_executor(db_path=db_path)
        agent_with_history = history_manager.create_agent_with_history(agent)

        response = agent_with_history.invoke(
            {"input": request.message, "chat_history": request.chat_history}
        )

        return ChatResponse(response=response["output"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
