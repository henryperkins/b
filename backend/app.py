from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from typing import Dict
from datetime import datetime

from .auth.auth_service import auth_service
from .services.gemini_service import GeminiService
from .services.rag_service import RAGService
from .services.tool_service import ToolService
from .models.conversation import Conversation, Message

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
gemini_service = GeminiService()
rag_service = RAGService()
tool_service = ToolService()

# Store conversations in memory (replace with database in production)
conversations: Dict[str, Conversation] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/chat/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    
    if conversation_id not in conversations:
        conversations[conversation_id] = Conversation(
            id=conversation_id,
            messages=[],
            metadata={"created_at": datetime.now().isoformat()}
        )
    
    try:
        # Wait for authentication message
        auth_message = await websocket.receive_json()
        if auth_message.get("type") != "authenticate":
            await websocket.close(code=4001)
            return

        # Verify token
        token = auth_message.get("token")
        try:
            user = await auth_service.get_current_user(token)
        except Exception:
            await websocket.close(code=4001)
            return

        await manager.connect(websocket, user.id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Create user message
                user_message = Message(
                    role="user",
                    content=message_data["content"]
                )
                
                # Add message to conversation history
                conversations[conversation_id].messages.append(user_message)
                
                # Get relevant context using RAG
                context = await rag_service.get_relevant_context(user_message.content)
                
                # Get available tools
                tools = tool_service.get_available_tools()
                
                # Generate response using Gemini
                response_content = await gemini_service.generate_response(
                    messages=conversations[conversation_id].messages,
                    context=context,
                    tools=tools
                )
                
                # Create assistant message
                assistant_message = Message(
                    role="assistant",
                    content=response_content,
                    context=context
                )
                
                # Add assistant message to conversation history
                conversations[conversation_id].messages.append(assistant_message)
                
                # Send response back to client
                await websocket.send_json({
                    "message": assistant_message.dict(),
                    "conversation_id": conversation_id
                })
                
        except WebSocketDisconnect:
            manager.disconnect(user.id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=4000)

# Add REST endpoints for conversation management
@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        return {"error": "Conversation not found"}
    return conversations[conversation_id]

@app.post("/conversations")
async def create_conversation():
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = Conversation(
        id=conversation_id,
        messages=[],
        metadata={"created_at": datetime.now().isoformat()}
    )
    return {"conversation_id": conversation_id}