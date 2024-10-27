from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database.db import get_db
from ..services.conversation_service import conversation_service
from ..auth.auth_service import auth_service
from ..schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    FolderCreate,
    FolderResponse,
    TagCreate,
    TagResponse
)

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    return await conversation_service.create_conversation(db, current_user.id, data)

@router.get("/", response_model=List[ConversationResponse])
async def get_conversations(
    folder_id: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    tag_ids = tags.split(",") if tags else None
    return await conversation_service.get_conversations(
        db, current_user.id, folder_id, search, tag_ids, skip, limit
    )

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    return await conversation_service.add_message(
        db, conversation_id, current_user.id, message
    )

@router.post("/folders", response_model=FolderResponse)
async def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    return await conversation_service.create_folder(
        db, current_user.id, data.name, data.description
    )

@router.post("/tags", response_model=TagResponse)
async def create_tag(
    data: TagCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    return await conversation_service.create_tag(
        db, current_user.id, data.name, data.color
    )

@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    return await conversation_service.update_conversation(
        db, conversation_id, current_user.id, data
    )

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    await conversation_service.delete_conversation(db, conversation_id, current_user.id)
    return {"message": "Conversation deleted"}