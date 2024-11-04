# db_connect.py

import asyncio
import datetime
import pandas as pd  # Pandas 임포트 추가
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL, Boolean, UniqueConstraint
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.future import select

from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from schemas import Place, Tag, PlaceTag  # Users, UserTags 제거

# Database connection details
user = MYSQL_USER
password = MYSQL_PASSWORD
host = MYSQL_HOST
port = MYSQL_PORT
database_name = MYSQL_DATABASE

# MySQL용 데이터베이스 URL 설정 (aiomysql 드라이버 사용)
DATABASE_URL = f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database_name}"

# Create asynchronous engine
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Create asynchronous session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

# Dependency to get DB session
async def get_db_session() -> AsyncSession:  # type: ignore
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# *** 추가된 함수: 최근 60일 이내의 placeId, tagId를 DataFrame으로 반환 ***
async def get_recent_place_tags_dataframe(session: AsyncSession) -> pd.DataFrame:
    # two_months_ago = datetime.datetime.now() - datetime.timedelta(days=60)
    # 필요한 컬럼만 선택
    # stmt = select(PlaceTag.placeId, PlaceTag.tagId, PlaceTag.isRepresentative, PlaceTag.id, PlaceTag.createdAt).where(
    #     PlaceTag.createdAt >= two_months_ago
    # )
    stmt = select(PlaceTag.placeId, PlaceTag.tagId, PlaceTag.isRepresentative, PlaceTag.id)
    result = await session.execute(stmt)
    data = result.fetchall()  # List of Row objects

    # DataFrame 생성
    df = pd.DataFrame(data, columns=['placeId', 'tagId', 'isRepresentative', 'id'])
    
    return df

# 테스트 함수
async def test_dataframe():
    async with AsyncSessionLocal() as session:
        df = await get_recent_place_tags_dataframe(session)
        print(df)

if __name__ == "__main__":
    asyncio.run(test_dataframe())
