from langchain.schema import Document
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from react_agent.tools.retriever_tool.vector_store.vector_store import VectorStore
from typing import List
import json
import os


class DocumentRetriever:
    def __init__(
        self,
        db_path: str,
        collection_name: str = "pdf_collection",
        k: int = 3,
        score_threshold: float = 0.5,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
    ):
        self.vector_store = VectorStore(db_path, collection_name)
        self.json_path = os.path.join(db_path, "processed_states.json")
        self.k = k
        self.score_threshold = score_threshold
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self._retriever = None
        self._bm25_retriever = None
        self._ensemble_retriever = None

    def _load_texts_from_json(self) -> List[str]:
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            texts = []
            for pdf_data in data.values():
                if "text_summary" in pdf_data:
                    texts.extend(pdf_data["text_summary"].values())
            return texts
        except Exception as e:
            print(f"JSON 파일 로딩 중 오류 발생: {e}")
            return []

    @property
    def retriever(self):
        if self._retriever is None:
            db = self.vector_store.get_db()
            self._retriever = db.as_retriever(search_kwargs={"k": self.k * 2})
        return self._retriever

    @property
    def bm25_retriever(self):
        if self._bm25_retriever is None:
            texts = self._load_texts_from_json()
            if texts:  # texts가 비어있지 않은 경우에만 BM25 검색기 생성
                self._bm25_retriever = BM25Retriever.from_texts(texts, k=self.k * 2)
        return self._bm25_retriever

    @property
    def ensemble_retriever(self):
        if self._ensemble_retriever is None:
            # BM25 검색기가 생성되지 않았거나 실패한 경우 벡터 검색기만 사용
            if self.bm25_retriever is None:
                return self.retriever

            self._ensemble_retriever = EnsembleRetriever(
                retrievers=[self.retriever, self.bm25_retriever],
                weights=[self.vector_weight, self.bm25_weight],
            )
        return self._ensemble_retriever

    def search(self, query: str) -> List[Document]:
        """
        주어진 쿼리로 문서를 검색합니다.

        Args:
            query (str): 검색어. 자연어 질문 형태로 입력 가능

        Returns:
            List[Document]: 검색된 문서 리스트
        """
        try:
            processed_query = query.strip()

            # ensemble_retriever가 None이면 기본 벡터 검색기 사용
            retriever_to_use = self.ensemble_retriever or self.retriever
            docs = retriever_to_use.invoke(processed_query)
            return docs

        except Exception as e:
            print(f"검색 중 오류 발생: {e}")
            return []
