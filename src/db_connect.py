# db_connect.py

import asyncio
import datetime
import pandas as pd
import logging
from collections import defaultdict
from typing import List, Tuple, Union
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from schemas import Place, Tag, User, PlaceTag, PlaceVisit, UserPlaceTag, UserMenu, UserActivity
from vdb import get_tag_sentiment, get_best_tags

# # 개별 로거 생성
# logger = logging.getLogger('db_connect')
# logger.setLevel(logging.WARNING)

# # FileHandler 생성 및 설정
# file_handler = logging.FileHandler('db_connect_operations.log')
# file_handler.setLevel(logging.WARNING)

# # 로그 포맷 설정
# formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# file_handler.setFormatter(formatter)

# # 핸들러가 이미 추가되지 않았다면 추가
# if not logger.hasHandlers():
#     logger.addHandler(file_handler)

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
            # logger.info(f"Inserted Tag: id={tag.id}, tagName={tag.tagName}, createdAt={tag.createdAt}, updatedAt={tag.updatedAt}")        
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
    # else:
    #     logger.info(f"Retrieved existing Tag: id={tag.id}, tagName={tag.tagName}, createdAt={tag.createdAt}, updatedAt={tag.updatedAt}")
    return tag

async def add_visit(
    session: AsyncSession,
    place_id: int,
    user_id: int
) -> PlaceVisit:
    """
    주어진 place_id와 age를 사용하여 placeVisit 테이블을 업데이트하거나 새 레코드를 생성합니다.

    :param session: 활성화된 AsyncSession.
    :param place_id: 장소의 ID (Place.id).
    :param age: 방문자의 나이.
    :return: 추가 또는 업데이트된 PlaceVisit 객체.
    :raises IntegrityError: 외래 키 제약 조건 위반 등.
    """
    try:
        # 기존 PlaceVisit 레코드 조회
        tmp = await session.execute(
            select(User).where(User.id == user_id)
        )
        age = tmp.scalars().first().age
        
        result = await session.execute(
            select(PlaceVisit).where(PlaceVisit.placeId == place_id)
        )
        place_visit = result.scalars().first()
        # print("\n\n place_visit \n\n", place_visit.age, place_visit.visit)

        if place_visit:
            # 기존 방문 정보 업데이트
            total_age = place_visit.age * place_visit.visit
            place_visit.visit += 1
            place_visit.age = (total_age + age) / place_visit.visit
            # logger.info(f"Updated PlaceVisit for place_id={place_id}: visit={place_visit.visit}, age={place_visit.age}")
        else:
            # 새로운 PlaceVisit 레코드 생성
            place_visit = PlaceVisit(placeId=place_id, visit=1, age=age)
            session.add(place_visit)
            # logger.info(f"Created new PlaceVisit for place_id={place_id}: visit=1, age={age}")

        return place_visit

    except IntegrityError as e:
        logger.error(f"IntegrityError for place_id {place_id}: {e.orig}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error for place_id {place_id}: {e}")
        raise e

async def add_place_tag(
    session: AsyncSession, 
    place_id: int, 
    tag_id: int, 
    is_representative: bool
) -> PlaceTag:
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
            # logger.info(f"Updated PlaceTag: placeId={existing_place_tag.placeId}, tagId={existing_place_tag.tagId}, tagCount={existing_place_tag.tagCount}")            
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
            # logger.info(f"Inserted PlaceTag: placeId={new_place_tag.placeId}, tagId={new_place_tag.tagId}, tagCount={new_place_tag.tagCount}")            
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
            # logger.info(f"Set isRepresentative=True for top tags: {top_tag_ids}")
        
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

async def add_tags_and_place_tags(
    session: AsyncSession, 
    tag_names: list[str], 
    place_id: int,
    user_id : int
) -> list[PlaceTag]:
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
        # PlaceVisit 에 추가
        place_visit = await add_visit(session, place_id, user_id)
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

