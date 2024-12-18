
from openai import OpenAI
import base64
import os
from pydantic import BaseModel
import chromadb
import uuid
from typing import List, Tuple
# from chromadb.utils.embedding_functions import EmbeddingFunction
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config import OPENAI_KEY, VDB_PATH
os.environ['OPENAI_API_KEY'] = OPENAI_KEY

chroma_client = chromadb.PersistentClient(path=VDB_PATH, settings=Settings(anonymized_telemetry=False))
db = chroma_client.get_or_create_collection(
    name="hashtag_embeddings",
    metadata={"hnsw:space": "cosine"}
    )

embedding_model = SentenceTransformer(model_name_or_path='snunlp/KR-SBERT-V40K-klueNLI-augSTS', device='cpu')

class Tag_Response(BaseModel):
    tags: list[str]

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def embed_hashtags(hashtags):
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


def store_hashtags_in_db(hashtags, embeddings, sentiment):
    for hashtag, embedding in zip(hashtags, embeddings):
        unique_id = str(uuid.uuid4())  # 각 해시태그에 대해 고유한 ID 생성
        db.add(ids=[unique_id], documents=[hashtag], embeddings=[embedding], metadatas=[{"count": 1, "sentiment": sentiment}])


def find_similar_hashtag(new_embedding):
    # 새로운 임베딩과 기존 임베딩들 간의 유사도 계산
    results = db.query(query_embeddings=[new_embedding], n_results=1)
    # print(db.count())
    if db.count() == 0:
        return None, None, None, None, None
    # print("유사도 계산 결과:")
    
    # 모든 유사도 결과를 확인
    min_distance = float('inf')
    most_similar_document = None
    most_similar_id = None
    most_similar_count = None
    
    # print(results)
    # print(results['metadatas'][0])
    min_distance = results['distances'][0]
    most_similar_document = results['documents'][0]
    most_similar_id = results['ids'][0]
    most_similar_count = results['metadatas'][0][0]['count']
    most_similar_sentiment = results['metadatas'][0][0]['sentiment']

    # 가장 유사한 해시태그 반환
    if most_similar_document is not None:
        return most_similar_id, most_similar_document, min_distance, most_similar_count, most_similar_sentiment
    return None, None, None, None, None

def print_db_contents():
    all_documents = db.get(include=['documents', 'embeddings', 'metadatas'])
    if all_documents and len(all_documents['documents']) > 0:
        print("DB에 저장된 데이터:")
        for doc, meta, id in zip(all_documents['documents'], all_documents['metadatas'], all_documents['ids']):
            print(f"Document: {doc}, Metadata: {meta}, Id: {id}")
    else:
        print("DB가 비어있습니다.")

def tag_valid(
    hashtags : list[str],
    sentiment : int
) -> list[str]:
    embeddings = embed_hashtags(hashtags=hashtags)

    new_tag = []

    for hashtag, embedding in zip(hashtags, embeddings):
        similar_id, similar_hashtag, distance, similar_count, similar_sentiment = find_similar_hashtag(new_embedding=embedding)
        # print(f"for문 안 id: {similar_id}, distance: {distance}, count: {similar_count}")
        if similar_hashtag and distance[0] < 0.2:
            new_tag.append(similar_hashtag[0])
            # vdb +=count
            db.update(ids=similar_id, metadatas=[{"count": int(similar_count) + 1, "sentiment": similar_sentiment}])
            # print(f"'{hashtag}' is similar to existing hashtag '{similar_hashtag}' and will be replaced.")
        else:
            store_hashtags_in_db(hashtags=[hashtag], embeddings=[embedding], sentiment=sentiment)
            new_tag.append(hashtag)
            # print(f"Stored new hashtag: {hashtag}")

    return new_tag

def get_tag_sentiment(
    tag_ids = list[str]
) -> dict[str, int]:
    sentiments = {}
    embeddings = embed_hashtags(hashtags=tag_ids)
    for tag, embedding in zip(tag_ids, embeddings):
        db_results = db.query(query_embeddings=[embedding], n_results=1)
        sentiments[tag] = db_results['metadatas'][0][0]['sentiment']
        print(f"Sentiment for tag '{tag}': {db_results['documents'][0]} {sentiments[tag]}")
    
    return sentiments

def get_best_tags() -> list[str]:
    docus = db.get(where={"count": {"$gt": 1}}, include=['documents', 'metadatas'])
    
    combined = sorted(zip(docus['documents'], [meta['count'] for meta in docus['metadatas']]), key=lambda x: x[1], reverse=True)
    
    ret = [doc for doc, count in combined]

    return ret

if __name__ == "__main__":
    example_review = "백다방 에스프레소 맛있어요. 직원들이 불친절해서 나빠요."
    # process_review(example_review)
    # tag_valid(["매우 행복함"], 1)

    # print_db_contents()
    # tag_valid(["케이크 맛집"], 1)
    # tag_valid(["아이스아메리카노 맛집"], 1)
    # tag_valid(["녹차 좋아"], 1)
    # tag_valid(["케이크 맛집"], 1)
    # tag_valid(["아이스아메리카노 맛집"], 1)
    # tag_valid(["녹차 좋아"], 1)
    temp = get_best_tags()
    print(temp)


"""

"""
