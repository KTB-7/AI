from dotenv import load_dotenv
import os
import time

# .env 파일 로드
load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

AI_IP = "0.0.0.0"
AI_PORT = 8000

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", 3306)
MYSQL_USER = os.getenv("MYSQL_USER", "airoot")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "airoot")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ai_db")

VDB_PATH = os.getenv("VDB_PATH", "../vectordb")

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "pinpung-s3")