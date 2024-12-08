import os
import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)
sys.path.append(project_root)

from langchain.tools import Tool
from react_agent.tools.retriever_tool.retriever.retriever import DocumentRetriever


def retriever_tool(db_path: str | Path, name: Optional[str] = "retrieve_tool") -> Tool:
    """문서 검색 도구를 생성합니다.

    Args:
        db_path: 벡터 데이터베이스 경로
        name: 도구 이름 (기본값: "retrieve_tool")

    Returns:
        Tool: 문서 검색을 위한 LangChain Tool 객체

    Raises:
        ValueError: db_path가 존재하지 않는 경우
    """
    if not Path(db_path).exists():
        raise ValueError(f"데이터베이스 경로가 존재하지 않습니다: {db_path}")

    retriever = DocumentRetriever(db_path=db_path)

    return Tool(
        name=name,
        description="""
            이 도구는 기업과 산업에 대한 기본 정보를 검색하는 필수 도구입니다.
            사용 규칙:
            1. 모든 질문에 대해 반드시 먼저 사용
            2. 검색 결과가 있으면 해당 정보로 답변
            3. 검색 결과가 없으면 즉시 '관련 정보를 찾을 수 없습니다'로 답변
            4. 부분적인 정보만 있어도 그 정보만으로 답변
            입력: 검색하고자 하는 키워드나 문장
            출력: [문서명.pdf, 페이지번호, 문단번호] 형식으로 출처 표시
        """.strip(),
        func=retriever.search,
    )


if __name__ == "__main__":
    tool = retriever_tool(db_path="./data/vectordb")
    results = tool.run(
        "롯데쇼핑의 ESG 점수를 전체 평균과 비교한 그래프가 어떻게 되어 있나요?"
    )
    print(results)
