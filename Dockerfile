# 베이스 이미지 설정
FROM python:3.11-slim

# 필수 빌드 도구 및 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 소스 코드 복사
COPY . /app

# 실행 명령어
CMD ["python", "src/main.py"]
