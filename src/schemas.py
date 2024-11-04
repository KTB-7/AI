# schemas.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Place ORM 모델
class Place(Base):
    __tablename__ = 'Place'
    id = Column(Integer, primary_key=True, autoincrement=True)
    placeId = Column(Integer, nullable=False, unique=True)
    address = Column(String(255))
    x = Column(DECIMAL(10, 7))
    y = Column(DECIMAL(10, 7))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Place_Tag와의 관계 설정
    place_tags = relationship("PlaceTag", back_populates="place", cascade="all, delete-orphan")


# Tag ORM 모델
class Tag(Base):
    __tablename__ = 'Tag'
    tagId = Column(Integer, primary_key=True, autoincrement=True)
    tagName = Column(String(100), nullable=False)
    
    # Place_Tag와의 관계 설정
    place_tags = relationship("PlaceTag", back_populates="tag", cascade="all, delete-orphan")


# Place_Tag ORM 모델
class PlaceTag(Base):
    __tablename__ = 'Place_Tag'
    id = Column(Integer, primary_key=True, autoincrement=True)
    placeId = Column(Integer, ForeignKey('Place.placeId', ondelete='CASCADE'), nullable=False)
    tagId = Column(Integer, ForeignKey('Tag.tagId', ondelete='CASCADE'), nullable=False)
    isRepresentative = Column(Boolean, default=False)
    
    # 관계 설정
    place = relationship("Place", back_populates="place_tags")
    tag = relationship("Tag", back_populates="place_tags")
    
    __table_args__ = (
        UniqueConstraint('placeId', 'tagId', name='uix_place_tag'),
    )
