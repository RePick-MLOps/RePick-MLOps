# 필요한 도구들 import
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler # AI의 응답을 실시간으로 보여주는 도구
from langchain.agents import create_react_agent, AgentExecutor

from tools.news_search import create_news_search
from tools.retriever_tool import create_retriever_tools
from prompts.template import create_prompt_template
from agents.history import ChatHistoryManager

class ChatAgent:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.setup_agent()

    def validate_input(self, input_data):
        required_keys = ["input", "session_id"]
        for key in required_keys:
            if key not in input_data:
                raise ValueError(f"입력 데이터에 '{key}'가 누락되었습니다.")

    def setup_agent(self):
        # 도구 생성
        news_search_tool = create_news_search()
        retrieve_tool = create_retriever_tools(self.vectorstore.as_retriever())
        self.tools = [news_search_tool, retrieve_tool]

        # 프롬프트 및 LLM 설정
        self.prompt = create_prompt_template()
        self.llm = ChatOpenAI(
            model_name='gpt-4',
            streaming=True,
            temperature=0,
            callbacks=[StreamingStdOutCallbackHandler()]
        )

        # Agent 생성
        react_agent = create_react_agent(self.llm, self.tools, self.prompt)
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

    def invoke_agent(self, input_data):
        self.validate_input(input_data)
        return self.agent_with_chat_history.invoke(input_data)

# 사용 예시
if __name__ == "__main__":
    # Chatbot 인스턴스 생성 (vectorstore 포함)
    chatbot = Chatbot()
    
    # ChatAgent 생성 (chatbot의 vector_store 사용)
    chat_agent = ChatAgent(chatbot.vector_store)
    
    # 에이전트 실행
    response = chat_agent.invoke_agent({
        "input": "지금 시장에 대해서 짧게 설명해줘",
        "session_id": "user_123"
    }) 