from fastapi import FastAPI
from app.api.chatbot_api import router

app = FastAPI()
app.include_router(router)
