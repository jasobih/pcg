
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class GigType(str, enum.Enum):
    ODD_JOB = "ODD_JOB"
    MARKET_SPOT = "MARKET_SPOT"

class GigStatus(str, enum.Enum):
    LIVE = "LIVE"
    FLAGGED = "FLAGGED"
    DELETED = "DELETED"
    COMPLETED = "COMPLETED"

class Gig(Base):
    __tablename__ = "gigs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    gig_type = Column(SAEnum(GigType))
    suburb = Column(String)
    details = Column(String)
    image_url = Column(String, nullable=True)
    status = Column(SAEnum(GigStatus), default=GigStatus.LIVE)
    report_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="gigs")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    bio = Column(String, nullable=True)
    hashed_password = Column(String)

    gigs = relationship("Gig", back_populates="owner")
    messages = relationship("Message", back_populates="sender")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    gig_id = Column(Integer, ForeignKey("gigs.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))

    gig = relationship("Gig")
    sender = relationship("User", back_populates="messages")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer)
    comment = Column(String)
    gig_id = Column(Integer, ForeignKey("gigs.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    reviewee_id = Column(Integer, ForeignKey("users.id"))

    gig = relationship("Gig")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    reviewee = relationship("User", foreign_keys=[reviewee_id])
