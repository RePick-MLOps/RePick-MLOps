from pymongo import MongoClient
from dotenv import load_dotenv
import os

def check_mongodb():    
    # .env 파일 로드
    load_dotenv()
    
    # 환경변수에서 URI 가져오기
    mongodb_uri = os.getenv("MONGO_URI")
    
    if not mongodb_uri:
        print("Error: MONGO_URI 환경변수가 설정되지 않았습니다.")
        return
    
    try:
        # MongoDB 연결 시도
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=2000)
        server_info = client.server_info()
        print(f"MongoDB 버전: {server_info['version']}")
        print("MongoDB 연결 성공!")
        
    except Exception as e:
        print(f"MongoDB 연결 실패: {e}")

if __name__ == "__main__":
    check_mongodb()