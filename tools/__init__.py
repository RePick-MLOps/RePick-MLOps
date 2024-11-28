from .retriever_tool import create_retriever_tools
from .news_search import create_news_search
from .python_executor import create_python_executor


def initialize_tools(vectorstore):
    retriever = vectorstore.as_retriever(
        search_type="similarity", search_kwargs={"k": 3}
    )
    tools = [
        create_retriever_tools(retriever),
        create_news_search(),
        create_python_executor()
    ]
    return tools
