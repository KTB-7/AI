# db_connect.py

import asyncio
import datetime
import pandas as pd  # Pandas 임포트 추가
import logging
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from schemas import Place, Tag, PlaceTag 

# logging
logging.basicConfig(
    filename='db_operations.log',  # 로그 파일 이름
    level=logging.INFO,  # 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s %(levelname)s:%(name)s:%(message)s',  # 로그 메시지 형식
    datefmt='%Y-%m-%d %H:%M:%S'  # 날짜 형식
)

# logger obj create
logger = logging.getLogger(__name__)

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
async def get_db_session() -> AsyncSession: # type: ignore
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
        tag = Tag(tagName=tag_name, createdAt=datetime.datetime.now(), updatedAt=datetime.datetime.now())
        session.add(tag)
        try:
            await session.flush()  # 데이터베이스에 반영
            # print(f"Inserted Tag: id={tag.id}, tagName={tag.tagName}, createdAt={tag.createdAt}, updatedAt={tag.updatedAt}")
            logger.info(f"Inserted Tag: id={tag.id}, tagName={tag.tagName}, createdAt={tag.createdAt}, updatedAt={tag.updatedAt}")        
        except IntegrityError as e:
            await session.rollback()
            # print(f"IntegrityError while creating tag '{tag_name}': {e.orig}")
            logger.error(f"IntegrityError while creating tag '{tag_name}': {e.orig}")            
            raise e
        except Exception as e:
            await session.rollback()
            # print(f"Unexpected error while creating tag '{tag_name}': {e}")
            logger.error(f"Unexpected error while creating tag '{tag_name}': {e}")            
            raise e
    else:
        logger.info(f"Retrieved existing Tag: id={tag.id}, tagName={tag.tagName}, createdAt={tag.createdAt}, updatedAt={tag.updatedAt}")
    return tag

async def add_place_tag(session: AsyncSession, place_id: int, tag_id: int, is_representative: bool) -> PlaceTag:
    """
    Inserts a new record into the Place_Tag table. Additionally, updates the isRepresentative
    field for the top 5 tags with the highest tagCount for the given place_id.

    :param session: The active AsyncSession.
    :param place_id: The identifier of the place (Place.id).
    :param tag_id: The identifier of the tag (Tag.id).
    :param is_representative: Boolean indicating if the tag is representative for the place.
    :return: The PlaceTag object that was inserted or updated.
    :raises IntegrityError: If the combination of place_id and tag_id violates the unique constraint or other integrity constraints are violated.
    """
    try:
        # 동일한 placeId와 tagId를 가진 PlaceTag가 존재하는지 확인
        stmt = select(PlaceTag).where(
            PlaceTag.placeId == place_id,
            PlaceTag.tagId == tag_id
        )
        result = await session.execute(stmt)
        existing_place_tag = result.scalar_one_or_none()
        
        if existing_place_tag:
            # 기존 PlaceTag가 존재하면 tagCount를 1 증가시킴
            existing_place_tag.tagCount += 1
            await session.flush()
            logger.info(f"Updated PlaceTag: placeId={existing_place_tag.placeId}, tagId={existing_place_tag.tagId}, tagCount={existing_place_tag.tagCount}")            
            place_tag = existing_place_tag
        else:
            # 새로운 PlaceTag를 생성하고 삽입함
            new_place_tag = PlaceTag(
                placeId=place_id,
                tagId=tag_id,
                tagCount=1,  # 기본값으로 설정
                isRepresentative=is_representative  # 현재는 사용하지 않음
            )
            session.add(new_place_tag)
            await session.flush()
            logger.info(f"Inserted PlaceTag: placeId={new_place_tag.placeId}, tagId={new_place_tag.tagId}, tagCount={new_place_tag.tagCount}")            
            place_tag = new_place_tag

        # 상위 5개 태그를 대표 태그로 설정
        # 1. 상위 5개 태그 조회
        top_tags_stmt = select(PlaceTag).where(
            PlaceTag.placeId == place_id
        ).order_by(PlaceTag.tagCount.desc()).limit(5)
        top_tags_result = await session.execute(top_tags_stmt)
        top_tags = top_tags_result.scalars().all()

        # 2. 상위 5개 태그의 tagId를 추출
        top_tag_ids = {tag.tagId for tag in top_tags}

        # 3. 모든 태그의 isRepresentative를 False로 설정
        reset_stmt = update(PlaceTag).where(
            PlaceTag.placeId == place_id
        ).values(isRepresentative=False)
        await session.execute(reset_stmt)

        # 4. 상위 5개 태그의 isRepresentative를 True로 설정
        if top_tag_ids:
            set_representative_stmt = update(PlaceTag).where(
                PlaceTag.placeId == place_id,
                PlaceTag.tagId.in_(top_tag_ids)
            ).values(isRepresentative=True)
            await session.execute(set_representative_stmt)
            logger.info(f"Set isRepresentative=True for top tags: {top_tag_ids}")
        
        # Commit은 함수 외부에서 처리하도록 함
        return place_tag

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e.orig}")
        raise e
    except Exception as e:
        await session.rollback()
        logger.error(f"Error inserting/updating place_tag: {e}")
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
                # print(f"IntegrityError for tag '{tag_name}' and place_id {place_id}: {e.orig}")
                logger.error(f"IntegrityError for tag '{tag_name}' and place_id {place_id}: {e.orig}")
                raise e
            except Exception as e:
                # print(f"Unexpected error for tag '{tag_name}' and place_id {place_id}: {e}")
                logger.error(f"Unexpected error for tag '{tag_name}' and place_id {place_id}: {e}")
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