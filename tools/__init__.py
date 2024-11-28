# 필요한 도구들 import
from .news_search import create_news_search
from .retriever_tool import create_retriever_tools


def initialize_tools(vectorstore):
    news_search_tool = create_news_search()
    retrieve_tool = create_retriever_tools(vectorstore.as_retriever())
    return [news_search_tool, retrieve_tool]
