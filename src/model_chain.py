from pydantic import BaseModel
from openai import OpenAI
cli = OpenAI()

import base64
import json
import os
from config import OPENAI_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_KEY

class Tag_Response(BaseModel):
    # tags: list[str]
    # index: int
    positive_tags: list[str]
    negative_tags: list[str]

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_review_hashtags(review_text):
    completion = cli.beta.chat.completions.parse(
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
                    6. 메뉴와 관련된 문장이 있으면 메뉴이름 + 특징 으로 뽑아줘. (ex. 밀크 크레이프 케익은 빌리엔젤이 최고! -> #밀크 크레이프 케익 최고)

                    출력방식: 
                    #해시태그1, #해시태그2, #해시태그3 ... 

                    생성된 해시태그를 긍정적인 해시태그와 부정적인 해시태그로 나눠서 출력해줘.
                    
                    리뷰: {review_text}                    
                """
            }
        ],
        response_format=Tag_Response
    )
    res = json.loads(completion.choices[0].message.content)
    return res

def extract_image_hashtags(image_path):
    base64_image = encode_image(image_path)
    completion = cli.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        다음 이미지를 한글로 설명해줘. 그리고 난 다음에는 사진에서 주요 특징이 보이는 키워드 5개를 '#키워드1, #키워드2' 형태로 출력시켜줘: 
                        
                        생성된 해시태그를 긍정적인 해시태그와 부정적인 해시태그로 나눠서 출력해줘.
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
        response_format=Tag_Response
    )
    res = json.loads(completion.choices[0].message.content)
    return res

