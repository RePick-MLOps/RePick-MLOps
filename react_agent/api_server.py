from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models.executor import agent_executor
from models.chat import MaxIterationCallbackHandler
from chat_history import ChatHistoryManager
from io import BytesIO
import base64
import re
import uvicorn

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


class ChatRequest(BaseModel):
    message: str
    chat_history: list = []


class ChatResponse(BaseModel):
    response: str
    image: str = None


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # db_path 설정
        db_path = r"C:\Users\user\Desktop\RePick-MLOps\data\vectordb"

        # 최대 2번의 도구 사용만 허용하는 콜백 핸들러 생성
        callback = MaxIterationCallbackHandler(max_iterations=2)

        # 에이전트 실행 및 채팅 기록 추가
        agent = agent_executor(db_path=db_path)
        agent_with_history = history_manager.create_agent_with_history(agent)

        try:
            response = agent_with_history.invoke(
                {"input": request.message, "chat_history": request.chat_history},
                callbacks=[callback]  # 콜백 핸들러 추가
            )
        except ValueError as e:
            # 최대 반복 횟수 초과 시 현재까지의 정보로 응답
            return ChatResponse(
                response=f"Warning: {str(e)}\n현재까지 수집된 정보로 답변드립니다.",
                image=None
            )
        
        response = agent_with_history.invoke(
            {"input": request.message, "chat_history": request.chat_history}
        )
        
        # 응답에서 Base64 이미지 추출
        image_data = None
        output_text = response["output"]
        
        # Base64 이미지 데이터 찾기
        base64_pattern = r'data:image/png;base64,[A-Za-z0-9+/=]+'
        match = re.search(base64_pattern, output_text)
        if match:
            image_data = match.group(0)
            # 텍스트에서 이미지 데이터 제거
            output_text = re.sub(base64_pattern, '', output_text)

        return ChatResponse(response=output_text, image=image_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# 이미지 테스트를 위한 엔드포인트 추가
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
