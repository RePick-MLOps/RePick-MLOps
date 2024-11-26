import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain import PromptTemplate
from langchain.chains import RetrievalQA

# OpenAI API 키 설정
load_dotenv()

class Chatbot:
    def __init__(self, db_path="data/vectordb", model_name="BAAI/bge-m3"):
        # 임베딩 모델 로드
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        
        # 벡터스토어 로드
        self.vector_store = Chroma(persist_directory=db_path, embedding_function=self.embedding_model)
        
        # 검색기 생성
        self.retriever = self.vector_store.as_retriever()

        # 프롬프트 템플릿 설정
        template = """당신은 증권사 애널리스트가 만든 리포트를 분석하고 요약하는 챗봇입니다. 
        주어진 검색 결과를 바탕으로 답변하세요. 검색 결과에 없는 내용이라면 답변할 수 없다고 하세요.
        아래 규칙을 바탕으로 공손한 어투를 사용하여 답변하세요.

        ### 규칙
        1. summary는 최대 1000자로 요약하세요.
        2. markdown 형식으로 답변하세요.
        3. 최대한 자세하게 답변하세요.

        {context}

        Question: {question}
        Answer:
        """
        self.prompt = PromptTemplate.from_template(template)

        # LLM 설정
        self.llm = ChatOpenAI(
            model_name='gpt-4o',
            temperature=0,
        )

        # QA 체인 생성
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type_kwargs={"prompt": self.prompt},
            retriever=self.retriever,
            return_source_documents=True
        )

    def __call__(self, query):
        # 쿼리를 처리하여 응답 생성
        response = self.qa_chain.run(query)
        return {'result': response}

# 챗봇 인스턴스 생성
chatbot = Chatbot()