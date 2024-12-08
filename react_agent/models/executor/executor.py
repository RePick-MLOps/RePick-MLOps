# AgentExecutor는 LangChain에서 Agent의 실행을 관리하는 핵심 컴포넌트 이다.

from langchain.agents import AgentExecutor
from .agent import react_agent
from react_agent.tools import tool_list


def agent_executor(db_path: str):
    """
    AgentExecutor를 생성하는 함수
    """
    agent = react_agent(db_path=db_path)
    tools = tool_list(db_path)

    return AgentExecutor(
        agent=agent, tools=tools, verbose=True, handle_parsing_errors=True
    )