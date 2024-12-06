from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models.executor import agent_executor
from chat_history import ChatHistoryManager
from io import BytesIO
import base64
import re
import uvicorn
import os
import logging
from typing import Optional

app = FastAPI(title="RePick Chat API")

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ChatHistoryManager 인스턴스 생성
history_manager = ChatHistoryManager()

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    chat_history: list = []


class ChatResponse(BaseModel):
    response: str
    image: str | None = None


@app.get("/")
async def root():
    return {"message": "Welcome to the RePick Chat API!"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"Received request: {request}")
        
        # db_path 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, "data", "vectordb")
        
        if not os.path.exists(db_path):
            logger.error(f"Database path does not exist: {db_path}")
            raise HTTPException(status_code=500, detail=f"Database path not found: {db_path}")
            
        logger.info(f"Using database path: {db_path}")

        # 에이전트 실행
        agent = agent_executor(db_path=db_path)
        agent_with_history = history_manager.create_agent_with_history(agent)

        try:
            logger.info("Invoking agent...")
            # 검색 키워드 로깅 추가
            logger.info(f"Searching for keywords related to: {request.message}")
            
            response = agent_with_history.invoke(
                {
                    "input": request.message,
                    "chat_history": request.chat_history[-5:]
                }
            )
            
            # 검색 결과 로깅
            logger.info(f"Retrieved documents: {response.get('intermediate_steps', [])}")
            logger.info(f"Agent response: {response}")
            
        except Exception as e:
            logger.error(f"Error during agent invocation: {str(e)}", exc_info=True)
            return ChatResponse(
                response=f"죄송합니다. 문서 검색 중 오류가 발생했습니다. 다시 시도해 주세요.",
                image=""
            )

        # 응답 처리
        image_data = ""
        output_text = response["output"]
        
        # 검색된 문서 출처 추가
        if "source_documents" in response:
            sources = [f"- {doc.metadata.get('source', '알 수 없는 출처')}, 페이지: {doc.metadata.get('page', 'N/A')}"
                      for doc in response["source_documents"]]
            output_text += "\n\n출처:\n" + "\n".join(sources)

        # Base64 이미지 데이터 찾기
        base64_pattern = r'data:image/png;base64,[A-Za-z0-9+/=]+'
        match = re.search(base64_pattern, output_text)
        if match:
            image_data = match.group(0)
            output_text = re.sub(base64_pattern, '', output_text)

        return ChatResponse(
            response=output_text,
            image=image_data
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/test-image", response_class=HTMLResponse)
async def test_image():
    import matplotlib.pyplot as plt
    import numpy as np

    # 간단한 테스트 그래프 생성
    plt.figure(figsize=(10, 6))
    x = np.linspace(0, 10, 100)
    plt.plot(x, np.sin(x))
    plt.title('Test Plot')
    
    # 이미지를 Base64로 변환
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode()
    
    # HTML로 반환
    html_content = f"""
    <html>
        <body>
            <h1>Test Image</h1>
            <img src="data:image/png;base64,{img_base64}"/>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
