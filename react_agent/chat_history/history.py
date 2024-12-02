from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI


# 키의 이름은 일관성 있게 관리하는 것이 중요하며, 프롬프트 템플릿이나 다른 컴포넌트에서도 동일한 키 이름을 참조해야 한다.
class ChatHistoryManager:
    def __init__(self):
        llm = ChatOpenAI()
        self.memory = ConversationSummaryBufferMemory(
            llm=llm,
            max_token_limit=300,
            return_messages=True,
            memory_key="chat_history", # 대화 기록이 저장될 때 사용되는 키(key)의 이름
            output_key="output"        # 에이전트의 응답이 저장될 때 사용되는 키의 이름
        )

    def create_agent_with_history(self, agent_executor):
        """
        채팅 기록을 포함하여 에이전트를 생성합니다.
        """
        agent_executor.memory = self.memory
        return agent_executor

    def clear_history(self):
        """
        채팅 기록을 초기화합니다.
        """
        self.memory.clear()
