from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from ..models.conversation import Conversation, Message, Folder, Tag
from ..schemas.conversation import ConversationCreate, ConversationUpdate, MessageCreate
from fastapi import HTTPException, status

class ConversationService:
    async def create_conversation(
        self, 
        db: Session, 
        user_id: str, 
        data: ConversationCreate
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            title=data.title,
            description=data.description,
            folder_id=data.folder_id
        )
        
        if data.tags:
            tags = db.query(Tag).filter(
                and_(Tag.id.in_(data.tags), Tag.user_id == user_id)
            ).all()
            conversation.tags = tags
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    async def get_conversations(
        self,
        db: Session,
        user_id: str,
        folder_id: Optional[str] = None,
        search: Optional[str] = None,
        tag_ids: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Conversation]:
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        
        if folder_id:
            query = query.filter(Conversation.folder_id == folder_id)
        
        if search:
            query = query.filter(
                or_(
                    Conversation.title.ilike(f"%{search}%"),
                    Conversation.description.ilike(f"%{search}%")
                )
            )
        
        if tag_ids:
            query = query.filter(Conversation.tags.any(Tag.id.in_(tag_ids)))
        
        return query.order_by(
            Conversation.is_pinned.desc(),
            Conversation.updated_at.desc()
        ).offset(skip).limit(limit).all()

    async def add_message(
        self,
        db: Session,
        conversation_id: str,
        user_id: str,
        message_data: MessageCreate
    ) -> Message:
        conversation = await self.get_conversation(db, conversation_id, user_id)
        
        message = Message(
            conversation_id=conversation_id,
            role=message_data.role,
            content=message_data.content,
            metadata=message_data.metadata
        )
        
        db.add(message)
        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(message)
        return message

    async def create_folder(
        self,
        db: Session,
        user_id: str,
        name: str,
        description: Optional[str] = None
    ) -> Folder:
        folder = Folder(
            user_id=user_id,
            name=name,
            description=description
        )
        
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder

    async def create_tag(
        self,
        db: Session,
        user_id: str,
        name: str,
        color: Optional[str] = None
    ) -> Tag:
        tag = Tag(
            user_id=user_id,
            name=name,
            color=color
        )
        
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    async def search_conversations(
        self,
        db: Session,
        user_id: str,
        query: str,
        include_messages: bool = False
    ) -> List[Conversation]:
        base_query = db.query(Conversation).filter(Conversation.user_id == user_id)
        
        if include_messages:
            base_query = base_query.join(Message).filter(
                or_(
                    Conversation.title.ilike(f"%{query}%"),
                    Conversation.description.ilike(f"%{query}%"),
                    Message.content.ilike(f"%{query}%")
                )
            ).distinct()
        else:
            base_query = base_query.filter(
                or_(
                    Conversation.title.ilike(f"%{query}%"),
                    Conversation.description.ilike(f"%{query}%")
                )
            )
        
        return base_query.order_by(Conversation.updated_at.desc()).all()

conversation_service = ConversationService()