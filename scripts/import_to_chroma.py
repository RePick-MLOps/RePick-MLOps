import json
import logging
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.vectorstore import VectorStore
from langchain.schema import Document

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def import_json_to_chroma(json_path: str = "./data/vectordb/processed_states.json"):
    """JSON 파일에서 처리된 데이터를 읽어 Chroma 벡터 데이터베이스에 저장합니다."""
    try:
        # JSON 파일 읽기
        logger.info(f"JSON 파일 읽기 시작: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            processed_states = json.load(f)
        logger.info(f"총 {len(processed_states)}개의 PDF 파일 데이터 로드됨")

        # VectorStore 초기화
        vector_store = VectorStore(
            persist_directory="./data/vectordb", collection_name="pdf_collection"
        )
        logger.info("VectorStore 초기화 완료")

        # 처리할 요약 타입들
        summary_types = [
            "text_summary",
            "image_summary",
            "table_summary",
            "table_markdown",
        ]
        total_added = 0

        for pdf_file, state in processed_states.items():
            logger.info(f"\n처리 중인 파일: {pdf_file}")
            for summary_type in summary_types:
                if state.get(summary_type):
                    texts = []
                    metadatas = []
                    for idx, text in state[summary_type].items():
                        texts.append(text)
                        metadatas.append(
                            {
                                "source": pdf_file,
                                "type": summary_type,
                                "index": idx,
                                "page_number": idx,
                            }
                        )
                        total_added += 1

                    if texts:
                        try:
                            documents = [
                                Document(page_content=text, metadata=metadata)
                                for text, metadata in zip(texts, metadatas)
                            ]
                            vector_store.add_documents(documents=documents)
                            logger.info(
                                f"  - {summary_type}: {len(texts)}개 임베딩 추가됨"
                            )
                        except Exception as e:
                            logger.error(
                                f"  - {summary_type} 처리 중 오류 발생: {str(e)}"
                            )
                            continue

        logger.info(f"\n처리 완료:")
        logger.info(f"- 추가된 문서: {total_added}개")

    except Exception as e:
        logger.error(f"처리 중 예상치 못한 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    json_path = (
        sys.argv[1] if len(sys.argv) > 1 else "./data/vectordb/processed_states.json"
    )
    import_json_to_chroma(json_path)
