import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
)

from langchain.agents import AgentExecutor
from react_agent.models.executor.agent import get_agent
from react_agent.tools import tool_list  # 도구 목록 직접 가져오기

def agent_executor(db_path: str) -> AgentExecutor:
    """
    AgentExecutor를 생성하는 함수

    Args:
        db_path (str): 벡터 데이터베이스 경로

    Returns:
        AgentExecutor: 생성된 에이전트 실행기
    """
    try:
        # 에이전트 생성
        agent = get_agent(db_path)
        
        # 도구 목록 직접 가져오기
        tools = tool_list(db_path)
        
        # AgentExecutor 생성
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
        
        return agent_executor
        
    except Exception as e:
        print(f"\nAgentExecutor 생성 중 오류 발생: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    # 테스트를 위한 데이터베이스 경로 설정
    db_path = r"/Users/jeonghyeran/Desktop/RePick-MLOps/data/vectordb"
    
    try:
        # 1. AgentExecutor 생성
        print("\n=== AgentExecutor 생성 시작 ===")
        executor = agent_executor(db_path)
        print("=== AgentExecutor 생성 완료 ===\n")
        
        # 2. 테스트 실행
        test_input = {
            "input": "엘앤에프의 1개월 수익률이 긍정적인 이유는 무엇인가요?",
            "chat_history": []
        }
        
        print(f"테스트 질문: {test_input['input']}")
        response = executor.invoke(test_input)
        print(f"\n최종 답변: {response['output']}")
        
    except Exception as e:
        print(f"\n테스트 중 오류 발생: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")