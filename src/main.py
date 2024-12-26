import os
from config import AI_IP, AI_PORT

from fastapi import FastAPI, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from rec import recommendation_router
from tag import tag_router
app = FastAPI()

app.include_router(tag_router)
app.include_router(recommendation_router)

# Health check
@app.get('/health')
def health_check():
    return {"status": "ok"}

@app.get('/')
def home():
    return {'message' : 'main'}

if __name__ == "__main__":
    uvicorn.run("main:app", host=AI_IP, port=AI_PORT, reload=True)
