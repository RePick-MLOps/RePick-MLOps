import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    )
)

from react_agent.models.llm import llm_model
from react_agent.prompts import get_prompt_template
from react_agent.tools import tool_list
from langchain.agents import create_react_agent

def get_agent(db_path: str):
    """
    ReAct 에이전트를 생성하는 함수
    """
    try:
        # 1. 데이터베이스 경로 확인
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"데이터베이스 경로를 찾을 수 없습니다: {db_path}")
        print(f"데이터베이스 경로 확인 완료: {db_path}")

        # 2. LLM 모델 불러오기
        llm = llm_model()
        print("LLM 호출 완료")

        # 3. 도구 리스트 불러오기
        tools = tool_list(db_path)
        print(f"도구 호출 완료: {[tool.name for tool in tools]}")

        # 4. 프롬프트 템플릿 불러오기
        prompt = get_prompt_template()
        print("프롬프트 템플릿 호출 완료")

        # 5. ReAct 에이전트 생성
        agent = create_react_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )
        print("에이전트 생성 완료")

        return agent

    except Exception as e:
        print(f"\n에이전트 생성 중 오류 발생: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    # 테스트를 위한 데이터베이스 경로 설정
    db_path = r"/Users/jeonghyeran/Desktop/RePick-MLOps/data/vectordb"
    
    try:
        # 1. 에이전트 생성
        print("\n=== 에이전트 생성 시작 ===")
        agent = get_agent(db_path)
        print("=== 에이전트 생성 완료 ===\n")
        
        # 2. 테스트 실행
        test_input = {
            "input": "롯데쇼핑의 ESG 점수를 알려주세요",
            "chat_history": [],
            "intermediate_steps": []
        }
        
        print(f"테스트 질문: {test_input['input']}")
        response = agent.invoke(test_input)
        print(f"\n에이전트 응답: {response}")
        
    except Exception as e:
        print(f"\n테스트 중 오류 발생: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")