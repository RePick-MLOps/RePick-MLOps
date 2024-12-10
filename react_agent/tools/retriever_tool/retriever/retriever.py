from langchain.schema import Document
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from react_agent.tools.retriever_tool.vector_store.vector_store import VectorStore
from typing import List
import json
import os

class DocumentRetriever:
    def __init__(
        self,
        db_path: str,
        collection_name: str = "pdf_collection",
        k: int = 5,
        score_threshold: float = 0.5,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
    ):
        """
        초기화 메서드: 리트리버 설정 및 데이터 경로 초기화
        Args:
            db_path (str): 벡터 DB 파일 경로
            collection_name (str): 벡터 DB 내 컬렉션 이름
            k (int): 검색 결과에서 반환할 문서 수
            score_threshold (float): 검색 결과 필터링에 사용할 점수 임계값
            vector_weight (float): 벡터 검색 결과의 가중치
            bm25_weight (float): BM25 검색 결과의 가중치
        """
        # 가중치 합이 1이 되는지 확인 (앙상블 점수 계산의 일관성 보장)
        if vector_weight + bm25_weight != 1.0:
            raise ValueError("Vector and BM25 weights must sum to 1.")
        self.vector_store = VectorStore(db_path, collection_name)  # 벡터 DB 초기화
        self.json_path = os.path.join(db_path, "processed_states.json")  # JSON 데이터 경로 설정
        self.k = k  # 반환할 문서 개수
        self.score_threshold = score_threshold  # 문서 필터링 점수 임계값
        self.vector_weight = vector_weight  # 벡터 검색 가중치
        self.bm25_weight = bm25_weight  # BM25 검색 가중치
        self._retriever = None  # 벡터 검색기 초기 상태
        self._bm25_retriever = None  # BM25 검색기 초기 상태
        self._ensemble_retriever = None  # 앙상블 검색기 초기 상태
    def _load_texts_from_json(self) -> List[str]:
        """
        JSON 파일에서 텍스트 데이터를 읽어옵니다.
        Returns:
            List[str]: JSON에서 추출한 텍스트 데이터 리스트
        """
        try:
            # JSON 파일 열기
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)  # JSON 데이터 로드
            texts = []  # 텍스트 데이터를 저장할 리스트
            # JSON의 각 PDF 데이터에서 텍스트 추출
            for pdf_data in data.values():
                if "text_summary" in pdf_data:  # "text_summary" 키가 있는 경우
                    texts.extend(pdf_data["text_summary"].values())  # 해당 텍스트 추가
            if not texts:  # 텍스트 데이터가 없으면 에러 발생
                raise ValueError("No valid texts found in JSON file for BM25.")
            return texts
        except Exception as e:
            # JSON 로딩 실패 시 에러 출력
            print(f"JSON 파일 로딩 중 오류 발생: {e}")
            return []
    @property
    def retriever(self):
        """
        벡터 검색기를 초기화 및 반환합니다.
        Returns:
            Retriever: 초기화된 VectorStore retriever
        """
        if self._retriever is None:  # 검색기가 아직 초기화되지 않았다면
            db = self.vector_store.get_db()  # 벡터 DB 가져오기
            # 검색기를 설정 (k 값 사용)
            self._retriever = db.as_retriever(
                search_type="mmr",
                search_kwargs={"k": self.k}
            )
        return self._retriever
    @property
    def bm25_retriever(self):
        """
        BM25 검색기를 초기화 및 반환합니다.
        Returns:
            BM25Retriever: 초기화된 BM25Retriever
        """
        if self._bm25_retriever is None:  # BM25 검색기가 초기화되지 않았다면
            texts = self._load_texts_from_json()  # JSON에서 텍스트 로드
            # BM25 검색기를 생성
            self._bm25_retriever = BM25Retriever.from_texts(texts, k=self.k * 2)
        return self._bm25_retriever
    @property
    def ensemble_retriever(self):
        """
        앙상블 검색기를 초기화 및 반환합니다.
        Returns:
            EnsembleRetriever: 초기화된 EnsembleRetriever
        """
        if self._ensemble_retriever is None:  # 앙상블 검색기가 초기화되지 않았다면
            # BM25 검색기가 없으면 벡터 검색기만 반환
            if self.bm25_retriever is None:
                return self.retriever
            # 앙상블 검색기를 생성 (가중치 기반 결합)
            self._ensemble_retriever = EnsembleRetriever(
                retrievers=[self.retriever, self.bm25_retriever],
                weights=[self.vector_weight, self.bm25_weight],
            )
        return self._ensemble_retriever
    def search(self, query: str) -> List[Document]:
        """
        사용자의 쿼리를 기반으로 문서를 검색합니다.
        Args:
            query (str): 검색어 (자연어 형태)
        Returns:
            List[Document]: 검색된 문서 리스트
        """
        try:
            processed_query = query.strip()  # 쿼리 전처리 (공백 제거)
            # 사용할 검색기 선택 (앙상블이 있으면 우선 사용)
            retriever_to_use = self.ensemble_retriever or self.retriever
            # 검색 실행
            docs = retriever_to_use.get_relevant_documents(processed_query)
            # 임계값을 기준으로 검색 결과 필터링
            filtered_docs = [
                doc for doc in docs if doc.metadata.get("score", 1.0) >= self.score_threshold
            ]
            return filtered_docs
        except Exception as e:
            # 검색 중 오류 발생 시 에러 출력
            print(f"검색 중 오류 발생: {e}")
            return []
