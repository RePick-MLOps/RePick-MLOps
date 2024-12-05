from executor import agent_executor
from langchain.callbacks.base import BaseCallbackHandler
from typing import Dict, Any


class MaxIterationCallbackHandler(BaseCallbackHandler):
    """최대 반복 횟수를 제한하는 콜백 핸들러"""

    def __init__(self, max_iterations: int = 2):
        self.iteration_count = 0
        self.max_iterations = max_iterations
        super().__init__()

    def on_agent_action(self, action: str, **kwargs: Any) -> None:
        """에이전트가 액션을 수행할 때마다 호출"""
        self.iteration_count += 1
        if self.iteration_count > self.max_iterations:
            raise ValueError(
                f"최대 반복 횟수({self.max_iterations})를 초과했습니다. 현재 정보로 답변을 생성합니다."
            )


def test_chat():
    """에이전트와의 대화를 테스트하는 함수"""
    db_path = r"/Users/jeonghyeran/Desktop/RePick-MLOps/data/vectordb"

    # 최대 2번의 도구 사용만 허용
    callback = MaxIterationCallbackHandler(max_iterations=2)

    try:
        response = agent_executor(db_path=db_path).invoke(
            {
                "input": "롯데쇼핑의 ESG 점수를 전체 평균이 어떻게 되어 있나요?",
                "chat_history": [],
            },
            callbacks=[callback],
        )
        print("\n최종 응답:", response)

    except ValueError as e:
        print("\n경고:", str(e))
        print("현재까지 수집된 정보로 답변을 생성합니다.")


if __name__ == "__main__":
    test_chat()