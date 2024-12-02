from langchain.agents import AgentExecutor, create_react_agent
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from react_agent.tools.tools import tool_list
from react_agent.prompts.template import prompt_template

def create_llm():
    """스트리밍 지원 GPT-4 언어 모델 생성"""
    return ChatOpenAI(
        model_name='gpt-4',
        streaming=True,
        temperature=0,
        callbacks=[StreamingStdOutCallbackHandler()]
    )

def create_agent(llm=None, tools=tool_list, prompt=prompt_template) -> AgentExecutor:
    """한국어 ReAct 에이전트 생성"""
    if llm is None:
        llm = create_llm()
        
    agent = create_react_agent(llm, tools, prompt)
    react_agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    return react_agent_executor

agent = create_agent()

# 에이전트와 대화
response = agent.invoke("중국 시장에 대해서 분석해줘")