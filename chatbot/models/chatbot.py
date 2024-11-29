from langchain.callbacks.manager import CallbackManager
from langchain.callbacks import StreamingStdOutCallbackHandler, LangChainTracer
from langchain.callbacks.tracers import ConsoleCallbackHandler


# 필요한 도구들 import
from langchain_openai import ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.agents import create_react_agent, AgentExecutor
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from tools import initialize_tools
from agents import chat_manager  # 전역 인스턴스 사용
from prompts import initialize_prompts
from langchain.callbacks import LangChainTracer

import logging
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# logger 설정 / 디버깅, 경고, 에러를 기록하며 디버깅을 편하게 해준다.
logger = logging.getLogger(__name__)


class ChatAgent:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.chat_history = chat_manager

        # 벡터 검색 설정
        self.search_kwargs = {
            "k": 5,  # 검색할 문서 수
            "score_threshold": 0.7,  # 유사도 점수 임계값
        }

        # tools와 prompt 초기화
        self.tools = initialize_tools(self.vectorstore)
        self.prompt = initialize_prompts()

        self.setup_callbacks()
        self.setup_agent()

        # 프로젝트 이름을 환경 변수에서 가져옴
        self.project_name = os.getenv("LANGCHAIN_PROJECT", "default_project")

        # LangSmith 트레이서 설정
        self.tracer = LangChainTracer(project_name=self.project_name)
        self.setup_agent()

    def validate_input(self, input_data):
        if "input" not in input_data:
            raise ValueError(f"입력 데이터에 'input'이 누락되었습니다.")

    def setup_callbacks(self):
        """콜백 설정"""
        callbacks = []
        callbacks.append(StreamingStdOutCallbackHandler())

        if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true":
            project_name = os.getenv("LANGCHAIN_PROJECT", "default")
            self.tracer = LangChainTracer(project_name=project_name)
            callbacks.append(self.tracer)

        callbacks.append(ConsoleCallbackHandler())
        self.callback_manager = CallbackManager(handlers=callbacks)

    def setup_agent(self):
        # LLM 설정
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            streaming=True,
            temperature=0.7,
            callback_manager=self.callback_manager,
        )

        # Agent 생성
        react_agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=react_agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )

        # RunnableWithMessageHistory로 agent_executor 래핑
        self.agent_executor = self.chat_history.create_agent_with_history(
            self.agent_executor
        )

        # RunnableWithMessageHistory로 agent_executor 래핑
        self.agent_executor = self.chat_history.create_agent_with_history(
            self.agent_executor
        )

    def invoke_agent(self, input_data):
        try:
            self.validate_input(input_data)

            # 직접 agent_executor를 통해 처리 (tools 사용)
            response = self.agent_executor.invoke(input_data)
            return response.get("output", "답변을 생성하지 못했습니다.")

        except Exception as e:
            logger.error(f"에이전트 실행 중 오류 발생: {str(e)}")
            raise ChatAgentError(f"챗봇 실행 중 오류가 발생했습니다: {str(e)}")


class ChatAgentError(Exception):
    pass


if __name__ == "__main__":
    # 허깅페이스 임베딩 모델 초기화
    embedding_model = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sbert-sts",
    )

    # Chroma vectorstore 불러오기
    vectorstore = Chroma(
        persist_directory="/Users/naeun/working/RePick-MLOps/data/vectordb",
        embedding_function=embedding_model,
    )

    # ChatAgent 생성 및 실행
    chat_agent = ChatAgent(vectorstore)
    response = chat_agent.invoke_agent({"input": "안녕하세요, 당신은 누구인가요?"})
