from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging

load_dotenv()


def get_db_connection():
    try:
        host = os.environ.get("EC2_HOST")
        port = os.environ.get("EC2_PORT")
        user = os.environ.get("DB_USER")
        password = os.environ.get("DB_PASSWORD")

        # 연결 정보 로깅 (비밀번호 제외)
        logging.info(f"MongoDB Connection Info:")
        logging.info(f"Host: {host}")
        logging.info(f"Port: {port}")
        logging.info(f"User: {user}")

        uri = f"mongodb://{user}:{password}@{host}:{port}/admin"
        client = MongoClient(uri)

        # 연결 테스트
        client.admin.command("ping")
        logging.info("Successfully connected to MongoDB")

        return client.research_db

    except Exception as e:
        logging.error(f"MongoDB connection error: {str(e)}")
        logging.error(f"Connection details:")
        logging.error(f"Host: {os.getenv('EC2_HOST')}")
        logging.error(f"Port: {os.getenv('EC2_PORT')}")
        logging.error(f"User: {os.getenv('DB_USER')}")
        raise
