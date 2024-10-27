from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database.db import Base

# Many-to-many relationship for conversation tags
conversation_tags = Table(
    'conversation_tags',
    Base.metadata,
    Column('conversation_id', String, ForeignKey('conversations.id')),
    Column('tag_id', String, ForeignKey('tags.id'))
)

class Folder(Base):
    __tablename__ = "folders"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    conversations = relationship("Conversation", back_populates="folder")
    user = relationship("DBUser", back_populates="folders")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    color = Column(String, default="#808080")
    
    conversations = relationship("Conversation", secondary=conversation_tags, back_populates="tags")
    user = relationship("DBUser", back_populates="tags")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    folder_id = Column(String, ForeignKey("folders.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    is_pinned = Column(Boolean, default=False)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    folder = relationship("Folder", back_populates="conversations")
    tags = relationship("Tag", secondary=conversation_tags, back_populates="conversations")
    user = relationship("DBUser", back_populates="conversations")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    
    conversation = relationship("Conversation", back_populates="messages")