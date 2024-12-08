from typing import List, Dict, Any
from langchain.memory import ConversationBufferMemory


class ChatHistoryManager:
    def __init__(self):
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

    def create_agent_with_history(self, agent):
        """에이전트에 채팅 기록을 추가합니다."""
        return agent.with_memory(self.memory)

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """현재 채팅 기록을 반환합니다."""
        return self.memory.chat_memory.messages

    def clear_history(self):
        """채팅 기록을 초기화합니다."""
        self.memory.clear()
