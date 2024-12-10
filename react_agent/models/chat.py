from react_agent.models.executor.executor import agent_executor

def test_chat():
    """에이전트와의 대화를 테스트하는 함수"""
    db_path = r"/Users/jeonghyeran/Desktop/RePick-MLOps/data/vectordb"

    try:
        # 에이전트 실행기 생성
        executor = agent_executor(db_path=db_path)
        
        # 테스트 질문
        test_input = {
            "input": "삼성전자 전망에 대해서 설명해줘?",
            "chat_history": [],
        }
        
        # 에이전트에게 질문을 보내고 응답 받기
        response = executor.invoke(test_input)
        
        # 최종 응답 출력
        print("\n최종 응답:", response)
    except Exception as e:
        print("오류 발생:", e)

if __name__ == "__main__":
    test_chat()