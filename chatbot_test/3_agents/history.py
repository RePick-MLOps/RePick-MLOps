from langchain.memory import ChatMessageHistory
from langchain.agents import RunnableWithMessageHistory

class ChatHistoryManager:
    def __init__(self):
        self.store = {}

    def get_session_history(self, session_ids):
        if session_ids not in self.store:
            self.store[session_ids] = ChatMessageHistory()
        return self.store[session_ids]

    def cleanup_old_sessions(self, max_sessions=100):
        if len(self.store) > max_sessions:
            oldest_session = next(iter(self.store))
            del self.store[oldest_session]

    def create_agent_with_history(self, agent_executor):
        return RunnableWithMessageHistory(
            agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )