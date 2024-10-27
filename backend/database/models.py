from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    conversations = relationship("DBConversation", back_populates="user")

class DBConversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    metadata = Column(JSON)
    user = relationship("DBUser", back_populates="conversations")
    messages = relationship("DBMessage", back_populates="conversation")

class DBMessage(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)
    content = Column(String)
    context = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    conversation = relationship("DBConversation", back_populates="messages")

class DBFile(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    filename = Column(String)
    file_path = Column(String)
    mime_type = Column(String)
    size = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    metadata = Column(JSON)