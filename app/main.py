from fastapi import FastAPI
from .api.chatbot_api import router

app = FastAPI(title="RePick API")


# root 엔드포인트를 라우터 등록 전에 정의
@app.get("/")
async def root():
    return {"message": "Welcome to RePick API"}


# 라우터 등록
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
