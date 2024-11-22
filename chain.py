from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import PromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler # 스트리밍 방식으로 데이터를 처리하는데 사용됨
from langchain.agents import AgentExecutor, create_react_agent # 에이전트를 실행하는 핵심 클래스, ReAct기반 에이전트를 생성하는 함수

# 검색기 생성 ( Retriever )
retriever = vectorstore.as_retriever()

# 툴 생성
vectorstore_search_tool = create_retriever_tool(
    retriever=retriever,
    name="industry_search", # 도구 이름 정의
    description="Search for insights on trends, technologies, market dynamics, and key players across various industries and economic sectors.."
)

search = TavilySearchResults(
    include_domains = ["hankyung.com"],
    search_depth = "basic",
    days = 7,
    max_result = 10,
    include_answer = True,
    include_raw_content = True,
    include_links = True,
    format_output = True
    )

tools = [ search, retrieve_toorl ]

# 프롬프트 생성 ( Creat Prompt )
template ="""
다음 질문에 최선을 다해 답변하세요. 당신이 사용할 수 있는 도구는 다음과 같습니다.:

{tools}
search: 인터넷에서 검색하는 도구,
retrieve_toorl: This PDF provides information about trends in the ICT industry,

다음 형식을 따릅니다:

***retrieve_toorl을 먼저 사용하여 사용자에게 답변할 내용을 먼저 검색 후,*** 사용자 질문에 대한 키워드를 추출한 뒤 해당 키워드로 자료를 보강하기 위해 search 도구를 활용하여 관련 뉴스를 출처와 함께 나열하세요.

Question: 당신이 답해야 할 입력 질문
Thought: 무엇을 해야 할지 생각하세요
Action: 취해야 할 행동을 선택하세요. [{tool_names}] 중 하나여야 합니다.
Action Input: 행동에 대한 입력을 작성하세요.
Observation: 행동의 결과를 작성하세요
...(이 생각/행동/행동 입력/관찰 단계는 여러 번 반복될 수 있습니다)
Thought: 이제 최종 답변을 알겠습니다.
Final Answer: 원래 질문에 대한 최종 답변을 작성하세요.

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""

prompt = PromptTemplate.from_template(template) # Text Template 생성
prompt

# 언어모델 ( LLM ) 생성

llm = ChatOpenAI(
    model_name='gpt-4o',
    streaming=True, # 스트리밍 응답 활성화
    temperature=0, # 데이터 분석이 중요하기 때문에 랜덤성 0 부여
    callbacks=[StreamingStdOutCallbackHandler()] # 생성된 응답을 실시간으로 콘솔에 출력
)

# Create ReAct agent / AgentExecutor
react_agent = create_react_agent(llm, tools=tools, prompt=prompt) # 한국어 프롬프트 지정

react_agent_executor = AgentExecutor(
    agent=react_agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

react_agent_executor.invoke({"input": "중국 잦동차 시장의 현황에 대해서 설명해줘"})

def chat():
    print("챗봇 대화를 시작합니다. 'exit'을 입력하면 종료됩니다.")

    while True:
        # 사용자 입력 받기
        user_input = input("질문을 입력하세요: ")
        if user_input.lower() == "exit":
            print("챗봇을 종료합니다.")
            break

        # QA 체인 실행
        try:
            # 사용자 입력 전달
            result = react_agent_executor.invoke({"input": user_input})

            # 원하는 출력 키 사용
            if "output" in result:
                print("\n챗봇 응답:", result["output"])
            else:
                print("\n챗봇 응답: 예상치 못한 결과:", result)

        except Exception as e:
            print(f"오류 발생: {e}")

# 실행
chat()