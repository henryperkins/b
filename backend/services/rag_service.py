# backend/services/rag_service.py

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS, Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Optional
import os
import json
from datetime import datetime

class RAGService:
    def __init__(self, config):
        self.config = config
        
        # Initialize embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Initialize vector store (choose one)
        self.vector_store = self._initialize_vector_store()
        
        # Text splitter for document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def _initialize_vector_store(self):
        """Initialize the vector store with either FAISS or Chroma"""
        if self.config.VECTOR_STORE_TYPE == "faiss":
            if os.path.exists(self.config.FAISS_INDEX_PATH):
                return FAISS.load_local(
                    self.config.FAISS_INDEX_PATH, 
                    self.embeddings
                )
            return FAISS.from_texts(
                ["Initial empty index"], 
                self.embeddings
            )
        else:
            return Chroma(
                persist_directory=self.config.CHROMA_PERSIST_DIR,
                embedding_function=self.embeddings
            )

    async def add_document(
        self, 
        content: str, 
        metadata: Optional[Dict] = None
    ) -> List[str]:
        """Add a document to the vector store"""
        # Split document into chunks
        chunks = self.text_splitter.split_text(content)
        
        # Add metadata to each chunk
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_meta = {
                'chunk_id': i,
                'timestamp': datetime.utcnow().isoformat(),
                'source': metadata.get('source', 'unknown') if metadata else 'unknown',
                **metadata if metadata else {}
            }
            chunk_metadata.append(chunk_meta)

        # Add to vector store
        try:
            self.vector_store.add_texts(
                texts=chunks,
                metadatas=chunk_metadata
            )
            
            # If using FAISS, save the index
            if isinstance(self.vector_store, FAISS):
                self.vector_store.save_local(self.config.FAISS_INDEX_PATH)
                
            return chunks
        except Exception as e:
            print(f"Error adding document to vector store: {e}")
            raise

    async def get_relevant_context(
        self, 
        query: str,
        num_chunks: int = 3,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """Retrieve relevant context for a query"""
        try:
            # Get similar documents with scores
            docs_and_scores = self.vector_store.similarity_search_with_score(
                query,
                k=num_chunks
            )
            
            # Filter and format results
            relevant_contexts = []
            for doc, score in docs_and_scores:
                if score >= min_similarity:
                    relevant_contexts.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata,
                        'similarity_score': score
                    })
            
            return relevant_contexts
        except Exception as e:
            print(f"Error retrieving context: {e}")
            raise

    async def delete_document(self, document_id: str):
        """Delete a document and its chunks from the vector store"""
        try:
            # For Chroma
            if not isinstance(self.vector_store, FAISS):
                self.vector_store.delete(
                    filter={"source_id": document_id}
                )
            # For FAISS (requires reimplementation of the index)
            else:
                # Get all documents except the one to delete
                all_docs = self.vector_store.index_to_docstore_id
                filtered_docs = {
                    k: v for k, v in all_docs.items() 
                    if v.get('source_id') != document_id
                }
                # Recreate index with filtered documents
                new_texts = [doc.page_content for doc in filtered_docs.values()]
                new_metadata = [doc.metadata for doc in filtered_docs.values()]
                
                self.vector_store = FAISS.from_texts(
                    new_texts,
                    self.embeddings,
                    metadatas=new_metadata
                )
                self.vector_store.save_local(self.config.FAISS_INDEX_PATH)
                
        except Exception as e:
            print(f"Error deleting document: {e}")
            raise

    async def search_documents(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search documents with optional metadata filters"""
        try:
            if filters and not isinstance(self.vector_store, FAISS):
                # Chroma supports metadata filtering
                results = self.vector_store.similarity_search_with_score(
                    query,
                    k=limit,
                    filter=filters
                )
            else:
                # Basic search for FAISS
                results = self.vector_store.similarity_search_with_score(
                    query,
                    k=limit
                )
            
            return [{
                'content': doc.page_content,
                'metadata': doc.metadata,
                'similarity_score': score
            } for doc, score in results]
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            raise