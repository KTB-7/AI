from fastapi import FastAPI, APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db_connect import get_db_session, get_tag_feature, get_tagplace_interactions, make_frame, get_user_info, get_place_info, get_userplace_interactions, get_top_tags, get_top_tags_vdb
from rc_graph import recommend_cafe
from vdb import get_best_tags

# 장소 추천 라우터
recommendation_router = APIRouter(prefix="/get_recs", tags=["Place Recommendation"])

# 추천 알고리즘 함수
# 장소 추천 요청 및 응답 모델
class Rec_Request(BaseModel):
    user_id: int
    place_ids: List[int]

class Rec_Response_AI(BaseModel):
    cafe_list: List[int]

class Rec_Response_Popular(BaseModel):
    hashtags: List[str]
    cafe_list: List[List[str]]

# 장소 추천 엔드포인트
@recommendation_router.post("/ai", response_model=Rec_Response_AI)
async def get_recommendations(
    request: Rec_Request,
    session: AsyncSession = Depends(get_db_session)
):
    # hashtags = await get_tag_feature(session, request.user_id, request.place_ids)
    # print(f"hashtags : {hashtags}")
    returned_frame = await make_frame(session, request.user_id, request.place_ids)
    print(returned_frame)
    userframe = returned_frame[0]
    placeframe = returned_frame[1]

    userfeature = await get_user_info(session, userframe)
    print(userfeature)
    placefeature = await get_place_info(session, placeframe)
    print(placefeature)
    interactions = await get_userplace_interactions(session, userframe, placeframe)
    print(interactions)
    # print(userframe)
    # print(placeframe)

    users, cafe_list = await recommend_cafe(userfeature, placefeature, interactions, [request.user_id], [request.place_ids])
    
    cafe_list = list(map(int, cafe_list[0]))

    return Rec_Response_AI(cafe_list=cafe_list)

@recommendation_router.post("/popular", response_model=Rec_Response_Popular)
async def get_recommendations(
    request: Rec_Request,
    session: AsyncSession = Depends(get_db_session)
):
    tagfeature = await get_tag_feature(session, request.user_id, request.place_ids)
    print("rec.py tagfeature : ",tagfeature)
    placefeature = await get_place_info(session, request.place_ids)
    print("rec.py placefeature : ", placefeature)
    interactions = await get_tagplace_interactions(session, user_id=request.user_id, place_ids=request.place_ids)
    print("rec.py interactions : ", interactions)

    # 전체
    best_tags = await get_top_tags_vdb(session)
    # 개인화
    # best_tags = await get_top_tags(session, request.user_id)
    place_ids_list = [request.place_ids] * len(best_tags)

    tags, cafe_list = await recommend_cafe(tagfeature, placefeature, interactions, best_tags, place_ids_list)
    print("rec.py tags : ", tags)
    print("rec.py cafe_list : ", cafe_list)

    return Rec_Response_Popular(hashtags=tags, cafe_list=cafe_list)
