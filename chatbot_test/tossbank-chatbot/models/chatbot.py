import os
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain import PromptTemplate
from langchain.chains import RetrievalQA

os.environ['OPENAI_API_KEY'] = "YOUR_API_KEY"

def load_embedding_model(model_name="BAAI/bge-m3"):
    return HuggingFaceEmbeddings(model_name=model_name)

def load_vectorstore(vectordb_path):
    # 불러오기
    return Chroma(
        persist_directory=vectordb_path,
        embedding_function=load_embedding_model()
    )

def toss_chatbot():
    vectorstore = load_vectorstore("/home/ubuntu/working/tossbank-chatbot/models/tossbank.db")
    retriever = vectorstore.as_retriever()

    template = """당신은 토스뱅크에서 만든 대출상품에 대해 설명해주는 챗봇입니다.
    "개쩌는개발자소미노"가 만들었습니다. 주어진 검색 결과를 바탕으로 답변하세요.
    검색 결과에 없는 내용이라면 답변할 수 없다고 하세요. 반말로 친근하게 답변하세요.
    {context}

    Question: {question}
    Answer:
    """

    prompt = PromptTemplate.from_template(template)
    llm = ChatOpenAI(
        model_name='gpt-4o',
        temperature=0,
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type_kwargs={"prompt": prompt},
        retriever=retriever,
        return_source_documents=True
    )

    return qa_chain