# PinPung AI Repo
이 프로젝트는 사용자가 리뷰(글과 사진)를 올리면 관련된 해시태그를 생성하고, 생성된 해시태그를 통해 비슷한 사용자와 카페를 찾아서 개인화된 추천을 제공한다.

## AI TASK
1. 리뷰 게시글과 리뷰 이미지를 받아와서 긍정/중립/부정에 따라서 해시태그를 생성한다.
2. 해시태그 생성 시 발생할 수 있는 문법적 오류, 어색한 표현을 검토하고 수정한다.
3. 개인화된 추천에서 해시태그를 사용하기 위해, sparse한 item feature를 줄인다. 유사한 해시태그는 클러스터링하여 추천 알고리즘에서 사용한다.
4. user-item interaction의 score로 생성된 해시태그의 긍정/중립/부정 비율에 가중치를 두어 학습한다.

## 파일 구조
```
AI/
├── src/                     # 소스 코드 디렉토리
│   ├── config.py            # 설정 파일 (.env 파일에 저장된 환경 변수를 설정)
│   ├── db_connect.py        # 비동기적으로 database 처리
│   ├── lm_graph.py          # Langgraph를 통해 해시태그 생성, 검증하는 파이프라인
│   ├── main.py              # 메인 실행 스크립트
│   ├── model_chain.py       # Openai API와 prompt engineering을 통해 해시태그를 생성
│   ├── rc_graph.py          # LightFM 라이브러리를 사용하여 사용자 맞춤 카페를 추천
│   ├── rec.py               # 추천 알고리즘 API
│   ├── s3image.py           # AWS S3에서 리뷰 이미지를 가져옴
│   ├── schemas.py           # Database DTO
│   ├── tag.py               # 해시태그 생성 API
│   └── vdb.py               # 뉴스 요약 처리 스크립트
├── Dockerfile
├── Jenkinsfile
└── requirements.txt         # 프로젝트 실행에 필요한 라이브러리 목록이 저장된 파일 (pipreqs)
```

## Keyword
FastAPI, Langchain, Langgraph, MySQL, RAG, ChromaDB, Hybrid filtering, Content-based filtering, Collaborative filtering, LightFM
