from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from react_agent.models.executor import agent_executor
from react_agent.models.chat import MaxIterationCallbackHandler
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="RePick Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    chat_history: list = []


class ChatResponse(BaseModel):
    response: str
    image: str | None = None


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"Received chat request: {request.message}")

        # 벡터 DB 경로 설정
        db_path = "s3://repick-chromadb/vectordb/"

        # 에이전트 실행
        agent = agent_executor(db_path=db_path)

        try:
            response = agent.invoke(
                {"input": request.message, "chat_history": request.chat_history},
                callbacks=[MaxIterationCallbackHandler(max_iterations=2)],
            )
            logger.info("Successfully processed chat request")

            # 이미지 데이터 추출
            output_text = response["output"]
            image_data = None

            if "<img src='data:image/png;base64," in output_text:
                parts = output_text.split("<img src='data:image/png;base64,")
                text_part = parts[0]
                image_part = parts[1].split("'")[0]
                output_text = text_part
                image_data = f"data:image/png;base64,{image_part}"

            return ChatResponse(response=output_text, image=image_data)

        except ValueError as e:
            logger.warning(f"Max iterations exceeded: {str(e)}")
            return ChatResponse(
                response=f"Warning: {str(e)}\n현재까지 수집된 정보로 답변드립니다.",
                image=None,
            )

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"message": "내부 서버 오류가 발생했습니다.", "error": str(e)},
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
