# schemas.py

from sqlalchemy import Column, BigInteger, ForeignKey, String, DateTime, Boolean, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Place ORM 모델
class Place(Base):
    __tablename__ = 'Place'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    placeId = Column(String(255), unique=True, nullable=True)
    placeName = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    x = Column(String(255), nullable=True)
    y = Column(String(255), nullable=True)
    createdAt = Column(DateTime, server_default=func.now(), nullable=False)
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Place_Tag와의 관계 설정
    place_tags = relationship("PlaceTag", back_populates="place", cascade="all, delete-orphan")


# Tag ORM 모델
class Tag(Base):
    __tablename__ = 'Tag'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tagName = Column(String(255), unique=True, nullable=True)
    createdAt = Column(DateTime, nullable=False)
    updatedAt = Column(DateTime, nullable=False)
    
    # Place_Tag와의 관계 설정
    place_tags = relationship("PlaceTag", back_populates="tag", cascade="all, delete-orphan")


# Place_Tag ORM 모델
class PlaceTag(Base):
    __tablename__ = 'PlaceTag'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    placeId = Column(BigInteger, ForeignKey('Place.id', ondelete='CASCADE'), nullable=False)
    tagId = Column(BigInteger, ForeignKey('Tag.id', ondelete='CASCADE'), nullable=False)
    tagCount = Column(BigInteger, default=1, nullable=False)
    isRepresentative = Column(Boolean, default=False)
    
    # 관계 설정
    place = relationship("Place", back_populates="place_tags")
    tag = relationship("Tag", back_populates="place_tags")
    
    __table_args__ = (
        UniqueConstraint('placeId', 'tagId', name='uix_place_tag'),
    )
