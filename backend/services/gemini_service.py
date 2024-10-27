import google.generativeai as genai
from typing import List, Dict
from ..config import settings
from ..models.conversation import Message

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        
    async def generate_response(
        self, 
        messages: List[Message], 
        context: Dict = None,
        tools: List[Dict] = None
    ) -> str:
        # Format conversation history
        formatted_messages = self._format_messages(messages)
        
        # Prepare prompt with context
        prompt = self._prepare_prompt(formatted_messages, context)
        
        # Generate response
        response = await self.model.generate_content_async(
            prompt,
            generation_config={
                'temperature': settings.TEMPERATURE,
                'max_output_tokens': settings.MAX_OUTPUT_TOKENS,
            }
        )
        
        return response.text

    def _format_messages(self, messages: List[Message]) -> str:
        formatted = []
        for msg in messages[-settings.MAX_HISTORY_LENGTH:]:
            formatted.append(f"{msg.role}: {msg.content}")
        return "\n".join(formatted)

    def _prepare_prompt(self, messages: str, context: Dict = None) -> str:
        prompt = messages
        if context:
            context_str = "\nRelevant context:\n" + "\n".join(
                [f"- {k}: {v}" for k, v in context.items()]
            )
            prompt = context_str + "\n" + prompt
        return prompt   