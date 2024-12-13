# schemas.py

from sqlalchemy import Column, BigInteger, Integer, Float, ForeignKey, String, DateTime, Boolean, UniqueConstraint, func
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

    # placeVisit과의 관계 설정
    place_visits = relationship("PlaceVisit", back_populates="place", cascade="all, delete-orphan")


# Tag ORM 모델
class Tag(Base):
    __tablename__ = 'Tag'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tagName = Column(String(255), unique=True, nullable=True)
    createdAt = Column(DateTime, nullable=False)
    updatedAt = Column(DateTime, nullable=False)
    
    # Place_Tag와의 관계 설정
    place_tags = relationship("PlaceTag", back_populates="tag", cascade="all, delete-orphan")

    # Tag와 UserTag 간의 관계 설정
    user_tags = relationship("UserTag", back_populates="tag", cascade="all, delete-orphan")


# Place_Tag ORM 모델
class PlaceTag(Base):
    __tablename__ = 'placeTag'
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

class PlaceVisit(Base):
    __tablename__ = 'placeVisit'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    placeId = Column(BigInteger, ForeignKey('Place.id'), nullable=False)
    visit = Column(Integer, nullable=False)
    age = Column(Float, nullable=False)

    # Place와의 관계 설정
    place = relationship("Place", back_populates="place_visits")

class User(Base):
    __tablename__ = 'User'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    userEmail = Column(String(255), unique=True, nullable=False)
    userName = Column(String(255), nullable=False)
    socialId = Column(String(255), nullable=True)
    profileImageId = Column(BigInteger, nullable=True)
    createdAt = Column(DateTime, server_default=func.now(), nullable=False)
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # User와 UserTag 간의 관계 설정
    user_tags = relationship("UserTag", back_populates="user", cascade="all, delete-orphan")

class UserTag(Base):
    __tablename__ = 'userTag'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    userId = Column(BigInteger, ForeignKey('User.id', ondelete='CASCADE'), nullable=False)
    tagId = Column(BigInteger, ForeignKey('Tag.id', ondelete='CASCADE'), nullable=False)
    tagCount = Column(Integer, nullable=False, default=0)
    
    # UserTag와 User 간의 관계 설정
    user = relationship("User", back_populates="user_tags")
    
    # UserTag와 Tag 간의 관계 설정
    tag = relationship("Tag", back_populates="user_tags")