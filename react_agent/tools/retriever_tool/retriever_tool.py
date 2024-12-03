import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)
sys.path.append(project_root)

from langchain.tools import Tool
from .retriever.retriever import DocumentRetriever


def retriever_tool(db_path: str, name: str = "retrieve_tool"):
    """문서 검색 도구 생성"""
    retriever = DocumentRetriever(db_path=db_path)
    return Tool(
        name=name,
        description="데이터베이스 검색 도구로, 기업과 산업에 대한 기본 정보를 찾는 데 사용됩니다.",
        func=retriever.search,
    )


if __name__ == "__main__":
    tool = retriever_tool(db_path=r"C:\Users\user\Desktop\RePick-MLOps\data\vectordb")
    results = tool.run(
        "롯데쇼핑의 ESG 점수를 전체 평균과 비교한 그래프가 어떻게 되어 있나요?"
    )
    print(results)
