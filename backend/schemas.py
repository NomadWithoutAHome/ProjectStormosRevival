from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    class Config:
        orm_mode = True

class ForumPostBase(BaseModel):
    content: str

class ForumPostCreate(ForumPostBase):
    pass

class ForumPostRead(ForumPostBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        orm_mode = True

class ChatMessageBase(BaseModel):
    content: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageRead(ChatMessageBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        orm_mode = True 