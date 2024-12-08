from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, model_name: str = "jhgan/ko-sbert-sts"):
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.local_db_path = Path("./data/vectordb")
        self.s3_bucket = "repick-chromadb"

    def sync_from_s3(self):
        """S3에서 vectordb 동기화"""
        try:
            self.local_db_path.parent.mkdir(parents=True, exist_ok=True)
            sync_cmd = (
                f"aws s3 sync s3://{self.s3_bucket}/vectordb {self.local_db_path}"
            )
            result = subprocess.run(
                sync_cmd, shell=True, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("S3에서 데이터 동기화 완료")
            else:
                logger.error(f"S3 동기화 실패: {result.stderr}")

        except Exception as e:
            logger.error(f"S3 동기화 오류: {str(e)}")
            raise

    def get_db(self) -> Chroma:
        """벡터스토어 로드"""
        self.sync_from_s3()

        client = chromadb.PersistentClient(
            path=str(self.local_db_path),
            settings=Settings(
                anonymized_telemetry=False, allow_reset=True, is_persistent=True
            ),
        )

        return Chroma(
            client=client,
            embedding_function=self.embeddings,
            collection_name="pdf_collection",
        )
