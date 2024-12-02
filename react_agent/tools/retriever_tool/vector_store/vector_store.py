from langchain_chroma import Chroma
from ..embedding.embedding_model import EmbeddingModelSingleton

class VectorStore:
    def __init__(self, db_path: str, collection_name: str = "pdf_collection"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.embedding_model = EmbeddingModelSingleton.get_instance()
        
    def get_db(self):
        return Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embedding_model,
            collection_name=self.collection_name
        )