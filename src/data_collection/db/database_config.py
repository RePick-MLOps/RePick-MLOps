from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging

load_dotenv()


def get_db_connection():
    try:
        host = os.getenv("EC2_HOST")
        port = os.getenv("EC2_PORT")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")

        # 연결 문자열 생성
        uri = f"mongodb://{user}:{password}@{host}:{port}/research_db?authSource=admin&authMechanism=SCRAM-SHA-1"

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
