from typing import Optional
from ..vector_store.vector_store import VectorStore

class DocumentRetriever:
    def __init__(
        self,
        db_path: str,
        collection_name: str = "pdf_collection",
        k: int = 3
    ):
        self.vector_store = VectorStore(db_path, collection_name)
        self.k = k
        self._retriever = None
        
    @property
    def retriever(self):
        if self._retriever is None:
            db = self.vector_store.get_db()
            self._retriever = db.as_retriever(
                search_kwargs={"k": self.k}
            )
        return self._retriever
    
    def search(self, query: str):
        return self.retriever.get_relevant_documents(query)