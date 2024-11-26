import os
import nest_asyncio
from google.colab import drive
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import PromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import json

from dotenv import load_dotenv
load_dotenv()


# def install_dependencies():
#     !pip install llama-index-core llama-parse llama-index-readers-file
#     !pip install langchain_community
#     !pip install langchain_openai faiss-cpu

def create_parser(file_path):
    parsing_instruction = (
        "문서에서 표와 그래프, 관련 텍스트를 분석하여 정보를 추출하세요. "
        "표는 반드시 마크다운 형식으로 작성하고, 제목과 데이터 출처를 포함해야 합니다. "
        "텍스트와 표는 한국어로 반환하세요. "
        "그래프가 포함된 경우, '그래프 설명:'이라는 키워드로 시작하는 간단한 설명을 작성하세요. "
        "모든 정보는 명확하고 일관된 형식으로 반환하세요."
    )
    parser = LlamaParse(
        use_vendor_multimodal_model=True,
        vendor_multimodal_model_name="openai-gpt4o",
        vendor_multimodal_api_key=os.environ["OPENAI_API_KEY"],
        result_type="markdown",
        language="ko",
        parsing_instruction=parsing_instruction,
    )
    return parser.load_data(file_path=file_path)

def create_vectorstore(docs):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents=docs, embedding=embeddings)
    return vectorstore

def create_tools(vectorstore):
    retriever = vectorstore.as_retriever()
    vectorstore_search_tool = create_retriever_tool(
        retriever=retriever,
        name="industry_search",
        description="Search for insights on trends, technologies, market dynamics, and key players across various industries and economic sectors."
    )
    news_search = TavilySearchResults(
        search_depth="basic",
        topic="news",
        days=7,
        max_result=10,
        include_answer=True,
        include_raw_content=True,
        include_links=True,
        format_output=True
    )
    news_search.name = "news_search"
    news_search.description = (
        "Use this tool to search for news articles on the web. "
        "It is optimized for retrieving recent news topics."
    )
    retrieve_tool = create_retriever_tool(
        retriever,
        name="retrieve_tool",
        description="use this tool to search information from the PDF document"
    )
    return [news_search, retrieve_tool]

def create_prompt():
    template = """
    다음 질문에 최선을 다해 답변하세요. 당신이 사용할 수 있는 도구는 다음과 같습니다.:

    {tools}
    news_search: 인터넷에서 관련 뉴스를 검색하는 도구,
    retrieve_tool: 무조건 답변의 배경이 되어야 하는 DB에서 정보를 검색하는 도구,

    다음 형식을 따릅니다:

    ***retrieve_tool을 먼저 사용하여 사용자에게 답변할 내용을 먼저 검색 후,***
    사용자 질문에 대한 키워드를 추출한 뒤 해당 키워드로 자료를 보강하기 위해 news_search 도구를 활용하여 관련 뉴스를 출처와 함께 나열하세요.
    질문이 너무 추상적이거나 관련 데이터를 찾을 수 없을 경우, ***retrieve_tool의 결과만으로 답변하세요.***

    #### 답변 생성 규칙

    Question: 당신이 답해야 할 입력 질문
    Thought: 무엇을 해야 할지 생각하세요
      - 질문이 추상적인지 평가합니다.
      - news_search 도구는 풍부한 답변을 위한 도구이지 답변의 필수적인 요소는 아닙니다.
    Action: 취해야 할 행동을 선택하세요. [{tool_names}] 중 하나여야 합니다.
    Action Input: 행동에 대한 입력을 작성하세요.
    Observation: 행동의 결과를 작성하세요
    ...(이 생각/행동/행동 입력/관찰 단계는 여러 번 반복될 수 있습니다)
    Thought: 필요한 데이터를 충분히 수집했거나, 더 이상 유효한 결과를 찾을 수 없음을 판단합니다.
    Final Answer: 원래 질문에 대한 최종 답변을 작성하세요.

    Begin!

    placeholder: "{chat_history | []}"  # 기본값을 빈 리스트로 설정
    Question: "{input}"
    Thought: "{agent_scratchpad}"
    """
    return PromptTemplate.from_template(template)

def create_agent_executor(tools, prompt):
    llm = ChatOpenAI(
        model_name='gpt-4o',
        streaming=True,
        temperature=0,
        callbacks=[StreamingStdOutCallbackHandler()]
    )
    react_agent = create_react_agent(llm, tools=tools, prompt=prompt)
    return AgentExecutor(
        agent=react_agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )

def chat(react_agent_executor):
    print("챗봇 대화를 시작합니다. 'exit'을 입력하면 종료됩니다.")
    while True:
        user_input = input("질문을 입력하세요: ")
        if user_input.lower() == "exit":
            print("챗봇을 종료합니다.")
            break
        try:
            result = react_agent_executor.invoke({"input": user_input})
            if "output" in result:
                print("\n챗봇 응답:", result["output"])
            else:
                print("\n챗봇 응답: 예상치 못한 결과:", result)
        except Exception as e:
            print(f"오류 발생: {e}")

def main():
    setup_environment()
    initialize_drive()
    install_dependencies()
    file_path = "/content/drive/MyDrive/한국경제_TossBank/final_project/data/산업/20241112_industry_584909000.pdf"
    parsed_docs = create_parser(file_path)
    docs = [doc.to_langchain_format() for doc in parsed_docs]
    vectorstore = create_vectorstore(docs)
    tools = create_tools(vectorstore)
    prompt = create_prompt()
    react_agent_executor = create_agent_executor(tools, prompt)
    chat(react_agent_executor)

if __name__ == "__main__":
    main()