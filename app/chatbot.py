from dotenv import load_dotenv
from typing import List
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_teddynote.evaluator import OpenAIRelevanceGrader
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA

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
        # 임베딩 모델 초기화
        self.embedding = HuggingFaceEmbeddings(model_name=model_name)

        if documents:
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding_function=self.embedding,
                persist_directory=persist_directory,
            )
        else:
            self.vectorstore = self.load_vectorstore(persist_directory, model_name)

        # 벡터스토어 생성 및 문서 추가
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding_function=self.embedding,
            persist_directory=persist_directory,
        )

        self.setup_retrievers()
        self.setup_relevance_checker()
        self.setup_chain()

    def setup_chain(self):
        # 프롬프트 템플릿 설정
        prompt = PromptTemplate.from_template(
            """당신은 질의응답 작업을 위한 어시스턴트입니다.
        제공된 검색 컨텍스트를 사용하여 질문에 답변하세요.
        답을 모르는 경우에는 모른다고 말씀해 주세요.
        한국어로 답변하세요.

        # 지침:
        질문의 의도를 정확히 파악하고 가장 적절한 답변을 제공하세요.
        - 질문의 맥락과 질문자가 왜 이 질문을 했는지 스스로 물어보고, 질문에 대해 고민한 후 이해를 바탕으로 적절한 답변을 제공하세요.
        2. 검색된 컨텍스트에서 가장 관련성 높은 내용(질문과 직접적으로 관련된 핵심 내용)을 선별하여 답변을 작성하세요.
        3. 간결하고 논리적인 답변을 작성하세요. 답변 작성 시 단순히 선별한 내용을 나열하지 말고, 맥락에 맞게 재구성하여 자연스러운 문단이 되도록 하세요.
        4. 질문에 대한 컨텍스트를 찾지 못했거나, 문서는 검색되었으나 그 내용이 질문과 관련이 없는 경우 '보유한 자료에서 해당 질문에 대한 답변을 찾을 수 없습니다'라고 말씀해 주세요.
        5. 답변을 핵심 포인트 표로 작성하세요.
        6. 답변에는 반드시 모든 출처와 페이지 번호를 포함해야 합니다.
        7. 답변은 반드시 한국어로 작성해야 합니다.
        8. 가능한 한 상세하게 답변하세요.
        9. 답변은 '**📚 문서에서 검색한 내용 기반 답변입니다**'로 시작하고 '**📌 출처**'로 끝내세요.
        10. 페이지 번호는 정수여야 합니다.

        #Context: 
        {context}

        ###

        #답변 형식 예시:
        **📚 문서에서 검색한 내용기반 답변입니다**

        (답변 요약)
        (질문과 관련된 표가 컨텍스트에 있는 경우 포함)
        (질문과 관련된 이미지 설명이 컨텍스트에 있는 경우 포함)
        (질문에 대한 상세 답변)

        **📌 출처**
        [여기에는 파일명(.pdf만)과 페이지만 작성]

        - 파일명.pdf, 192쪽
        - 파일명.pdf, 192쪽
        - ...

        ###

        #Question:
        {question}

        #Answer:"""
        )

        # LLM 설정
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

        # RetrievalQA 체인 설정
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type_kwargs={"prompt": prompt},
            retriever=self.ensemble_retriever,
            return_source_documents=True,
        )

        # 기존 체인도 유지 (필요한 경우)
        self.chain = (
            {
                "context": RunnableLambda(self.retrieve_and_check),
                "question": RunnablePassthrough(),
            }
            | prompt
            | llm
            | StrOutputParser()
        )

    def setup_retrievers(self):
        # BM25 리트리버 설정
        self.bm25_retriever = BM25Retriever.from_documents(self.vectorstore.get(), k=5)

        # 벡터스토어 리트리버 설정
        self.vector_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})

        # 앙상블 리트리버 설정
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, self.vector_retriever], weights=[0.7, 0.3]
        )

    def setup_relevance_checker(self):
        # Relevance Checker 설정
        self.relevance_checker = OpenAIRelevanceGrader(
            ChatOpenAI(model="gpt-4o-mini", temperature=0), target="retrieval-question"
        ).create()

    def retrieve_and_check(self, question, use_checker=True):
        # 문서 검색
        retrieved_documents = self.ensemble_retriever.invoke(question)

        if not use_checker:
            return retrieved_documents

        # 관련성 체크를 위한 입력 준비
        checking_inputs = [
            {"context": doc.page_content, "input": question}
            for doc in retrieved_documents
        ]

        # 관련성 체크 수행
        checked_results = self.relevance_checker.batch(checking_inputs)

        # 관련 있는 문서만 필터링
        filtered_documents = [
            doc
            for doc, result in zip(retrieved_documents, checked_results)
            if result.score == "yes"
        ]

        return filtered_documents

    # 출력 포맷팅
    def format_response(self, answer: str, sources: List[Document]) -> str:
        """
        답변과 출처를 포맷팅합니다.
        """
        response = "**📚 문서에서 검색한 내용 기반 답변입니다**\n\n"
        response += f"{answer}\n\n"

        if sources:
            response += "**📌 출처**\n"
            for source in sources:
                response += f"- {source.metadata.get('source', 'Unknown')}\n"

        return response

    def chat(self, question: str) -> str:
        """
        사용자 질문에 대한 답변을 생성합니다.

        Args:
            question (str): 사용자 질문

        Returns:
            str: 생성된 답변
        """
        try:
            # RetrievalQA 체인을 사용하여 답변 생성
            result = self.qa_chain({"query": question})

            # 응답 포맷팅
            return self.format_response(result["result"], result["source_documents"])
        except Exception as e:
            return f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"

    @staticmethod
    def load_vectorstore(vectordb_path: str, model_name: str = "BAAI/bge-m3"):
        """
        벡터스토어를 로드합니다.
        """
        embedding = HuggingFaceEmbeddings(model_name=model_name)
        return Chroma(persist_directory=vectordb_path, embedding_function=embedding)
