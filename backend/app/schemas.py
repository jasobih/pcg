from pydantic import BaseModel, Field, computed_field
from datetime import datetime
from typing import List, Optional
from .models import GigType, GigStatus

class GigBase(BaseModel):
    title: str
    gig_type: GigType
    suburb: str
    details: str
    image_url: Optional[str] = None

class GigCreate(GigBase):
    pass

class Gig(GigBase):
    id: int
    status: GigStatus
    report_count: int
    created_at: datetime
    owner_id: int

    @computed_field
    @property
    def owner_username(self) -> str:
        return self.owner.username

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: str
    bio: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    gigs: list[Gig] = []

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    sender_id: int
    gig_id: int

    class Config:
        from_attributes = True

class ReviewBase(BaseModel):
    rating: int
    comment: str

class ReviewCreate(ReviewBase):
    pass

class Review(ReviewBase):
    id: int
    reviewer_id: int
    reviewee_id: int

    class Config:
        from_attributes = True