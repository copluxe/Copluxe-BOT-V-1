from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    videos = relationship("VideoProject", back_populates="owner")


class VideoProject(Base):
    __tablename__ = "video_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    image_paths = Column(JSON, default=list)
    output_path = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)  # seconds
    style_settings = Column(JSON, default=dict)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="videos")
