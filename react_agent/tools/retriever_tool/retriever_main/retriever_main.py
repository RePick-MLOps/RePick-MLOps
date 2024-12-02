from react_agent.tools.retriever_tool.retriever.retriever import DocumentRetriever

def create_retriever(db_path: str, k: int = 3):
    """리트리버 생성 함수"""
    return DocumentRetriever(db_path=db_path, k=k)