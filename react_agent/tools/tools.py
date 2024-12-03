from react_agent.tools.news_tool.news_search import news_search_tool
from react_agent.tools.retriever_tool.retriever_tool import retriever_tool
from react_agent.tools.python_executor.python_executor import create_python_executor
from typing import List
from langchain_community.tools import BaseTool
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


def tool_list(db_path: str) -> List[BaseTool]:
    """모든 도구들을 생성하고 리스트로 반환합니다.

    Args:
        db_path (str): 문서 검색을 위한 벡터 데이터베이스 경로

    Returns:
        List[BaseTool]: 생성된 도구들의 리스트
    """
    tools = [
        news_search_tool(),  # API 키는 환경 변수에서 자동으로 가져갑니다
        retriever_tool(db_path=db_path, name="retrieve_tool"),
        create_python_executor(),
    ]

    return tools


# if __name__ == "__main__":
#     # 테스트용 db_path 설정
#     test_db_path = "path/to/your/vectordb"
#     created_tools = tool_list(test_db_path)
#     print("생성된 도구들:")
#     for tool in created_tools:
#         print(f"- {tool.name}: {tool.description}")
