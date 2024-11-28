from langchain.tools import Tool


def create_retriever_tools(retriever):
    """retriever를 이용한 검색 도구 생성"""
    return Tool(
        name="retrieve_tool",
        description="use this tool to search information from the main document",
        func=retriever.get_relevant_documents,
    )
