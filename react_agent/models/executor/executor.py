# AgentExecutor는 LangChain에서 Agent의 실행을 관리하는 핵심 컴포넌트 이다.

from langchain.agents import AgentExecutor
from .agent import react_agent


def agent_executor(db_path: str):
    """
    AgentExecutor를 생성하는 함수
    """
    agent = react_agent(db_path=db_path)

    return AgentExecutor.from_agent_and_tools(
        agent=agent, verbose=True, handle_parsing_errors=True
    )
