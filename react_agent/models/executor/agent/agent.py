import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    )
)

from react_agent.models.llm import llm_model
from react_agent.prompts import prompt_template
from react_agent.tools import tool_list
from langchain.agents import create_react_agent


def react_agent(db_path: str):
    """
    ReAct 에이전트를 생성하는 함수
    """
    llm = llm_model()
    tools = tool_list(db_path)
    tool_names = [tool.name for tool in tools]
    chat_history = ""  # 초기 대화 기록 설정
    agent_scratchpad = ""  # 초기 에이전트 스크래치패드 설정
    input_text = ""  # 초기 입력 설정

    # tools를 문자열로 변환
    tools_str = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])

    prompt = prompt_template().format(
        tools=tools_str,
        tool_names=", ".join(tool_names),  # tool_names를 문자열로 변환
        chat_history=chat_history,
        agent_scratchpad=agent_scratchpad,
        input=input_text
    )

    # create_react_agent 함수를 사용하여 에이전트 생성
    return create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )