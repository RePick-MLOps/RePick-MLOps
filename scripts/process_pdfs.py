import re
import os
import json
from pathlib import Path
from src.vectorstore import VectorStore, process_pdf_directory
from src.parser import process_single_pdf


def load_processed_states():
    """처리된 PDF 파일 목록을 로드합니다."""
    processed_files = set()
    if os.path.exists("data/vectordb/processed_files.txt"):
        with open("data/vectordb/processed_files.txt", "r") as f:
            for line in f:
                # 파일 경로에서 파일명만 추출
                filename = os.path.basename(line.strip())
                processed_files.add(filename)
    return processed_files


def is_original_pdf(filename: str, processed_files: set) -> bool:
    """
    원본 PDF 파일이면서 아직 처리되지 않은 파일인지 확인합니다.
    """
    if filename in processed_files:
        return False

    split_pattern = r"_\d{4}_\d{4}\.pdf$"
    return filename.endswith(".pdf") and not re.search(split_pattern, filename)


def process_new_pdfs():
    """새로운 PDF 파일들을 처리하고 상태를 저장합니다."""
    pdf_directory = "./data/pdf"
    processed_states_path = Path("./data/vectordb/processed_states.json")

    # 1. 이전에 처리된 상태 로드
    if processed_states_path.exists():
        with open(processed_states_path, "r", encoding="utf-8") as f:
            processed_states = json.load(f)
    else:
        processed_states = {}

    # processed_files 로드
    processed_files = load_processed_states()

    # 2. 새로운 원본 PDF 파일만 필터링
    pdf_files = [
        f
        for f in os.listdir(pdf_directory)
        if is_original_pdf(f, processed_files) and f not in processed_states
    ]

    print(f"처리할 새로운 PDF 파일: {len(pdf_files)}개")

    # 3. 새로운 파일들 처리
    if pdf_files:
        print(f"새로운 PDF 파일 {len(pdf_files)}개를 처리합니다.")

        # 3.1 벡터 DB에 저장 - 필터링된 파일들만 처리하도록 수정
        vector_store = VectorStore(persist_directory="./data/vectordb")
        process_pdf_directory(
            vector_store=vector_store,
            pdf_dir="./data",
            collection_name="pdf_collection",
        )

        # 3.2 각 파일 파싱 및 요약
        for pdf_file in pdf_files:
            try:
                pdf_path = os.path.join(pdf_directory, pdf_file)
                state = process_single_pdf(pdf_path)

                # GraphState 객체를 딕셔너리로 변환
                state_dict = {
                    "text_summary": getattr(state, "text_summary", {}),
                    "image_summary": getattr(state, "image_summary", {}),
                    "table_summary": getattr(state, "table_summary", {}),
                }

                # 디버깅을 위한 로깅 추가
                print(f"텍스트 요약 수: {len(state_dict['text_summary'])}")
                print(f"이미지 요약 수: {len(state_dict['image_summary'])}")
                print(f"테이블 요약 수: {len(state_dict['table_summary'])}")

                processed_states[pdf_file] = state_dict

                print(f"처리 완료: {pdf_file}")
            except Exception as e:
                print(f"처리 실패 ({pdf_file}): {str(e)}")

        # 3.3 처리된 상태 저장
        with open(processed_states_path, "w", encoding="utf-8") as f:
            json.dump(processed_states, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    process_new_pdfs()
