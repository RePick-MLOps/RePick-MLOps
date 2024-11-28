from langchain.tools import create_retriever_tool


def create_retriever_tools(retriever):
    retrieve_tool = create_retriever_tool(
        retriever,
        name="retrieve_tool",
        description="use this tool to search information from the main document",
    )
    return retrieve_tool
