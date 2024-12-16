from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_core.documents import Document
import chromadb
from chromadb.config import Settings
import logging
import subprocess
import os
from .prompt_template import PROMPT_TEMPLATE
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()


def load_embedding_model(model_name="jhgan/ko-sbert-sts"):
    return HuggingFaceEmbeddings(model_name=model_name)


def load_vectorstore(vectordb_path=None):
    try:
        embeddings = load_embedding_model()
        local_db_path = "./data/vectordb"
        s3_bucket = "repick-chromadb"

        logger.info(f"ChromaDB 경로: {local_db_path}")

        # S3에서 전체 데이터 다운로드
        try:

            # 전체 디렉토리 동기화
            sync_cmd = f"aws s3 sync s3://repick-chromadb/vectordb {local_db_path}"
            logger.info(f"실행 명령어: {sync_cmd}")
            result = subprocess.run(
                sync_cmd, shell=True, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("S3에서 모든 데이터를 성공적으로 다운로드했습니다.")
            else:
                logger.error(f"S3 다운로드 실패: {result.stderr}")

            # 로컬 디렉토리 내용 확인
            logger.info(f"로컬 디렉토리 내용:")
            ls_result = subprocess.run(
                f"ls -la {local_db_path}", shell=True, capture_output=True, text=True
            )
            logger.info(ls_result.stdout)

        except Exception as e:
            logger.error(f"S3 다운로드 실패: {str(e)}")

        # ChromaDB 클라이언트 생성
        client = chromadb.PersistentClient(
            path=local_db_path,
            settings=Settings(
                anonymized_telemetry=False, allow_reset=True, is_persistent=True
            ),
        )

        # Langchain Chroma 초기화
        vectorstore = Chroma(
            client=client,
            embedding_function=embeddings,
            collection_name="pdf_collection",
        )

        # 컬렉션 상태 확인
        try:
            collection = client.get_collection("pdf_collection")
            count = collection.count()
            logger.info(f"\n=== Chroma DB 상태 ===")
            logger.info(f"총 문서 수: {count}")
            logger.info(f"컬렉션 이름: pdf_collection")
            logger.info(f"로컬 경로: {local_db_path}")
        except Exception as e:
            logger.warning(f"컬렉션 상태 확인 실패: {str(e)}")
            collection = client.create_collection("pdf_collection")
            logger.info("새 컬렉션이 생성되었습니다.")

        return vectorstore

    except Exception as e:
        logger.error(f"Error loading vector store: {str(e)}")
        raise


def save_to_s3():
    """ChromaDB 데이터를 S3에 업로드"""
    try:
        local_db_path = "data/vectordb"

        # 현재 파일 상태 확인
        logger.info("=== 로컬 파일 상태 ===")
        ls_result = subprocess.run(
            f"ls -lh {local_db_path}", shell=True, capture_output=True, text=True
        )
        logger.info(ls_result.stdout)

        # S3 업로드 전 상태 확인
        logger.info("=== S3 업로드 전 상태 ===")
        s3_ls_result = subprocess.run(
            "aws s3 ls s3://repick-chromadb/vectordb/ --recursive",
            shell=True,
            capture_output=True,
            text=True,
        )
        logger.info(s3_ls_result.stdout)

        # 동기화 명령 실행
        sync_command = (
            f"aws s3 sync {local_db_path} s3://repick-chromadb/vectordb --delete"
        )
        logger.info(f"실행 명령어: {sync_command}")

        result = subprocess.run(
            sync_command, shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            logger.info("S3 업로드 성공")
        else:
            logger.error(f"S3 업로드 실패: {result.stderr}")

        # 업로드 후 S3 상태 확인
        logger.info("=== S3 업로드 후 상태 ===")
        s3_final_result = subprocess.run(
            "aws s3 ls s3://repick-chromadb/vectordb/ --recursive",
            shell=True,
            capture_output=True,
            text=True,
        )
        logger.info(s3_final_result.stdout)

    except Exception as e:
        logger.error(f"S3 업로드 실패: {str(e)}")
        raise


def create_prompt():
    return PromptTemplate.from_template(PROMPT_TEMPLATE)


def create_chain(retriever):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

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


def initialize_retrievers(vectorstore):
    # Chroma 리트리버 초기화 - k값과 score_threshold 조정
    chroma_retriever = vectorstore.as_retriever(
        search_type="mmr",  # MMR로 변경하여 다양성과 관련성 균형
        search_kwargs={
            "k": 8,  # 검색 문서 수 증가
            "fetch_k": 20,  # MMR 후보군 증가
            "lambda_mult": 0.7,  # 관련성과 다양성의 균형
        },
    )

    try:
        # Chroma에서 모든 문서를 가져오는 올바른 방법
        collection = vectorstore._collection
        result = collection.get()

        documents = []
        for i in range(len(result["documents"])):
            doc = result["documents"][i]
            metadata = result["metadatas"][i] if result["metadatas"] else {}
            # 문서 내용이 너무 짧은 경우 제외
            if len(str(doc).strip()) > 50:
                documents.append(Document(page_content=doc, metadata=metadata))

        if documents:
            bm25_retriever = BM25Retriever.from_documents(documents)
            bm25_retriever.k = 8  # BM25도 동일하게 k값 증가

            # 앙상블 리트리버의 가중치 조정
            ensemble_retriever = EnsembleRetriever(
                retrievers=[chroma_retriever, bm25_retriever],
                weights=[0.8, 0.2],  # 벡터 검색에 더 높은 가중치
            )
            logger.info("앙상블 리트리버 초기화 성공")
            return ensemble_retriever
        else:
            logger.warning("문서가 없어 Chroma 리트리버만 사용")
            return chroma_retriever

    except Exception as e:
        logger.error(f"BM25 리트리버 초기화 실패: {str(e)}")
        logger.info("Chroma 리트리버만 사용")
        return chroma_retriever


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

        if metadata.get("type") == "text":
            if "page" in metadata:
                new_metadata["page"] = metadata["page"]
            if "source" in metadata:
                new_metadata["source"] = metadata["source"]
            if "summary" in metadata:
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


def chatbot():
    vectorstore = load_vectorstore()
    # 앙상블 리트리버 사용
    retriever = initialize_retrievers(vectorstore)

    # k값 증가 및 search_type 다양화
    qa_chain = create_chain(retriever)
    return qa_chain
