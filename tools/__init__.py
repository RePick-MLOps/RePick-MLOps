from .retriever_tool import create_retriever_tools
from .news_search import create_news_search


def initialize_tools(vectorstore):
    retriever = vectorstore.as_retriever(
        search_type="similarity", search_kwargs={"k": 3}
    )
    tools = [create_retriever_tools(retriever), create_news_search()]
    return tools
