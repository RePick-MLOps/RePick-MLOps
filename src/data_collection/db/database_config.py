from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging

load_dotenv()


def get_db_connection():
    try:
        # EC2 MongoDB 연결 정보
        EC2_HOST = os.getenv("EC2_HOST")
        EC2_PORT = int(os.getenv("EC2_PORT", "27017"))
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")

        # MongoDB 연결 URI 구성
        uri = f"mongodb://{DB_USER}:{DB_PASSWORD}@{EC2_HOST}:{EC2_PORT}/"

        # 연결 타임아웃 값을 늘리고 재시도 로직 추가
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=30000,  # 30초
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            retryWrites=True,
            retryReads=True,
            maxPoolSize=1,
        )

        # 연결 테스트
        client.admin.command("ping")
        db = client["research_db"]  # 데이터베이스 이름 유지
        logging.info("MongoDB 연결 성공")

        return db
    except Exception as e:
        logging.error(f"MongoDB 연결 실패: {str(e)}")
        raise
