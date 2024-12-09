from models.executor.executor import agent_executor
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
