from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    posts = relationship('ForumPost', back_populates='user')
    messages = relationship('ChatMessage', back_populates='user')

class ForumPost(Base):
    __tablename__ = 'forum_posts'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='posts')

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='messages')

class LeaderboardScore(Base):
    __tablename__ = 'leaderboard_scores'
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, nullable=False)
    level_name = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    hash = Column(String, nullable=False)
    level_version = Column(Float, nullable=False)
    game_version = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow) 