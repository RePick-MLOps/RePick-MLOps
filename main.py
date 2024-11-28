# 필요한 도구들 import
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import (
    StreamingStdOutCallbackHandler,
)  # AI의 응답을 실시간으로 보여주는 도구
from langchain.agents import create_react_agent, AgentExecutor

from tools import initialize_tools  # 도구 초기화 함수 추가
from agents import ChatHistoryManager  # 채팅 기록 관리자 추가
from prompts import initialize_prompts  # 프롬프트 초기화 함수 추가

import logging

# logger 설정
logger = logging.getLogger(__name__)


class ChatAgent:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.setup_agent()

    # 사용자의 입력에 필수 필드가 존재하는지 검증
    def validate_input(self, input_data):
        required_keys = [
            "input",
            "session_id",
        ]  # 사용자의 실제 질문, 대화 세션을 구분하는 고유 식별자
        for key in required_keys:
            if key not in input_data:
                raise ValueError(f"입력 데이터에 '{key}'가 누락되었습니다.")

    def setup_agent(self):
        # 도구 초기화
        self.tools = initialize_tools(self.vectorstore)

        # 프롬프트 초기화
        self.prompt = initialize_prompts()

        # 프롬프트 및 LLM 설정
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
            return self.agent_with_chat_history.invoke(input_data)
        except ValueError as ve:
            logger.error(f"입력 값 검증 실패: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"에이전트 실행 중 오류 발생: {str(e)}")
            raise ChatAgentError(f"챗봇 실행 중 오류가 발생했습니다: {str(e)}")


class ChatAgentError(Exception):
    """챗봇 에이전트 관련 커스텀 예외"""

    pass


# 사용 예시
if __name__ == "__main__":
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma

    # 허깅페이스 임베딩 모델 초기화
    # 사용자의 질문과 문서를 같은 벡터 공간으로 변환하여 유사도 검색을 가능하게 함
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # 다국어 지원 모델 예시
        # model_kwargs={'device': 'cuda'}  # GPU 사용 시
    )

    # Chroma vectorstore 불러오기
    vectorstore = Chroma(
        persist_directory="path/to/your/chroma_db", embedding_function=embedding_model
    )

    # ChatAgent 생성 및 실행
    chat_agent = ChatAgent(vectorstore)
    response = chat_agent.invoke_agent(
        {"input": "안녕하세요, 당신은 누구인가요?", "session_id": "test_session"}
    )
