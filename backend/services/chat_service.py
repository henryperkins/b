# backend/services/chat_service.py

from typing import List, Dict
from .rag_service import RAGService

class ChatService:
    def __init__(self, config):
        self.config = config
        self.rag_service = RAGService(config)
        
    async def process_message(
        self,
        message: str,
        conversation_id: str,
        user_id: str
    ) -> Dict:
        try:
            # Get relevant context
            contexts = await self.rag_service.get_relevant_context(
                query=message,
                num_chunks=self.config.MAX_CONTEXTS
            )
            
            # Filter contexts by similarity score
            relevant_contexts = [
                ctx for ctx in contexts 
                if ctx["similarity_score"] >= self.config.MIN_SIMILARITY_SCORE
            ]
            
            # Format context for the LLM
            formatted_context = self._format_context(relevant_contexts)
            
            # Prepare prompt
            prompt = self._create_prompt(message, formatted_context)
            
            # Generate response using your LLM service
            response = await self.generate_response(prompt)
            
            # Store message and response
            await self.store_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                message=message,
                response=response,
                contexts=relevant_contexts
            )
            
            return {
                "response": response,
                "contexts": relevant_contexts
            }
            
        except Exception as e:
            print(f"Error processing message: {e}")
            raise

    def _format_context(self, contexts: List[Dict]) -> str:
        """Format contexts for the prompt"""
        if not contexts:
            return ""
            
        formatted = "Relevant context:\n\n"
        for i, ctx in enumerate(contexts, 1):
            formatted += f"{i}. {ctx['content']}\n\n"
        return formatted

    def _create_prompt(self, message: str, context: str) -> str:
        """Create prompt with context"""
        return f"""Given the following context and user message, provide a relevant response.
If the context is not relevant to the message, rely on your general knowledge.

{context}
User message: {message}

Response:"""
