import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools.retriever import create_retriever_tool
from chromasqlite3 import ChromaSQLite

def load_summaries(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [item['summary'] for item in data]

def load_existing_vectorstore():
    # 이미 생성된 ChromaDB 인스턴스를 로드합니다.
    vectorstore = ChromaSQLite.load("/data/vectordb/chroma.sqlite3")
    return vectorstore

def create_tools(vectorstore):
    retriever = vectorstore.as_retriever()
    retrieve_tool = create_retriever_tool(
        retriever,
        name="retrieve_tool",
        description="Use this tool to search information from the summaries"
    )
    return [retrieve_tool]

def create_prompt():
    template = """
    다음 질문에 최선을 다해 답변하세요. 당신이 사용할 수 있는 도구는 다음과 같습니다.:

    {tools}
    retrieve_tool: 요약된 정보를 검색하는 도구,

    다음 형식을 따릅니다:

    ***retrieve_tool을 사용하여 사용자에게 답변할 내용을 검색하세요.***

    #### 답변 생성 규칙

    Question: 당신이 답해야 할 입력 질문
    Thought: 무엇을 해야 할지 생각하세요
    Action: 취해야 할 행동을 선택하세요. [{tool_names}] 중 하나여야 합니다.
    Action Input: 행동에 대한 입력을 작성하세요.
    Observation: 행동의 결과를 작성하세요
    Thought: 필요한 데이터를 충분히 수집했거나, 더 이상 유효한 결과를 찾을 수 없음을 판단합니다.
    Final Answer: 원래 질문에 대한 최종 답변을 작성하세요.

    Begin!

    placeholder: "{chat_history | []}"  # 기본값을 빈 리스트로 설정
    Question: "{input}"
    Thought: "{agent_scratchpad}"
    """
    return PromptTemplate.from_template(template)

def create_agent_executor(tools, prompt):
    llm = ChatOpenAI(
        model_name='gpt-4o',
        streaming=True,
        temperature=0,
        callbacks=[StreamingStdOutCallbackHandler()]
    )
    react_agent = create_react_agent(llm, tools=tools, prompt=prompt)
    return AgentExecutor(
        agent=react_agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )

def chat(react_agent_executor):
    print("챗봇 대화를 시작합니다. 'exit'을 입력하면 종료됩니다.")
    while True:
        user_input = input("질문을 입력하세요: ")
        if user_input.lower() == "exit":
            print("챗봇을 종료합니다.")
            break
        try:
            result = react_agent_executor.invoke({"input": user_input})
            if "output" in result:
                print("\n챗봇 응답:", result["output"])
            else:
                print("\n챗봇 응답: 예상치 못한 결과:", result)
        except Exception as e:
            print(f"오류 발생: {e}")

def main():
    json_path = "/data/vectordb/processed_states.json"
    summaries = load_summaries(json_path)
    vectorstore = load_existing_vectorstore()
    tools = create_tools(vectorstore)
    prompt = create_prompt()
    react_agent_executor = create_agent_executor(tools, prompt)
    chat(react_agent_executor)

if __name__ == "__main__":
    main()