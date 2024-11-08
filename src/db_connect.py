# db_connect.py

import asyncio
import datetime
import pandas as pd  # Pandas 임포트 추가
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from schemas import Place, Tag, PlaceTag 

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
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def get_or_create_tag(session: AsyncSession, tag_name: str) -> Tag:
    """
    주어진 태그 이름으로 Tag 객체를 가져오거나, 존재하지 않으면 새로 생성합니다.

    :param session: 활성화된 AsyncSession.
    :param tag_name: 태그 이름.
    :return: 존재하는 Tag 객체 또는 새로 생성된 Tag 객체.
    """
    stmt = select(Tag).where(Tag.tagName == tag_name)
    result = await session.execute(stmt)
    tag = result.scalar_one_or_none()
    if tag is None:
        tag = Tag(tagName=tag_name)
        session.add(tag)
        try:
            await session.flush()  # 데이터베이스에 반영
        except IntegrityError as e:
            await session.rollback()
            print(f"IntegrityError while creating tag '{tag_name}': {e.orig}")
            raise e
        except Exception as e:
            await session.rollback()
            print(f"Unexpected error while creating tag '{tag_name}': {e}")
            raise e
    return tag

async def add_place_tag(session: AsyncSession, place_id: int, tag_id: int, is_representative: bool) -> PlaceTag:
    """
    Inserts a new record into the Place_Tag table.

    :param session: The active AsyncSession.
    :param place_id: The identifier of the place (Place.id).
    :param tag_id: The identifier of the tag (Tag.id).
    :param is_representative: Boolean indicating if the tag is representative for the place.
    :return: The PlaceTag object that was inserted.
    :raises IntegrityError: If the combination of place_id and tag_id violates the unique constraint or other integrity constraints are violated.
    """
    new_place_tag = PlaceTag(placeId=place_id, tagId=tag_id, isRepresentative=is_representative)
    session.add(new_place_tag)
    try:
        await session.flush()  # 트랜잭션 내에서 변경 사항을 데이터베이스에 반영
        return new_place_tag
    except IntegrityError as e:
        await session.rollback()
        print(f"IntegrityError: {e.orig}")
        raise e
    except Exception as e:
        await session.rollback()
        print(f"Error inserting place_tag: {e}")
        raise e

async def get_recent_place_tags_dataframe(session: AsyncSession) -> pd.DataFrame:
    # 필요한 컬럼만 선택
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

async def add_tags_and_place_tags(session: AsyncSession, tag_names: list[str], place_id: int) -> list[PlaceTag]:
    """
    주어진 태그 이름 목록과 장소 ID를 사용하여 Tag와 PlaceTag 레코드를 추가합니다.

    :param session: 활성화된 AsyncSession.
    :param tag_names: 태그 이름의 리스트.
    :param place_id: 장소의 ID (Place.id).
    :return: 추가된 PlaceTag 객체들의 리스트.
    :raises IntegrityError: 외래 키 제약 조건 위반 등.
    """
    place_tags = []
    async with session.begin():  # 트랜잭션 시작
        for tag_name in tag_names:
            try:
                # 태그 가져오기 또는 생성
                tag = await get_or_create_tag(session, tag_name)
                
                # PlaceTag 추가
                place_tag = await add_place_tag(
                    session=session,
                    place_id=place_id,
                    tag_id=tag.id,
                    is_representative=False  # 필요에 따라 변경 가능
                )
                place_tags.append(place_tag)
            except IntegrityError as e:
                print(f"IntegrityError for tag '{tag_name}' and place_id {place_id}: {e.orig}")
                # 필요에 따라 예외를 다시 던지거나 계속 진행
                raise e
            except Exception as e:
                print(f"Unexpected error for tag '{tag_name}' and place_id {place_id}: {e}")
                raise e
    return place_tags


async def main():
    async with AsyncSessionLocal() as session:
        try:
            place_tag = await add_tags_and_place_tags(session, tagName="test", place_id=3, is_representative=False)
            print(f"Inserted PlaceTag: PlaceID={place_tag.placeId}, TagID={place_tag.tagId}, IsRepresentative={place_tag.isRepresentative}")
        except IntegrityError as e:
            print(f"IntegrityError occurred: {e.orig}")
        except ValueError as ve:
            print(f"ValueError: {ve}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    # 엔진 종료(dispose) 추가
    await async_engine.dispose()

if __name__ == "__main__":
    # To test the dataframe function, uncomment the line below:
    # asyncio.run(test_dataframe())
    
    # To test adding a tag and place_tag, run the main function
    asyncio.run(main())