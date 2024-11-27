import os
import logging
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBHandler:
    def __init__(self):
        load_dotenv()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.mongodb_uri = os.getenv("MONGO_URI")
        self.client = MongoClient(self.mongodb_uri)
        self.db = self.client['research_db']
        self.collection = self.db['reports']
        
        # 문서 수 확인
        doc_count = self.collection.count_documents({})
        logger.info(f"reports 컬렉션의 전체 문서 수: {doc_count}")

    def download_pdf(self, output_dir: str = 'data/pdf', limit: int = 10) -> bool:
        output_dir = os.path.join(self.base_dir, output_dir)
        try:
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)

            # MongoDB에서 10개의 문서만 조회
            documents = list(self.collection.find({}).limit(limit))
            logger.info(f"가져온 문서 수: {len(documents)}")

            for doc in documents:
                report_id = str(doc['report_id'])
                output_path = os.path.join(output_dir, f"{report_id}.pdf")
                
                # PDF 링크가 없는 경우 로그 출력 후 다음 문서로 넘어감
                if 'pdf_link' not in doc:
                    logger.warning(f"PDF 링크 없음: report_id {report_id}")
                    continue

                logger.info(f"다운로드 시도: {doc['pdf_link']}")
                
                # PDF 다운로드 시도
                try:
                    response = requests.get(
                        doc['pdf_link'],
                        headers={ # 브라우저처럼 보이게 하는 헤더
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        },
                        timeout=30 # 30초 타임아웃
                    )
                    response.raise_for_status()
                    
                    # PDF 파일 저장
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"다운로드 완료: {output_path}")
                
                except requests.RequestException as e:
                    logger.error(f"다운로드 실패 (report_id: {report_id}): {str(e)}")
                    continue

            return True

        except Exception as e:
            logger.error(f"처리 중 오류 발생: {e}")
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

if __name__ == '__main__':
    with MongoDBHandler() as handler:
        handler.download_pdf(limit=10)  # 10개의 문서만 처리