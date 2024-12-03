from executor import agent_executor


def test_chat():
    """
    에이전트와의 대화를 테스트하는 함수
    """
    # db_path 추가
    db_path = r"C:\Users\user\Desktop\RePick-MLOps\data\vectordb"

    response = agent_executor(db_path=db_path).invoke(
        {
            "input": "롯데쇼핑의 ESG 점수를 전체 평균과 비교한 그래프가 어떻게 되어 있나요?",
            "chat_history": [],
        }
    )

    print("\n최종 응답:", response)


if __name__ == "__main__":
    test_chat()
