from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from chatbot.models.chatbot import ChatAgent
import uvicorn
import logging

# logger 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="RePick Chatbot API")


# Pydantic 모델 정의
class SendMessageRequest(BaseModel):
    input: str
    session_id: str


class ChatResponse(BaseModel):
    response: str


# 전역 변수로 ChatAgent 초기화
def initialize_chat_agent():
    try:
        embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        )

        vectorstore = Chroma(
            persist_directory="/Users/naeun/working/RePick-MLOps/data/vectordb",
            embedding_function=embedding_model,
        )

        return ChatAgent(vectorstore)
    except Exception as e:
        logger.error(f"ChatAgent 초기화 중 오류 발생: {str(e)}")
        raise


chat_agent = initialize_chat_agent()


@app.post("/api/v1/chat/sendMessage", response_model=ChatResponse)
async def send_message(request: SendMessageRequest):
    try:
        logger.info(f"Received chat request: {request}")
        response = chat_agent.invoke_agent(
            {"input": request.input, "session_id": request.session_id}
        )
        logger.info(f"Generated response: {response}")
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/chat/getResponse")
async def get_response():
    return {"status": "This endpoint is unnecessary without session management"}


# 서버 상태 확인 /ping GET 엔드포인트
@app.get("/ping")
async def ping():
    return {"status": "running"}


if __name__ == "__main__":
    uvicorn.run("app.api.chatbot_api:app", host="0.0.0.0", port=8000, reload=True)
