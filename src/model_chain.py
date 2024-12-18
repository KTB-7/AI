from pydantic import BaseModel
import os
from config import OPENAI_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_KEY

import openai
from openai import OpenAI, AsyncOpenAI
# cli = OpenAI()
cli = AsyncOpenAI()

import base64
import json
import urllib.parse

from s3image import encode_image_from_s3

class Tag_Response(BaseModel):
    tags: list[str]

class Tag_Score_Response(BaseModel):
    positive_tags: list[str]
    neutral_tags: list[str]
    negative_tags: list[str]

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def extract_review_hashtags(review_text):
    try:    
        completion = await cli.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                        텍스트는 카페에 대해서 사용자가 남긴 리뷰야. 해당 리뷰를 분석하여 각 리뷰에서 3개에서 5개의 주요 특징을 뽑아 해시태그로 만들어줘. 해시태그는 리뷰에서 중요한 키워드, 감정(긍정적/부정적), 서비스의 질 등을 반영하여 작성해줘. 
                        주의사항
                        1. 해시태그를 출력할 때 가게 이름(ex. 스타벅스, 블루보틀)은 들어가지 않게 해줘.
                        2. 메뉴 이름은 그 자체로 명사로 뽑아내줘.
                        3. 만약 형용사/부사와 명사가 같이 나온다면 형용사/부사 + 명사 순으로 뽑아내줘. (ex. 친절한 서비스, 불친절한 직원, )
                        출력방식은 다른 부가 설명 없이 깔끔하게 다음과 같아:
                        4. 띄어쓰기가 필요한 부분은 띄어쓰기 해줘.
                        5. 리뷰에 있는 단어만 추출해줘.
                        6. 메뉴와 관련된 문장이 있으면 메뉴이름 + 특징 으로 뽑아줘. (ex. 밀크 크레이프 케익은 빌리엔젤이 최고! -> 밀크 크레이프 케익 최고)
                        
                        리뷰: {review_text}                    
                    """
                }
            ],
            response_format=Tag_Score_Response
        )
        res = json.loads(completion.choices[0].message.content)
        return res
    except openai.APIError as e:
        print(f"OpenAI API 호출 실패: {e}")
        return {'positive_tags': [], 'neutral_tags': [], 'negative_tags': []}

async def extract_image_hashtags(image_path):
    parsed_path = urllib.parse.urlparse(image_path)
    path = parsed_path.path.lstrip('/')
    base64_image = await encode_image_from_s3(path)
    try:
        completion = await cli.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
                            텍스트는 카페에 대해서 사용자가 남긴 이미지야. 해당 리뷰를 분석하여 각 리뷰에서 3개에서 5개의 주요 특징을 뽑아 해시태그로 만들어줘. 
                            주의사항
                            1. 해시태그를 출력할 때 가게 이름(ex. 스타벅스, 블루보틀)이나 카페 는 들어가지 않아야해.
                            2. 이미지에서 확인할 수 있는 것만 해시태그로 만들어줘. 추론하면 안돼.
                            3. 맛에 관련된 부분도 추론이기 때문에 만들면 안돼. (ex. 달콤한 맛)
                            4. 사진에서 볼 수 있는 디저트가 있다면 해시태그로 만들어줘. (ex. 아이스 아메리카노, 라떼, 케이크, 쿠키 등)
                            5. 의자 사진이 많이 보인다면 이를 토대로 자리많음, 자리없음을 해시태그로 뽑아줘.
                            6. 음식사진만 있다면 혼잡도를 판단할 수 없어.
                            7. 인테리어가 전체적으로 어떤 느낌인지 확인할 수 있다면 해시태그로 뽑아줘.
                            """,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            response_format=Tag_Score_Response
        )
        res = json.loads(completion.choices[0].message.content)
        return res
    except openai.APIError as e:
        print(f"OpenAI API 호출 실패: {e}")
        return {'positive_tags': [], 'neutral_tags': [], 'negative_tags': []}
    

# print(extract_image_hashtags("https://pinpung-s3.s3.ap-northeast-2.amazonaws.com/original-images/25"))
# print(extract_review_hashtags("맛있어요!"))