from sqlalchemy.orm import Session
from . import models

def create_post(db: Session, user_id: int, content: str):
    post = models.ForumPost(user_id=user_id, content=content)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def get_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ForumPost).order_by(models.ForumPost.created_at.asc()).offset(skip).limit(limit).all()

def create_message(db: Session, user_id: int, content: str):
    message = models.ChatMessage(user_id=user_id, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_messages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ChatMessage).order_by(models.ChatMessage.created_at.asc()).offset(skip).limit(limit).all() 