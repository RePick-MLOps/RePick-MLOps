from langchain.memory import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory


class ChatHistoryManager:
    def __init__(self):
        self.store = {}

    def get_session_history(self, session_id):
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def create_agent_with_history(self, agent_executor):
        return RunnableWithMessageHistory(
            agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="output",
        )
