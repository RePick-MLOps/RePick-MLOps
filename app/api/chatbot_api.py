from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
import json
from pathlib import Path
from app.chatbot import DocumentChatbot
from src.vectorstore import VectorStore


app = FastAPI()


class QueryRequest(BaseModel):
    query: str


# 전역 변수로 챗봇 인스턴스 유지
chatbot = None


def initialize_chatbot():
    global chatbot
    if chatbot is None:
        # 벡터스토어 로드
        vector_store = VectorStore(persist_directory="./data/vectordb")

        # 처리된 상태 로드
        processed_states_path = Path("./data/vectordb/processed_states.json")
        with open(processed_states_path, "r", encoding="utf-8") as f:
            processed_states = json.load(f)

        # 모든 문서 준비
        documents = []
        for pdf_state in processed_states.values():
            # 텍스트 요약 추가
            for page, summary in pdf_state["text_summary"].items():
                documents.append(
                    Document(
                        page_content=summary,
                        metadata={"type": "text_summary", "page": page},
                    )
                )

            # 이미지 요약 추가
            for image_id, summary in pdf_state["image_summary"].items():
                documents.append(
                    Document(
                        page_content=summary,
                        metadata={"type": "image_summary", "id": image_id},
                    )
                )

            # 테이블 요약 추가
            for table_id, summary in pdf_state["table_summary"].items():
                documents.append(
                    Document(
                        page_content=summary,
                        metadata={"type": "table_summary", "id": table_id},
                    )
                )

        # 챗봇 초기화
        chatbot = DocumentChatbot(documents, persist_directory="./data/vectordb")


@app.post("/chatbot")
async def query(request: QueryRequest):
    try:
        # 챗봇이 초기화되지 않았다면 초기화
        if chatbot is None:
            initialize_chatbot()

        # 질문에 대한 답변 생성
        response = chatbot.chat(request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/ping")
async def ping():
    return {"status": "running"}
