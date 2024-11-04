import os
from config import AI_IP, AI_PORT

from fastapi import FastAPI, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from rec import recommendation_router
from tag import tag_router
from db_connect import get_db_session, get_recent_place_tags_dataframe
app = FastAPI()

app.include_router(tag_router)
app.include_router(recommendation_router)

@app.get('/')
def home():
    return {'message' : 'main'}

# 의존성 주입
# https://fastapi.tiangolo.com/ko/tutorial/dependencies/#annotated

@app.get("/recent-place-tags/")
async def recent_place_tags(session: AsyncSession = Depends(get_db_session)):
    df = await get_recent_place_tags_dataframe(session)
    return df.to_dict(orient="records")

if __name__ == "__main__":
    uvicorn.run("main:app", host=AI_IP, port=AI_PORT, reload=True)


# curl -X POST 'http://127.0.0.1:8000/tags/' \           
# -H 'Content-Type: application/json' \
# -d '{"review_text": "hello world", "image_url": "/home/test"}'