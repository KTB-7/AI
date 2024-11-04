from fastapi import FastAPI, APIRouter
from typing import List, Optional
from pydantic import BaseModel

# 장소 추천 라우터
recommendation_router = APIRouter(prefix="/get_recs", tags=["Place Recommendation"])

# 추천 알고리즘 함수
# 장소 추천 요청 및 응답 모델
class Rec_Request(BaseModel):
    user_id: int

class Rec_Response(BaseModel):
    place_ids: List[int]


def recommend_places(user_id: int) -> List[int]:
    # 추천 알고리즘을 사용하여 장소 ID를 생성합니다.
    
    # 임시로 간단한 예시 장소 ID 반환
    return [101, 102, 103]

# 장소 추천 엔드포인트
@recommendation_router.post("/", response_model=Rec_Response)
async def get_recommendations(request: Rec_Request):
    place_ids = recommend_places(user_id=request.user_id)
    return Rec_Response(place_ids=place_ids)
