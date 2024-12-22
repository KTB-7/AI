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
    
    place_tags = relationship("PlaceTag", back_populates="place", cascade="all, delete-orphan")
    place_visits = relationship("PlaceVisit", back_populates="place", cascade="all, delete-orphan")
    user_place_tags = relationship("UserPlaceTag", back_populates="place", cascade="all, delete-orphan")


# Tag ORM 모델
class Tag(Base):
    __tablename__ = 'Tag'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tagName = Column(String(255), unique=True, nullable=True)
    createdAt = Column(DateTime, nullable=False)
    updatedAt = Column(DateTime, nullable=False)
    
    place_tags = relationship("PlaceTag", back_populates="tag", cascade="all, delete-orphan")
    user_place_tags = relationship("UserPlaceTag", back_populates="tag", cascade="all, delete-orphan")


# Place_Tag ORM 모델
class PlaceTag(Base):
    __tablename__ = 'placeTag'
    __table_args__ = (
        UniqueConstraint('placeId', 'tagId', name='uix_place_tag'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    placeId = Column(BigInteger, ForeignKey('Place.id', ondelete='CASCADE'), nullable=False)
    tagId = Column(BigInteger, ForeignKey('Tag.id', ondelete='CASCADE'), nullable=False)
    tagCount = Column(BigInteger, default=1, nullable=False)
    isRepresentative = Column(Boolean, default=False)
    
    # 관계 설정
    place = relationship("Place", back_populates="place_tags")
    tag = relationship("Tag", back_populates="place_tags")

class PlaceVisit(Base):
    __tablename__ = 'placeVisit'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    placeId = Column(BigInteger, ForeignKey('Place.id'), nullable=False)
    visit = Column(Integer, nullable=False)
    age = Column(Float, nullable=False, default=0.0)

    # Place와의 관계 설정
    place = relationship("Place", back_populates="place_visits")

class User(Base):
    __tablename__ = 'User'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    userEmail = Column(String(255), unique=True, nullable=False)
    userName = Column(String(255), nullable=False)
    socialId = Column(String(255), nullable=True)
    profileImageId = Column(BigInteger, nullable=True)
    age = Column(Integer, nullable=True)
    createdAt = Column(DateTime, server_default=func.now(), nullable=False)
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user_place_tags = relationship("UserPlaceTag", back_populates="user", cascade="all, delete-orphan")
    user_menus = relationship("UserMenu", back_populates="user", cascade="all, delete-orphan")
    user_activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")


class UserPlaceTag(Base):
    __tablename__ = 'userPlaceTag'
    __table_args__ = (
        UniqueConstraint('userId', 'placeId', 'tagId', name='uix_user_place_tag'),
    )
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    userId = Column(BigInteger, ForeignKey('User.id', ondelete='CASCADE'), nullable=False)
    placeId = Column(BigInteger, ForeignKey('Place.id', ondelete='CASCADE'), nullable=False)
    tagId = Column(BigInteger, ForeignKey('Tag.id', ondelete='CASCADE'), nullable=False)
    
    user = relationship("User", back_populates="user_place_tags")
    place = relationship("Place", back_populates="user_place_tags")
    tag = relationship("Tag", back_populates="user_place_tags")


class UserMenu(Base):
    __tablename__ = 'UserMenu'
    
    userId = Column(BigInteger, ForeignKey('User.id'), primary_key=True)
    menuName = Column(String(100), primary_key=True)
    
    user = relationship("User", back_populates="user_menus")

class UserActivity(Base):
    __tablename__ = 'UserActivity'
    
    userId = Column(BigInteger, ForeignKey('User.id'), primary_key=True)
    activityName = Column(String(100), primary_key=True)
    
    user = relationship("User", back_populates="user_activities")