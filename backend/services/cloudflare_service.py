# backend/services/cloudflare_service.py

from typing import List, Dict, Optional
import asyncio
import httpx
import json
from datetime import datetime
import boto3
from botocore.config import Config
from sentence_transformers import SentenceTransformer

class CloudflareService:
    def __init__(self, config):
        self.config = config
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
        
        # Initialize Vectorize client
        self.vectorize_client = httpx.AsyncClient(
            base_url=f"https://api.cloudflare.com/client/v4/accounts/{config.CF_ACCOUNT_ID}/vectorize",
            headers={
                "Authorization": f"Bearer {config.CF_API_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        
        # Initialize R2 client
        self.r2_client = boto3.client(
            service_name='s3',
            endpoint_url=f'https://{config.CF_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=config.CF_R2_ACCESS_KEY_ID,
            aws_secret_access_key=config.CF_R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='v4'),
            region_name='auto'
        )

class VectorizeDB:
    def __init__(self, cloudflare_service):
        self.cf = cloudflare_service
        self.index_name = self.cf.config.CF_VECTORIZE_INDEX_NAME

    async def create_index(self, dimension: int = 768):
        """Create a new Vectorize index"""
        try:
            response = await self.cf.vectorize_client.post("/indexes", json={
                "name": self.index_name,
                "dimension": dimension,
                "metric": "cosine"
            })
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating Vectorize index: {e}")
            raise

    async def insert_vectors(self, vectors: List[Dict]):
        """Insert vectors into Vectorize"""
        try:
            response = await self.cf.vectorize_client.post(
                f"/indexes/{self.index_name}/insert",
                json={"vectors": vectors}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error inserting vectors: {e}")
            raise

    async def query_vectors(
        self, 
        query_vector: List[float], 
        top_k: int = 5
    ) -> List[Dict]:
        """Query similar vectors"""
        try:
            response = await self.cf.vectorize_client.post(
                f"/indexes/{self.index_name}/query",
                json={
                    "vector": query_vector,
                    "top_k": top_k
                }
            )
            response.raise_for_status()
            return response.json()["result"]["matches"]
        except Exception as e:
            print(f"Error querying vectors: {e}")
            raise

class R2Storage:
    def __init__(self, cloudflare_service):
        self.cf = cloudflare_service
        self.bucket_name = self.cf.config.CF_R2_BUCKET_NAME

    async def upload_document(
        self, 
        content: str, 
        document_id: str, 
        metadata: Optional[Dict] = None
    ):
        """Upload document to R2"""
        try:
            document_data = {
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.cf.r2_client.put_object(
                Bucket=self.bucket_name,
                Key=f"documents/{document_id}.json",
                Body=json.dumps(document_data),
                ContentType="application/json"
            )
            return document_id
        except Exception as e:
            print(f"Error uploading to R2: {e}")
            raise

    async def get_document(self, document_id: str) -> Dict:
        """Retrieve document from R2"""
        try:
            response = self.cf.r2_client.get_object(
                Bucket=self.bucket_name,
                Key=f"documents/{document_id}.json"
            )
            return json.loads(response['Body'].read())
        except Exception as e:
            print(f"Error retrieving from R2: {e}")
            raise

class RAGService:
    def __init__(self, config):
        self.config = config
        self.cloudflare = CloudflareService(config)
        self.vectorize = VectorizeDB(self.cloudflare)
        self.storage = R2Storage(self.cloudflare)
        
        # Text splitting settings
        self.chunk_size = 1000
        self.chunk_overlap = 200

    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end < len(text):
                # Find the last period or newline before chunk_size
                last_break = text.rfind('.', start, end)
                if last_break != -1:
                    end = last_break + 1
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - self.chunk_overlap
        return chunks

    async def add_document(
        self, 
        content: str, 
        metadata: Optional[Dict] = None
    ) -> str:
        """Add a document to RAG system"""
        try:
            # Generate document ID
            document_id = f"doc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Store original document in R2
            await self.storage.upload_document(content, document_id, metadata)
            
            # Split into chunks and generate embeddings
            chunks = self._split_text(content)
            vectors = []
            
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.cloudflare.embedding_model.encode(chunk)
                
                # Prepare vector record
                vector = {
                    "id": f"{document_id}_chunk_{i}",
                    "values": embedding.tolist(),
                    "metadata": {
                        "document_id": document_id,
                        "chunk_index": i,
                        "content": chunk,
                        **metadata if metadata else {}
                    }
                }
                vectors.append(vector)
            
            # Insert vectors into Vectorize
            await self.vectorize.insert_vectors(vectors)
            
            return document_id
            
        except Exception as e:
            print(f"Error adding document: {e}")
            raise

    async def get_relevant_context(
        self, 
        query: str,
        num_chunks: int = 3
    ) -> List[Dict]:
        """Get relevant context for a query"""
        try:
            # Generate query embedding
            query_embedding = self.cloudflare.embedding_model.encode(query)
            
            # Query Vectorize
            matches = await self.vectorize.query_vectors(
                query_embedding.tolist(),
                top_k=num_chunks
            )
            
            # Format results
            contexts = []
            for match in matches:
                contexts.append({
                    "content": match["metadata"]["content"],
                    "document_id": match["metadata"]["document_id"],
                    "similarity_score": match["score"],
                    "metadata": match["metadata"]
                })
            
            return contexts
            
        except Exception as e:
            print(f"Error getting context: {e}")
