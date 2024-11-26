from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from chatbot_test.models.chatbot import Chatbot

app = FastAPI()
router = APIRouter()  # 라우터 추가
chatbot = Chatbot()

@router.get("/")  # app -> router
async def root():
    return {"message": "Welcome to the Chatbot API"}

@router.post("/chat")  # app -> router
async def chat(query: str):
    try:
        response = chatbot(query)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

app.include_router(router)  # 라우터를 앱에 포함