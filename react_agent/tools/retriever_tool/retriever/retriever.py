from langchain.schema import Document
from react_agent.tools.retriever_tool.vector_store.vector_store import VectorStore
from typing import List


class DocumentRetriever:
    def __init__(
        self, db_path: str, collection_name: str = "pdf_collection", k: int = 5
    ):
        self.vector_store = VectorStore(db_path, collection_name)
        self.k = k
        self._retriever = None

    @property
    def retriever(self):
        if self._retriever is None:
            db = self.vector_store.get_db()
            self._retriever = db.as_retriever(
                search_type="similarity", search_kwargs={"k": self.k}
            )
        return self._retriever

    def search(self, query: str) -> List[Document]:
        """
        주어진 쿼리로 문서를 검색합니다.

        Args:
            query (str): 검색어. 자연어 질문 형태로 입력 가능

        Returns:
            List[Document]: 검색된 문서 리스트
        """
        try:
            # 검색어 전처리
            processed_query = query.strip()

            # 문서 검색 (한 번만 실행)
            docs = self.retriever.invoke(processed_query)
            return docs

        except Exception as e:
            print(f"검색 중 오류 발생: {e}")
            return []
