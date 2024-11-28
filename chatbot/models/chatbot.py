from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
from chromadb.config import Settings
import os
from typing import List
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools.retriever import create_retriever_tool
from langchain.prompts import PromptTemplate


load_dotenv()


class DocumentChatbot:
    def __init__(
        self,
        persist_directory: str,
        documents: List[Document] = None,
        model_name: str = "jhgan/ko-sbert-sts",
    ):
        """
        챗봇 초기화

        Args:
            persist_directory (str): 벡터스토어 저장 경로
            model_name (str): HuggingFace 임베딩 모델 이름
        """
        print(f"벡터스토어 디렉토리 확인: {persist_directory}")

        # 임베딩 모델 초기화
        self.embedding = HuggingFaceEmbeddings(model_name=model_name)

        try:
            if documents:
                print("새로운 벡터스토어 생성...")
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding_function=self.embedding,
                    persist_directory=persist_directory,
                )
                print("벡터스토어 생성 완료")
            else:
                print("기존 벡터스토어 로드 시도...")
                self.vectorstore = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embedding,
                )
                print("벡터스토어 로드 완료")

            # 리트리버 및 체인 설정
            self.setup_retrievers()
            self.setup_relevance_checker()
            self.setup_chain()

        except Exception as e:
            raise Exception(f"벡터스토어 초기화 중 오류: {str(e)}")

    def setup_retrievers(self):
        """리트리버 설정"""
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": 4}
        )
        self.tools = self._create_tools()

    def setup_relevance_checker(self):
        """관련성 체커 설정"""
        self.prompt = self._create_prompt()

    def setup_chain(self):
        """체인 설정"""
        self.agent_executor = self._create_agent_executor()

    def _create_new_vectorstore(self, documents, chroma_client):
        print("새로운 벡터스토어 생성...")
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model,
            client=chroma_client,
            collection_name="document_store",
        )
        print("새로운 벡터스토어 생성 성공")
        return vectorstore

    def _initialize_from_documents(self, documents, persist_directory):
        print("벡터스토어 초기화 시작")
        if not documents:
            raise ValueError("documents가 비어있습니다.")

        # documents가 있을 때는 새로운 vector store를 생성
        self.vector_store = ChromaSQLite.from_documents(
            documents=documents,
            embedding=self.embedding_model,
            persist_directory=persist_directory,
        )
        self.vector_store.persist()  # 디스크에 저장
        self.retriever = self.vector_store.as_retriever()
        print("벡터스토어 초기화 완료")

    def _initialize_from_processed_states(self, persist_directory):
        processed_states_path = Path(persist_directory) / "processed_states.json"
        with open(processed_states_path, "r", encoding="utf-8") as f:
            processed_states = json.load(f)

        documents = []
        for pdf_state in processed_states.values():
            # 텍스트 요약 추가
            for page, summary in pdf_state["text_summary"].items():
                documents.append(
                    Document(
                        page_content=summary,
                        metadata={"type": "text_summary", "page": page},
                    )
                )

            # 이미지 요약 추가
            for image_id, summary in pdf_state["image_summary"].items():
                documents.append(
                    Document(
                        page_content=summary,
                        metadata={"type": "image_summary", "id": image_id},
                    )
                )

            # 테이블 요약 추가
            for table_id, summary in pdf_state["table_summary"].items():
                documents.append(
                    Document(
                        page_content=summary,
                        metadata={"type": "table_summary", "id": table_id},
                    )
                )

        self.vector_store = ChromaSQLite.load(persist_directory)
        self.retriever = self.vector_store.as_retriever()

    def _create_tools(self):
        retrieve_tool = create_retriever_tool(
            self.retriever,
            name="retrieve_tool",
            description="Use this tool to search information from the summaries",
        )
        return [retrieve_tool]

    def _create_prompt(self):
        template = """
        다음 질문에 최선을 다해 답변하세요. 당신은 증권사 애널리스트가 만든 리포트를 분석하고 요약하는 챗봇입니다.
        
        사용 가능한 도구:
        {tools}
        retrieve_tool: 요약된 정보를 검색하는 도구

        형식:
        Question: 당신이 답해야 할 입력 질문
        Thought: 무엇을 해야 할지 생각하세요
        Action: 취해야 할 행동을 선택하세요. [{tool_names}] 중 하나여야 합니다.
        Action Input: 행동에 대한 입력을 작성하세요.
        Observation: 행동의 결과를 작성하세요
        Thought: 필요한 데이터를 충분히 수집했거나, 더 이상 유효한 결과를 찾을 수 없음을 판단합니다.
        Final Answer: 원래 질문에 대한 최종 답변을 markdown 형식으로 작성하세요.

        규칙:
        1. 답변은 최대 1000자로 요약하세요.
        2. markdown 형식으로 답변하세요.
        3. 최대한 자세하게 답변하세요.
        4. 검색 결과에 없는 내용이라면 답변할 수 없다고 하세요.

        Begin!

        Question: {input}
        {agent_scratchpad}
        """
        return PromptTemplate.from_template(template)

        prompt = PromptTemplate(
            template=template,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={
                "tools": self._get_tool_descriptions(),
                "tool_names": self._get_tool_names(),
            },
        )
        return prompt

    def _get_tool_descriptions(self):
        return "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])

    def _get_tool_names(self):
        return ", ".join([tool.name for tool in self.tools])

    def _create_agent_executor(self):
        llm = ChatOpenAI(
            model_name="gpt-4",
            streaming=True,
            temperature=0,
            callbacks=[StreamingStdOutCallbackHandler()],
        )
        react_agent = create_react_agent(llm, tools=self.tools, prompt=self.prompt)
        return AgentExecutor(
            agent=react_agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )

    def chat(self, query: str) -> str:
        try:
            # agent_executor를 사용하여 질문 처리
            response = self.agent_executor.invoke({"input": query})
            return response["output"]
        except Exception as e:
            raise Exception(f"채팅 처리 중 오류 발생: {str(e)}")
