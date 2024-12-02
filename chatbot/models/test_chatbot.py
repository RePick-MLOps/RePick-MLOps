from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_core.documents import Document


def load_embedding_model(model_name="jhgan/ko-sbert-sts"):
    return HuggingFaceEmbeddings(model_name=model_name)


def load_vectorstore(vectordb_path):
    try:
        embeddings = load_embedding_model()
        vectorstore = Chroma(
            persist_directory="s3://repick-chromadb/vectordb",
            embedding_function=embeddings,
            collection_name="pdf_collection",
        )

        # 데이터 상세 확인
        collection = vectorstore._collection.get()
        print(f"\n=== Chroma DB 상태 ===")
        print(
            f"총 문서 수: {len(collection['documents']) if collection['documents'] else 0}"
        )
        print(f"컬렉션 이름: pdf_collection")

        return vectorstore
    except Exception as e:
        print(f"Error loading vector store: {str(e)}")
        raise


def create_prompt():
    return PromptTemplate.from_template(
        """You are an assistant for question-answering tasks. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. 
Answer in Korean.

# Direction:
Make sure you understand the intent of the question and provide the most appropriate answer.
- Ask yourself the context of the question and why the questioner asked it, think about the question, and provide an appropriate answer based on your understanding.
2. Select the most relevant content (the key content that directly relates to the question) from the context in which it was retrieved to write your answer.
3. Create a concise and logical answer. When creating your answer, don't just list your selections, but rearrange them to fit the context so they flow naturally into paragraphs.
4. If you haven't searched for context for the question, or if you've searched for a document but its content isn't relevant to the question, you should say 'I can't find an answer to that question in the materials I have'.
5. Write your answer in a table of key points.
6. Your answer must include all sources and page numbers.
7. Your answer must be written in Korean.
8. Be as detailed as possible in your answer.
9. Begin your answer with 'This answer is based on content found in the document **' and end with '**📌 source**'.
10. Page numbers should be whole numbers.

#Context: 
{context}

###

#Example Format:
**📚 문서에서 검색한 내용기반 답변입니다**

(brief summary of the answer)
(include table if there is a table in the context related to the question)
(include image explanation if there is a image in the context related to the question)
(detailed answer to the question)

**📌 출처**
[here you only write filename(.pdf only), page]

- 파일명.pdf, 192쪽
- 파일명.pdf, 192쪽
- ...

###

#Question:
{question}

#Answer:"""
    )


def create_chain(retriever):
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    def retrieve_and_format(question: str) -> str:
        try:
            # 문서 검색
            docs = retriever.get_relevant_documents(question)

            # 검색된 문서의 내용을 하나의 문자열로 결합
            context = "\n\n".join(doc.page_content for doc in docs)

            # 메타데이터 정보 추가
            sources = []
            for doc in docs:
                if doc.metadata.get("source") and doc.metadata.get("page"):
                    sources.append(
                        f"- {doc.metadata['source']}, {doc.metadata['page']}쪽"
                    )

            if sources:
                context += "\n\n출처:\n" + "\n".join(sources)

            return context

        except Exception as e:
            print(f"Error in retrieve_and_format: {str(e)}")
            return "문서 검색 중 오류가 발생했습니다."

    chain = (
        {
            "context": RunnableLambda(retrieve_and_format),
            "question": RunnablePassthrough(),
        }
        | create_prompt()
        | llm
        | StrOutputParser()
    )

    return chain


def initialize_retrievers(all_docs):
    # BM25 리트리버 초기화
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = 5

    # FAISS 리트리버 초기화
    embedding = OpenAIEmbeddings()
    faiss_vectorstore = FAISS.from_documents(all_docs, embedding)
    faiss_retriever = faiss_vectorstore.as_retriever(search_kwargs={"k": 5})

    # 앙상블 리트리버 초기화
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.7, 0.3],
    )

    return ensemble_retriever


def clean_retrieved_documents(retrieved_documents):
    clean_docs = []

    for doc in retrieved_documents:
        # Document 객체가 아닌 경우 건너뛰기
        if not hasattr(doc, "metadata") or not hasattr(doc, "page_content"):
            continue

        metadata = doc.metadata
        new_metadata = {}
        content = doc.page_content

        if isinstance(content, dict):
            # content가 dict인 경우 문자열로 변환
            content = str(content)

        if metadata.get("type") in ["page_summary", "text"]:
            if "page" in metadata:
                new_metadata["page"] = metadata["page"]
            if "source" in metadata:
                new_metadata["source"] = metadata["source"]
            if metadata.get("type") == "text" and "summary" in metadata:
                new_metadata["summary"] = metadata["summary"]
            clean_docs.append(Document(page_content=content, metadata=new_metadata))

        elif metadata.get("type") == "hypothetical_questions":
            content = metadata.get("summary", content)
            if "page" in metadata:
                new_metadata["page"] = metadata["page"]
            if "source" in metadata:
                new_metadata["source"] = metadata["source"]
            clean_docs.append(Document(page_content=content, metadata=new_metadata))

    return clean_docs


def retrieve_and_check(question, ensemble_retriever):
    retrieved_documents = ensemble_retriever.invoke(question)
    cleaned_documents = clean_retrieved_documents(retrieved_documents)
    return cleaned_documents


def test_chatbot():
    vectorstore = load_vectorstore("/Users/naeun/working/RePick-MLOps/data/vectordb")
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},
        collection_name="pdf_collection",
    )

    qa_chain = create_chain(retriever)
    return qa_chain
