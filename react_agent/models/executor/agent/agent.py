import os
import sys
import subprocess
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    )
)

from react_agent.models.llm import llm_model
from react_agent.tools import tool_list
from langchain.agents import create_react_agent
from langchain_openai import ChatOpenAI
from react_agent.prompts.template import prompt_template


def react_agent(db_path: str):
    """
    ReAct 에이전트를 생성하는 함수
    """
    try:
        # LLM 모델 초기화
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, streaming=True)
        logger.info("LLM 모델 초기화 완료")

        # 도구 목록 가져오기
        tools = tool_list(db_path)
        tool_names = [tool.name for tool in tools]
        logger.info(f"도구 목록 로드 완료: {tool_names}")

        # 프롬프트 템플릿 생성
        prompt = prompt_template()
        logger.info("프롬프트 템플릿 생성 완료")

        # ReAct 에이전트 생성
        agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
        logger.info("에이전트 생성 완료")

        return agent

    except Exception as e:
        logger.error(f"에이전트 생성 중 오류 발생: {str(e)}")
        raise
