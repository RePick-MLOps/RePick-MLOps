import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)
sys.path.append(project_root)

from langchain.tools import Tool
from react_agent.tools.retriever_tool.retriever.retriever import DocumentRetriever


def retriever_tool(db_path: str, name: str = "retrieve_tool"):
    """문서 검색 도구 생성"""
    retriever = DocumentRetriever(db_path=db_path)
    return Tool(
        name=name,
        description=(
            "이 도구는 기업과 산업에 대한 기본 정보를 검색하는 필수 도구입니다.\n"
            "사용 규칙:\n"
            "1. 모든 질문에 대해 반드시 먼저 사용\n"
            "2. 검색 결과가 있으면 해당 정보로 답변\n"
            "3. 검색 결과가 없으면 즉시 '관련 정보를 찾을 수 없습니다'로 답변\n"
            "4. 부분적인 정보만 있어도 그 정보만으로 답변\n"
            "입력: 검색하고자 하는 키워드나 문장\n"
            "출력: [문서명.pdf, 페이지번호, 문단번호] 형식으로 출처 표시"
        ),
        func=retriever.search,
    )


if __name__ == "__main__":
    tool = retriever_tool(db_path=r"C:\Users\user\Desktop\RePick-MLOps\data\vectordb")
    results = tool.run(
        "롯데쇼핑의 ESG 점수를 전체 평균과 비교한 그래프가 어떻게 되어 있나요?"
    )
    print(results)