async def add_user_tags(
    session: AsyncSession, 
    user_id: int,
    place_id: int,
    tag_names: list[str]
) -> list[UserPlaceTag]:
    new_user_tags = []
    for tag_name in tag_names:
        try:
            tag = await get_or_create_tag(session, tag_name)
            stmt = select(UserPlaceTag).where(
                UserPlaceTag.userId == user_id,
                UserPlaceTag.tagId == tag.id
            )
            result = await session.execute(stmt)
            existing_user_tag = result.scalar_one_or_none()
            if existing_user_tag:
                # logger.info(f"Updated UserPlaceTag: userId={existing_user_tag.userId}, placeId={existing_user_tag.placeId}, tagId={existing_user_tag.tagId}")
                new_user_tags.append(existing_user_tag)
            else:
                new_user_tag = UserPlaceTag(userId=user_id, placeId=place_id ,tagId=tag.id)
                session.add(new_user_tag)
                await session.flush()
                await session.commit()
                # logger.info(f"Inserted UserPlaceTag: userId={new_user_tag.userId}, placeId={new_user_tag.placeId}, tagId={new_user_tag.tagId}")
                new_user_tags.append(new_user_tag)
        except IntegrityError as e:
            logger.error(f"IntegrityError for userplacetag '{tag_name}' and user_id {user_id}: {e.orig}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error for userplacetag '{tag_name}' and user_id {user_id}: {e}")
            raise e
    return new_user_tags

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

async def get_top_tags_vdb(
    session: AsyncSession
) -> List[Union[int, str]]:
    stmt = select(Tag.id).where(Tag.tagName.in_(get_best_tags()))
    result = await session.execute(stmt)
    top_tags = result.scalars().all()

    return top_tags

async def get_top_tags(
    session: AsyncSession, 
    user_id: int
) -> List[Union[int, str]]:
    subquery = (
        select(
            UserPlaceTag.tagId,
            func.count(UserPlaceTag.tagId).label('tag_count')
        )
        .where(UserPlaceTag.userId == user_id)
        .group_by(UserPlaceTag.tagId)
        .subquery()
    )

    stmt = (
        select(subquery.c.tagId)
        .order_by(subquery.c.tag_count.desc())
        .limit(10)
    )

    result = await session.execute(stmt)
    top_tags = result.scalars().all()
    print("top tags", top_tags)

    return top_tags

async def get_tag_feature(
    session: AsyncSession,
    user_id: int,
    place_ids: List[int]
) -> List[Union[int, str]]:
    stmt_usertag = select(UserPlaceTag.tagId).where(UserPlaceTag.userId == user_id)
    stmt_placetag = select(PlaceTag.tagId).where(
        PlaceTag.placeId.in_(place_ids),
        PlaceTag.isRepresentative == True
    )
    stmt_besttag = select(Tag.id).where(Tag.tagName.in_(get_best_tags()))
    
    usertag_result = await session.execute(stmt_usertag)
    placetag_result = await session.execute(stmt_placetag)
    besttag_result = await session.execute(stmt_besttag)
    
    combined_tags = list(set(usertag_result.scalars().all()) | set(placetag_result.scalars().all()) | set(besttag_result.scalars().all()))
    print("combined tags",combined_tags)
    stmt_taguser = select(UserPlaceTag.tagId, UserPlaceTag.userId).where(UserPlaceTag.tagId.in_(combined_tags))
    taguser_result = await session.execute(stmt_taguser)

    rows = taguser_result.fetchall()
    rows = sorted(rows, key=lambda x: x[0])
    print("taguser result", rows)

    return rows

async def get_tagplace_interactions(
    session: AsyncSession,
    user_id: int,
    place_ids: List[int]
) -> List[Union[int, str]]:
    stmt_score = select(UserPlaceTag.tagId, UserPlaceTag.placeId, UserPlaceTag.userId).where(
        UserPlaceTag.userId == user_id,
        UserPlaceTag.placeId.in_(place_ids)
    )
    res_score = await session.execute(stmt_score)
    score = res_score.fetchall()

    count_sum = defaultdict(int)
    for tag_id, place_id, user_id in score:
        count_sum[(tag_id, place_id)] += 1

    summed_score = []
    for (tag_id, place_id), count in count_sum.items():
        summed_score.append([tag_id, place_id, count])

    return summed_score        

async def make_frame(
    session: AsyncSession,
    user_id: int,
    place_ids: List[int]
) -> Tuple[List[int], List[Union[int, str]]]:
    print(user_id, place_ids)
    stmt_userframe = select(UserPlaceTag.userId).where(UserPlaceTag.placeId.in_(place_ids)).distinct()
    res_userframe = await session.execute(stmt_userframe)
    user_list = res_userframe.scalars().all()
    print("user_list", user_list)
    stmt_placeframe = select(UserPlaceTag.placeId).where(UserPlaceTag.userId.in_(user_list)).distinct()
    res_placeframe = await session.execute(stmt_placeframe)
    place_list = res_placeframe.scalars().all()
    print("place_list", place_list)
    return user_list, place_list

