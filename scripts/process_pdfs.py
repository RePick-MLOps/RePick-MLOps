import re
import sys
import time
import os
import logging
import psutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from pathlib import Path
from dotenv import load_dotenv
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

# .env 파일 로드
load_dotenv()


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
    retry=retry_if_exception_type((Exception, ValueError)),
)
def process_single_pdf_with_retry(pdf_path):
    try:
        state = process_single_pdf(pdf_path)
        if state is None:
            raise ValueError(f"PDF 처리 실패: {pdf_path}")
        return state
    except Exception as e:
        logger.error(f"PDF 처리 재시도 중 오류: {str(e)}")
        raise


def process_single_pdf(pdf_path):
    try:
        logger.info(f"=== PDF 처리 시작: {pdf_path} ===")

        # PDF 파일 유효성 검사
        if not os.path.exists(pdf_path):
            raise ValueError(f"PDF 파일이 존재하지 않습니다: {pdf_path}")

        if os.path.getsize(pdf_path) == 0:
            raise ValueError(f"PDF 파일이 비어있습니다: {pdf_path}")

        # PDF 처리 시도
        try:
            from src.parser import process_single_pdf as parser_process_pdf

            state = parser_process_pdf(pdf_path)

            # 처리 결과 검증
            if state is None:
                raise ValueError(f"PDF 처리 결과가 없습니다: {pdf_path}")

            required_keys = [
                "text_summary",
                "image_summary",
                "table_summary",
                "page_summary",
            ]
            missing_keys = [key for key in required_keys if key not in state]
            if missing_keys:
                logger.warning(f"누락된 키가 있습니다: {missing_keys}")
                # 누락된 키에 대해 빈 딕셔너리 추가
                for key in missing_keys:
                    state[key] = {}

            logger.info(f"PDF 처리 완료: {os.path.basename(pdf_path)}")
            logger.info(f"처리된 데이터 키: {list(state.keys())}")
            return state

        except Exception as e:
            logger.error(f"PDF 파싱 중 오류 발생: {str(e)}", exc_info=True)
            # 기본 상태 반환
            return {
                "text_summary": {},
                "image_summary": {},
                "table_summary": {},
                "table_markdown": {},
                "page_summary": {},
            }

    except Exception as e:
        logger.error(f"PDF 처리 중 치명적 오류 발생: {str(e)}", exc_info=True)
        return None


def process_new_pdfs():
    """새로운 PDF 파일들을 처리하고 상태를 저장합니다."""
    pdf_directory = "./data/pdf"
    processed_states_path = Path("./data/vectordb/processed_states.json")
    processed_states = load_processed_states()

    # 디버깅: 기존 상태 출력
    print("\n=== 기존 처리 상태 ===")
    print(f"처리된 파일 수: {len(processed_states)}")
    print(f"처리된 파일 목록: {list(processed_states.keys())}")

    # 새로운 원본 PDF 파일만 필터링
    pdf_files = [
        f for f in os.listdir(pdf_directory) if is_original_pdf(f, processed_states)
    ]

    logger.info(f"\n=== 새로운 PDF 파일 정보 ===")
    logger.info(f"처리할 새로운 PDF 파일: {len(pdf_files)}개")
    logger.info(f"PDF 파일 목록: {pdf_files}")

    if pdf_files:
        # VectorStore 초기화
        vector_store = VectorStore(persist_directory="./data/vectordb")

        for pdf_file in pdf_files:
            try:
                pdf_path = os.path.join(pdf_directory, pdf_file)
                state = process_single_pdf_with_retry(pdf_path)

                if state is None:
                    logger.error(f"PDF 처리 실패: {pdf_file}")
                    continue

                # 디버깅: 상태 병합 전 출력
                logger.info(f"\n=== 상태 병합 전 ({pdf_file}) ===")
                if pdf_file in processed_states:
                    logger.info(f"기존 상태: {processed_states[pdf_file]}")
                else:
                    logger.info("기존 상태 없음")

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

                # 디버깅: 새로운 상태 출력
                logger.info(f"새로운 상태: {state_dict}")

                # 기존 상태 정보와 병합
                if pdf_file in processed_states:
                    processed_states[pdf_file].update(state_dict)
                    logger.info(f"상태 병합 완료: {processed_states[pdf_file]}")
                else:
                    processed_states[pdf_file] = state_dict
                    logger.info("새로운 상태 추가됨")

                logger.info(f"\n=== 처리 완료: {pdf_file} ===")
                logger.info(f"텍스트 요약 수: {len(state_dict['text_summary'])}")
                logger.info(f"이미지 요약 수: {len(state_dict['image_summary'])}")
                logger.info(f"테이블 요약 수: {len(state_dict['table_summary'])}")
                logger.info(f"테이블 마크다운 수: {len(state_dict['table_markdown'])}")
                logger.info(f"페이지 요약 수: {len(state_dict['page_summary'])}")

                # 상태 저장
                with open(processed_states_path, "w", encoding="utf-8") as f:
                    json.dump(processed_states, f, ensure_ascii=False, indent=2)
                logger.info("상태 파일 저장 완료")

            except Exception as e:
                logger.error(f"처리 실패 ({pdf_file}): {str(e)}")
                continue


if __name__ == "__main__":
    process_new_pdfs()
