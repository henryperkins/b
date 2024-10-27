from langchain.vectorstores import Chroma
from langchain.embeddings import VertexAIEmbeddings
from typing import List, Dict
from ..config import settings

class RAGService:
    def __init__(self):
        self.embeddings = VertexAIEmbeddings()
        self.vector_store = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIR,
            embedding_function=self.embeddings
        )

    async def get_relevant_context(self, query: str, k: int = 3) -> Dict:
        results = self.vector_store.similarity_search(query, k=k)
        
        context = {
            f"reference_{i}": doc.page_content 
            for i, doc in enumerate(results)
        }
        
        return context

    async def add_to_knowledge_base(self, texts: List[str], metadata: List[Dict] = None):
        self.vector_store.add_texts(texts, metadatas=metadata)
        self.vector_store.persist()