from typing import Any, Dict, List
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseChatMessageHistory


class ChatHistoryManager:
    def __init__(self):
        self.message_history = ChatMessageHistory()
        self.memory = ConversationBufferMemory(
            chat_memory=self.message_history,
            return_messages=True,
            memory_key="chat_history",
            output_key="output",
        )

    def create_agent_with_history(self, agent_executor: Any) -> Any:
        """
        채팅 기록을 포함하여 에이전트를 생성합니다.
        """
        agent_executor.memory = self.memory
        return agent_executor

    def add_message(self, message: str) -> None:
        """
        채팅 기록에 메시지를 추가합니다.
        """
        self.message_history.add_user_message(message)

    def get_history(self) -> List[Dict[str, str]]:
        """
        현재 채팅 기록을 반환합니다.
        """
        return self.message_history.messages

    def clear_history(self) -> None:
        """
        채팅 기록을 초기화합니다.
        """
        self.message_history.clear()
