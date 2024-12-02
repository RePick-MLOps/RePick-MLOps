from langchain.tools import Tool
from react_agent.tools.retriever_tool.retriever_main.retriever_main import create_retriever

def retriever_tool(db_path: str, name: str = "industry_search"):
    """문서 검색 도구 생성"""
    retriever = create_retriever(db_path=db_path)
    return Tool(
        name=name,
        description="문서 검색을 위한 도구입니다.",
        func=retriever.search
    )

if __name__ == "__main__":
    tool = retriever_tool(
        db_path=r"C:\Users\user\Desktop\RePick-MLOps\data\vectordb"
    )
    results = tool.run("중국 자동차시장")
    print(results)