from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
from chromadb.config import Settings
import os


load_dotenv()


class DocumentChatbot:
    def __init__(self, persist_directory, documents=None, model_name="jhgan/ko-sbert-nli"):
    try:
        print(f"벡터스토어 디렉토리 확인: {persist_directory}")
        persist_directory = os.path.abspath(persist_directory)
        
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        
        # 새로운 ChromaDB 클라이언트 설정
        chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                is_persistent=True
            )
        )
        
        if documents is not None:
            print("새로운 벡터스토어 생성...")
            self.vectorstore = self._create_new_vectorstore(documents, chroma_client)
        else:
            try:
                print("기존 벡터스토어 로드 시도...")
                self.vectorstore = Chroma(
                    client=chroma_client,
                    embedding_function=self.embedding_model,
                    collection_name="document_store"
                )
                collection_count = self.vectorstore._collection.count()
                print(f"벡터스토어 항목 수: {collection_count}")
                if collection_count == 0:
                    raise ValueError("벡터스토어가 비어있습니다.")
            except Exception as e:
                print(f"기존 벡터스토어 로드 실패: {str(e)}")
                raise ValueError("벡터스토어 로드 실패 및 documents가 제공되지 않았습니다.")
                
    except Exception as e:
        raise Exception(f"벡터스토어 초기화 중 오류: {str(e)}")

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

        placeholder: "{chat_history | []}"
        Question: "{input}"
        Thought: "{agent_scratchpad}"
        """
        return PromptTemplate.from_template(template)

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
            docs = self.vectorstore.similarity_search(query)
            if not docs:
                return "관련된 정보를 찾을 수 없습니다."
            response = "\n".join([doc.page_content for doc in docs])
            return response
        except Exception as e:
            raise Exception(f"채팅 처리 중 오류 발생: {str(e)}")