async def get_user_info(
    session: AsyncSession,
    user_ids: List[int]
) -> List[Union[int, str]]:
    stmt_userage = select(User.id, User.age).where(User.id.in_(user_ids))
    stmt_usermenu = select(UserMenu.userId, UserMenu.menuName).where(UserMenu.userId.in_(user_ids))
    stmt_useractivity = select(UserActivity.userId, UserActivity.activityName).where(UserActivity.userId.in_(user_ids))

    userage_result = await session.execute(stmt_userage)
    usermenu_result = await session.execute(stmt_usermenu)
    useractivity_result = await session.execute(stmt_useractivity)

    userage = userage_result.fetchall()
    usermenu = usermenu_result.fetchall()
    useractivity = useractivity_result.fetchall()
    print("userage", userage)
    print("usermenu", usermenu)
    print("useractivity", useractivity)
    userfeature = userage + usermenu + useractivity

    return userfeature

async def get_place_info(
    session: AsyncSession,
    place_ids: List[int]
) -> List[Union[int, str]]:
    stmt_placereptag = select(PlaceTag.placeId, PlaceTag.tagId).where(PlaceTag.placeId.in_(place_ids), PlaceTag.isRepresentative == True)
    ### tagid로 feature를 비교해도 되지 않을까? 시각적으로 로그 확인하기에는 tagname이 좋겠지만, db query 시간 줄여보자.
    stmt_placeavgage = select(PlaceVisit.placeId, PlaceVisit.age).where(PlaceVisit.placeId.in_(place_ids))

    placereptag_result = await session.execute(stmt_placereptag)
    placeavgage_result = await session.execute(stmt_placeavgage)

    placereptag = placereptag_result.fetchall()
    placeavgage = placeavgage_result.fetchall()
    placeavgage = [(place_id, round(age, 1)) for place_id, age in placeavgage]

    print("placereptag", placereptag)
    print("placeavgage", placeavgage)

    placefeature = placereptag + placeavgage

    return placefeature

async def get_userplace_interactions(
    session: AsyncSession,
    user_ids: List[int],
    place_ids: List[int]
) -> List[Union[int, str]]:
    stmt_tagsentiment = select(UserPlaceTag.tagId).where(
        UserPlaceTag.userId.in_(user_ids),
        UserPlaceTag.placeId.in_(place_ids)
    ).distinct()
    tagsentiment_result = await session.execute(stmt_tagsentiment)
    tagsentiment = tagsentiment_result.scalars().all()
    sentiment_map = get_tag_sentiment(tagsentiment)
    print("sentiment_map", sentiment_map)
    
    stmt_interactions = select(UserPlaceTag.userId, UserPlaceTag.placeId, UserPlaceTag.tagId).where(
        UserPlaceTag.userId.in_(user_ids),
        UserPlaceTag.placeId.in_(place_ids)
    )
    interactions_result = await session.execute(stmt_interactions)
    interactions = interactions_result.fetchall()
    print("interactions", interactions)
    
    processed_interactions = []
    for user_id, place_id, tag_id in interactions:
        print("interaction to map",user_id, place_id, tag_id, sentiment_map.get(tag_id))
        processed_interactions.append([user_id, place_id, sentiment_map.get(tag_id, 0)])  # 기본값 0 설정
    
    sentiment_sum = defaultdict(float)
    sentiment_count = defaultdict(int)
    
    for user_id, place_id, sentiment in processed_interactions:
        key = (user_id, place_id)
        sentiment_sum[key] += sentiment
        sentiment_count[key] += 1
    
    averaged_interactions = [
        (user_id, place_id, sentiment_sum[key])# round(sentiment_sum[key] / sentiment_count[key], 3))
        for key, user_id, place_id in [
            (key, key[0], key[1]) for key in sentiment_sum
        ]
    ]
    
    print("averaged_interactions", averaged_interactions)
    
    
    return averaged_interactions

if __name__ == "__main__":
    asyncio.run(main())