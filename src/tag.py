from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from pydantic import BaseModel

from lm_graph import graph
from db_connect import add_tags_and_place_tags, get_db_session

# 태그 생성 라우터
tag_router = APIRouter(prefix="/gen_tags", tags=["Tag Generation"])

# 태그 생성 요청 및 응답 모델
class Tag_Request(BaseModel):
    place_id: int
    review_text: str
    review_image_url: Optional[str] = None

class Tag_Response(BaseModel):
    isGened: bool

# 태그 생성 함수
def generate_tags(place_id: int, review_text: str, review_image_url: Optional[str] = None) -> List[str]:
    # LangChain 또는 다른 NLP 모델을 사용하여 태그를 생성합니다.
    # model = SomeLangChainModel()
    # tags = model.generate_tags(review_text)
    
    # 임시로 간단한 예시 태그 반환
    if(review_image_url is not None):
        topic = "VL"
    else:
        topic = "L"

    ret = graph.invoke({"topic": [topic], "image_url": [review_image_url], "review_text": [review_text]})
    
    return ret['tags']

# 태그 생성 엔드포인트
@tag_router.post("/", response_model=Tag_Response)
async def create_tags(request: Tag_Request, session: AsyncSession = Depends(get_db_session)):
    # generate_tags 함수는 주어진 리뷰 텍스트와 이미지 URL로부터 태그 목록을 생성하는 함수라고 가정
    res = generate_tags(
        place_id=request.place_id,
        review_text=request.review_text,
        review_image_url=request.review_image_url
    )
    print(f"Place ID: {request.place_id}")
    print(f"Generated Tags: {res}")  # res는 list[str] 형태

    try:
        # 태그 및 PlaceTag 추가
        place_tags = await add_tags_and_place_tags(session, tag_names=res, place_id=request.place_id)
        print(f"Inserted PlaceTags: {[pt.id for pt in place_tags]}")
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Integrity error: {e.orig}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return Tag_Response(isGened=True)

    return Tag_Response(isGened=True)