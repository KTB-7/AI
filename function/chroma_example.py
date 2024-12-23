from openai import OpenAI
import openai
from chromadb.utils.embedding_functions import EmbeddingFunction
from sentence_transformers import SentenceTransformer
import base64
import json
import os
from pydantic import BaseModel
import chromadb
import numpy as np
import uuid
from dotenv import load_dotenv

# 디렉토리 중복 import 제거

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

class Tag_Response(BaseModel):
    tags: list[str]
    index: int

def extract_review_hashtags(review_text):
    try:
        completion = openai.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                        텍스트는 카페에 대해서 사용자가 남긴 리뷰야. 해당 리뷰를 분석하여 각 리뷰에서 3개에서 5개의 주요 특징을 뽑아 해시태그로 만들어줘. 해시태그는 리뷰에서 중요한 키워드, 감정(긍정적/부정적), 서비스의 질 등을 반영하여 작성해줘. 
                        주의사항
                        1. 해시태그를 출력할 때 가게 이름(ex. 스타벅스, 블루보틀)은 들어가지 않게 해줘.
                        2. 메뉴 이름은 그 자체로 명사로 뽑아내줘.
                        3. 만약 형용사/부사와 명사가 같이 나온다면 형용사/부사 + 명사 순으로 뽑아내줘. (ex. 친절한 서비스, 불친절한 직원)
                        출력방식은 다른 부가 설명 없이 깔끔하게 다음과 같아:
                        4. 띄어쓰기가 필요한 부분은 띄어쓰기 해줘.
                        5. 리뷰에 있는 단어만 추출해줘.
                        6. 메뉴와 관련된 문장이 있으면 메뉴이름 + 특징 으로 뽑아줘. (ex. 밀크 크레이프 케익은 빌리엔젤이 최고! -> #밀크 크레이프 케익 최고)

                        출력방식: 앞에 #을 붙여야해.
                        #해시태그1, #해시태그2, #해시태그3 ... 
                        
                        리뷰: {review_text}                    
                    """
                }
            ],
            response_format=Tag_Response
        )
        res = json.loads(completion.choices[0].message.content)
        return res
    except openai.error.OpenAIError as e:
        print(f"OpenAI API 호출 실패: {e}")
        return {'tags': []}

def embed_hashtags(hashtags, embedding_model):
    if not hashtags:
        print("No hashtags to embed.")
        return []

    hashtags = [str(tag) for tag in hashtags]
    if not all(isinstance(tag, str) for tag in hashtags):
        raise ValueError("All elements of hashtags must be strings")

    if len(hashtags) > 0:
        return embedding_model.encode(hashtags)
    else:
        print("Hashtags list is empty after processing.")
        return []

def store_hashtags_in_db(db, hashtags, embeddings):
    for hashtag, embedding in zip(hashtags, embeddings):
        unique_id = str(uuid.uuid4())  # 각 해시태그에 대해 고유한 ID 생성
        db.add(ids=[unique_id], documents=[hashtag], embeddings=[embedding], metadatas=[{"source": "new_review"}])

def find_similar_hashtag(db, new_embedding):
    # DB에서 모든 해시태그 임베딩 가져오기
    all_documents = db.get(include=['embeddings', 'documents', 'metadatas'])
    existing_embeddings = all_documents['embeddings']
    existing_documents = all_documents['documents']

    if len(existing_embeddings) == 0: #db 비어있는 경우
        return None, None

    # 새로운 임베딩과 기존 임베딩들 간의 유사도 계산
    results = db.query(query_embeddings=[new_embedding], n_results=len(existing_documents))
    print("유사도 계산 결과:")
    
    # 모든 유사도 결과를 확인
    min_distance = float('inf')
    most_similar_document = None
    for document, distance in zip(results['documents'][0], results['distances'][0]):
        print(f"Document: '{document}', Distance: {distance}")
        if distance < min_distance:
            min_distance = distance
            most_similar_document = document

    # 가장 유사한 해시태그 반환
    if most_similar_document is not None:
        return most_similar_document, min_distance
    return None, None

def process_review(review_text, db, embedding_model):
    hashtags = extract_review_hashtags(review_text)['tags']
    embeddings = embed_hashtags(hashtags, embedding_model)

    for hashtag, embedding in zip(hashtags, embeddings):
        similar_hashtag, distance = find_similar_hashtag(db, embedding)
        if similar_hashtag and isinstance(distance, (float, int)) and distance < 0.4:
            print(f"'{hashtag}' is similar to existing hashtag '{similar_hashtag}' and will be replaced.")
        else:
            store_hashtags_in_db(db, [hashtag], [embedding])
            print(f"Stored new hashtag: {hashtag}")

def print_db_contents(db):
    all_documents = db.get(include=['documents', 'embeddings', 'metadatas'])
    if all_documents and len(all_documents['documents']) > 0:
        print("DB에 저장된 데이터:")
        for doc, meta in zip(all_documents['documents'], all_documents['metadatas']):
            print(f"Document: {doc}, Metadata: {meta}")
    else:
        print("DB가 비어있습니다.")

def main():
    load_dotenv()  # .env 파일의 변수를 환경 변수로 로드
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. 환경 변수나 .env 파일에 설정해주세요.")
    
    db_path = ".venv/AI/function/chroma_db"
    
    # 디렉토리가 존재하지 않으면 생성
    os.makedirs(db_path, exist_ok=True)
    
    chroma_client = chromadb.PersistentClient(path=db_path)
    db = chroma_client.get_or_create_collection(name="hashtag_embeddings")
    
    # 모델 로딩을 main 블록 안으로 이동
    model_name = 'snunlp/KR-SBERT-V40K-klueNLI-augSTS'
    try:
        embedding_model = SentenceTransformer(model_name)
    except OSError as e:
        print(f"모델 로딩 실패: {e}")
        return
    
    example_review = "아이스아메리카노 맛있어요"
    process_review(example_review, db, embedding_model)
    print_db_contents(db)

if __name__ == "__main__":
    main()
