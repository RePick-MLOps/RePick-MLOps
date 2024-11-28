# 도구 설정 : 명명 규칙 통일 및 기본 설정 개선
def create_news_search():
    # 최근 뉴스 검색을 위한 도구를 생성
    news_search_tool = TavilySearchResults(
        include_domains = ["hankyung.com"],
        search_depth="basic",
        topic="news",
        days=7,
        max_result=10,
        include_answer=True,
        include_raw_content=True,
        include_links=True,
        format_output=True
    )
    news_search_tool.name = "news_search_tool"
    news_search_tool.description = (
        "이 도구는 웹에서 최근 뉴스 기사를 검색합니다. "
        "최신 정보를 보완할 때 사용하세요."
    )
    return news_search_tool

def create_retriever_tools(retriever):
    # 기본 데이터베이스 검색을 위한 도구를 생성
    retrieve_tool = create_retriever_tool(
        retriever,
        name="retrieve_tool",
        description="use this tool to search information from the main document"
    )
    return retrieve_tool

# 프롬프트 템플릿 생성
def create_prompt_template():
    return """
    다음 질문에 최선을 다해 답변하세요. 당신은 사용자의 질문에 답변하기 위해 다음 도구를 사용할 수 있습니다:

    도구: {tools}
    - retrieve_tool: 데이터베이스 검색 도구로, 기본 정보를 찾는 데 필수로 사용합니다.
    - news_search_tool: 최신 뉴스를 검색하는 도구로, ***보완 정보가 필요할 때 사용***합니다.

    항상 다음의 형식을 따릅니다:
    1. ***항상 retrieve_tool을 먼저 사용하여 기본 정보를 검색***합니다.
    2. 기본 정보가 충분하다면 news_search_tool을 사용하여 추가 정보를 검색합니다.
    3. 기본 정보가 충분하지 않다면, user에게 추가 질문을 하여 양질의 답변을 할 수 있게 합니다.
    3. 결과를 바탕으로 명확하고 체계적인 답변을 제공합니다.

    응답 형식:
    - 검색 결과를 요약하고, 출처를 명시하며, 구조화된 답변을 작성합니다.

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

    **이 프름프트는 매번 반복되어 사용자가 여러번의 질문을 하였을 때에도 반복적으로 사용 됩니다.**
    """

# 채팅 기록 관리 클래스: 메모리 최적화 포함
class ChatHistoryManager:
    def __init__(self):
        self.store = {}

    # 주어진 세션 ID에 대한 대화 기록을 반환하거나 새로 생성한다.
    def get_session_history(self, session_ids):
        if session_ids not in self.store:
            self.store[session_ids] = ChatMessageHistory()
        return self.store[session_ids]

    # 오래된 기록은 삭제하여 메모리를 최적화 한다.
    def cleanup_old_sessions(self, max_sessions=100):
        if len(self.store) > max_sessions:
            oldest_session = next(iter(self.store))
            del self.store[oldest_session]

    # 에이전트 실행에 대화 기록을 연결한다.
    def create_agent_with_history(self, agent_executor):
        return RunnableWithMessageHistory(
            agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )

# 에이전트 클래스: 입력 유효성 검사 포
class ChatAgent:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.setup_agent()

    # 에이전트 입력 데이터의 유효성을 검사합니다.
    def validate_input(self, input_data):
        required_keys = ["input", "session_id"]
        for key in required_keys:
            if key not in input_data:
                raise ValueError(f"입력 데이터에 '{key}'가 누락되었습니다.")

    # 에이전트 생성: 도구, 프롬프트, 모델을 초기화한다.
    def setup_agent(self):
        # 도구 생성
        news_search_tool = create_news_search_tool()
        retrieve_tool = create_retriever_tools(self.vectorstore.as_retriever())
        self.tools = [news_search_tool, retrieve_tool]

        # 프롬프트 생성
        self.prompt = create_prompt_template()

        # LLM 생성
        self.llm = ChatOpenAI(
            model_name='gpt-4',
            streaming=True,
            temperature=0,
            callbacks=[StreamingStdOutCallbackHandler()]
        )

        # Agent 생성
        react_agent = create_react_agent(self.llm, tools=self.tools, prompt=self.prompt)
        self.agent_executor = AgentExecutor(
            agent=react_agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )

        # 채팅 기록 관리자 설정
        chat_history_manager = ChatHistoryManager()
        self.agent_with_chat_history = chat_history_manager.create_agent_with_history(
            self.agent_executor
        )

    # 에이전트를 호출. 입력 유효성 검사 후 실행.
    def invoke_agent(self, input_data):
        self.validate_input(input_data)
        return self.agent_with_chat_history.invoke(input_data)

# vectorstore는 이미 생성되어 있다고 가정
chat_agent = ChatAgent(vectorstore)

# 에이전트 사용
response = chat_agent.agent_with_chat_history.invoke(
    {"input": "질문 내용", "session_id": "user_123"}
)