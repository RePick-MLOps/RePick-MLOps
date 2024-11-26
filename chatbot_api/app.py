from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.documents import Document  # Document 임포트 추가
from typing import Optional
import logging

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    query: str


# 전역 변수로 챗봇 인스턴스 유지
chatbot = None


def initialize_chatbot():
    global chatbot
    try:
        if chatbot is None:
            # 벡터스토어 로드
            from app.vectorstore import VectorStore  # 상대 경로로 수정

            vector_store = VectorStore(persist_directory="./data/vectordb")

            chatbot = DocumentChatbot(documents, persist_directory="./data/vectordb")
            logger.info("Chatbot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {str(e)}")
        raise


@router.post("/chatbot")
async def query(request: QueryRequest):
    try:
        if chatbot is None:
            initialize_chatbot()

        response = chatbot.chat(request.query)
        return {"response": response}
    except Exception as e:
        logger.exception("Error processing chat request")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/ping")
async def ping():
    return {"status": "running"}
