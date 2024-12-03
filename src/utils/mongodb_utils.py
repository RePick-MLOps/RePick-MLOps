import os
import logging
import requests
import ssl
from pymongo import MongoClient
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBHandler:
    def __init__(self):
        load_dotenv()
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.mongodb_uri = os.getenv("MONGO_URI")

        try:
            # SSL/TLS 설정 수정
            self.client = MongoClient(
                self.mongodb_uri,
                tls=True,
                tlsAllowInvalidCertificates=True,  # 개발 환경에서만 사용하세요
                serverSelectionTimeoutMS=20000,
                connectTimeoutMS=20000,
            )

            # 연결 테스트
            self.client.admin.command("ping")
            logger.info("MongoDB 연결 성공")

        except Exception as e:
            logger.error(f"MongoDB 연결 실패: {str(e)}")
            raise

        self.db = self.client.get_database("research_db")
        self.collection = self.db["reports"]

        # 문서 수 확인
        doc_count = self.collection.count_documents({})
        logger.info(f"reports 컬렉션의 전체 문서 수: {doc_count}")

    def download_pdf(self, output_dir: str = "data/pdf", limit: int = 10) -> bool:
        output_dir = os.path.join(self.base_dir, output_dir)
        try:
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)

            # 이미 다운로드된 파일들의 report_id 목록 생성
            existing_files = {
                os.path.splitext(f)[0]
                for f in os.listdir(output_dir)
                if f.endswith(".pdf")
            }
            logger.info(f"이미 존재하는 PDF 파일 수: {len(existing_files)}")

            # MongoDB에서 아직 다운로드되지 않은 문서들만 조회
            downloaded_count = 0
            cursor = self.collection.find({})

            for doc in cursor:
                if downloaded_count >= limit:
                    break

                report_id = str(doc["report_id"])
                if report_id in existing_files:
                    continue

                output_path = os.path.join(output_dir, f"{report_id}.pdf")

                # PDF 링크가 없는 경우 로그 출력 후 다음 문서로 넘어감
                if "pdf_link" not in doc:
                    logger.warning(f"PDF 링크 없음: report_id {report_id}")
                    continue

                logger.info(f"다운로드 시도: {doc['pdf_link']}")

                # PDF 다운로드 시도
                try:
                    response = requests.get(
                        doc["pdf_link"],
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                        },
                        timeout=30,
                    )
                    response.raise_for_status()

                    # PDF 파일 저장
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"다운로드 완료: {output_path}")
                    downloaded_count += 1

                except requests.RequestException as e:
                    logger.error(f"다운로드 실패 (report_id: {report_id}): {str(e)}")
                    continue

            logger.info(f"새로 다운로드한 PDF 파일 수: {downloaded_count}")
            return True

        except Exception as e:
            logger.error(f"처리 중 오류 발생: {e}")
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()


if __name__ == "__main__":
    with MongoDBHandler() as handler:
        handler.download_pdf(limit=5)  # 5개의 문서만 처리
