from fastapi import FastAPI, APIRouter
from typing import List, Optional
from pydantic import BaseModel

# 태그 생성 라우터
tag_router = APIRouter(prefix="/gen_tags", tags=["Tag Generation"])

# 태그 생성 요청 및 응답 모델
class Tag_Request(BaseModel):
    review_text: str
    review_image_url: Optional[str] = None

class Tag_Response(BaseModel):
    isGened: bool

# 태그 생성 함수
def generate_tags(review_text: str, review_image_url: Optional[str] = None) -> List[str]:
    # LangChain 또는 다른 NLP 모델을 사용하여 태그를 생성합니다.
    # model = SomeLangChainModel()
    # tags = model.generate_tags(review_text)
    
    # 임시로 간단한 예시 태그 반환
    return True

# 태그 생성 엔드포인트
@tag_router.post("/", response_model=Tag_Response)
async def create_tags(request: Tag_Request):
    res = generate_tags(
        review_text=request.review_text,
        review_image_url=request.review_image_url
    )
    return Tag_Response(isGened=res)