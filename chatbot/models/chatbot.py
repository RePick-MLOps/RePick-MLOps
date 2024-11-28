# 필요한 도구들 import
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.agents import create_react_agent, AgentExecutor
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from tools import initialize_tools
from agents import ChatHistoryManager
from prompts import initialize_prompts

import logging

# logger 설정
logger = logging.getLogger(__name__)


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
        # 도구 초기화
        self.tools = initialize_tools(self.vectorstore)

        # 프롬프트 초기화
        self.prompt = initialize_prompts()

        # LLM 설정
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            streaming=True,
            temperature=0,
            callbacks=[StreamingStdOutCallbackHandler()],
        )

        # Agent 생성
        react_agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=react_agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )

        # 채팅 기록 관리자 설정
        chat_history_manager = ChatHistoryManager()
        self.agent_with_chat_history = chat_history_manager.create_agent_with_history(
            self.agent_executor
        )

    def invoke_agent(self, input_data):
        try:
            self.validate_input(input_data)
            return self.agent_with_chat_history.invoke(
                {"input": input_data["input"]},
                {"configurable": {"session_id": input_data["session_id"]}},
            )
        except ValueError as ve:
            logger.error(f"입력 값 검증 실패: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"에이전트 실행 중 오류 발생: {str(e)}")
            raise ChatAgentError(f"챗봇 실행 중 오류가 발생했습니다: {str(e)}")


class ChatAgentError(Exception):
    pass


if __name__ == "__main__":
    # 허깅페이스 임베딩 모델 초기화
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )

    # Chroma vectorstore 불러오기
    vectorstore = Chroma(
        persist_directory="/Users/naeun/working/RePick-MLOps/data/vectordb",
        embedding_function=embedding_model,
    )

    # ChatAgent 생성 및 실행
    chat_agent = ChatAgent(vectorstore)
    response = chat_agent.invoke_agent(
        {"input": "안녕하세요, 당신은 누구인가요?", "session_id": "test_session"}
    )
