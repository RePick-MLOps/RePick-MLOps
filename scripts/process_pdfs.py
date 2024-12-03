import re
import sys
import time
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from pathlib import Path
from src.vectorstore import VectorStore, process_pdf_directory
from src.parser import process_single_pdf
from src.graphparser.state import GraphState
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_processed_states():
    """처리된 PDF 파일 목록을 로드합니다."""
    processed_states_path = Path("./data/vectordb/processed_states.json")
    if processed_states_path.exists():
        with open(processed_states_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def is_original_pdf(filename: str, processed_states: dict) -> bool:
    """원본 PDF 파일이면서 아직 처리되지 않은 파일인지 확인합니다."""
    if filename in processed_states:
        return False

    split_pattern = r"_\d{4}_\d{4}\.pdf$"
    return filename.endswith(".pdf") and not re.search(split_pattern, filename)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
)
def process_single_pdf_with_retry(pdf_path):
    """PDF 처리를 재시도 로직과 함께 실행합니다."""
    try:
        state = process_single_pdf(pdf_path)
        if state is None:
            raise ValueError(f"PDF 처리 실패: {pdf_path}")
        return state
    except Exception as e:
        if "rate_limit_exceeded" in str(e):
            logger.warning("Rate limit 도달. 60초 대기 후 재시도...")
            time.sleep(60)  # 1분 대기
        raise


def process_new_pdfs():
    """새로운 PDF 파일들을 처리하고 상태를 저장합니다."""
    pdf_directory = "./data/pdf"
    processed_states_path = Path("./data/vectordb/processed_states.json")
    processed_states = load_processed_states()

    # 새로운 원본 PDF 파일만 필터링
    pdf_files = [
        f for f in os.listdir(pdf_directory) if is_original_pdf(f, processed_states)
    ]

    logger.info(f"처리할 새로운 PDF 파일: {len(pdf_files)}개")
    logger.info(f"PDF 파일 목록: {pdf_files}")

    if pdf_files:
        # VectorStore 초기화
        vector_store = VectorStore(persist_directory="./data/vectordb")

        # PDF 파일들을 벡터 DB에 저장
        process_pdf_directory(
            vector_store=vector_store,
            pdf_dir="./data",  # vectorstore.py에서 /pdf를 자동으로 추가함
            collection_name="pdf_collection",
        )

        # 각 파일 파싱 및 요약
        for pdf_file in pdf_files:
            try:
                pdf_path = os.path.join(pdf_directory, pdf_file)
                state = process_single_pdf_with_retry(pdf_path)

                if state is None:
                    logger.error(f"PDF 처리 실패: {pdf_file}")
                    continue

                # 상태 정보 업데이트
                state_dict = {
                    "text_summary": state.get("text_summary", {}),
                    "image_summary": state.get("image_summary", {}),
                    "table_summary": state.get("table_summary", {}),
                    "table_markdown": state.get("table_markdown", {}),
                    "page_summary": state.get("page_summary", {}),
                    "parsing_processed": True,
                    "vectorstore_processed": True,
                }

                # 기존 상태 정보와 병합
                if pdf_file in processed_states:
                    processed_states[pdf_file].update(state_dict)
                else:
                    processed_states[pdf_file] = state_dict

                logger.info(f"\n=== 처리 완료: {pdf_file} ===")
                logger.info(f"텍스트 요약 수: {len(state_dict['text_summary'])}")
                logger.info(f"이미지 요약 수: {len(state_dict['image_summary'])}")
                logger.info(f"테이블 요약 수: {len(state_dict['table_summary'])}")
                logger.info(f"테이블 마크다운 수: {len(state_dict['table_markdown'])}")
                logger.info(f"페이지 요약 수: {len(state_dict['page_summary'])}")

                # 상태 저장
                with open(processed_states_path, "w", encoding="utf-8") as f:
                    json.dump(processed_states, f, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"처리 실패 ({pdf_file}): {str(e)}")
                continue

        # 최종 상태 확인
        try:
            collection = vector_store.client.get_collection("pdf_collection")
            logger.info(f"\n=== 최종 처리 결과 ===")
            logger.info(f"최종 벡터 DB 문서 수: {collection.count()}")
            logger.info(f"처리된 PDF 파일 수: {len(pdf_files)}")
        except Exception as e:
            logger.error(f"최종 상태 확인 중 오류: {str(e)}")


if __name__ == "__main__":
    process_new_pdfs()
