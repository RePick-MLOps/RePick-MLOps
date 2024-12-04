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
    prompt = prompt_template()

    # create_react_agent 함수를 사용하여 에이전트 생성
    return create_react_agent(llm=llm, tools=tools, prompt=prompt)
