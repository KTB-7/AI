from pydantic import BaseModel
from openai import OpenAI
cli = OpenAI()

import json
import os
from config import OPENAI_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_KEY

class Tag_Response(BaseModel):
    tags: list[str]
    index: int

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

                    출력방식: 
                    #해시태그1, #해시태그2, #해시태그3 ... 
                    
                    리뷰: {review_text}                    
                """
            }
        ],
        response_format=Tag_Response
    )
    res = json.loads(completion.choices[0].message.content)
    return res