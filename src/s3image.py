# s3image.py

import boto3
import base64
from botocore.exceptions import ClientError
import logging
from fastapi import HTTPException
from config import S3_BUCKET_NAME # , S3_REGION_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

# 로깅 설정
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# boto3 S3 클라이언트 생성
s3_client = boto3.client(
    's3' # ,
    # region_name=S3_REGION_NAME,
    # aws_access_key_id=AWS_ACCESS_KEY_ID,
    # aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def encode_image_from_s3(image_url: str) -> str:
    """
    S3에서 이미지를 가져와 Base64로 인코딩합니다.

    :param image_id: 이미지의 ID (long 타입)
    :return: Base64로 인코딩된 이미지 문자열
    :raises HTTPException: 이미지가 없거나 S3 접근 오류 시
    """
    # image_key = f"uploaded-images/{image_id}"
    # image_key = image_url
    image_key = f"{image_url}"
    try:
        # S3에서 객체 가져오기
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=image_key)
        # 객체의 바이트 데이터 읽기
        image_bytes = response['Body'].read()
        # Base64 인코딩
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        logger.info(f"Successfully fetched and encoded image with ID {image_url}.")
        return image_base64
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            logger.error(f"Image with ID {image_url} not found in bucket '{S3_BUCKET_NAME}'.")
            raise HTTPException(status_code=404, detail="Image not found.")
        else:
            logger.error(f"Error fetching image with ID {image_url} from S3: {e}")
            raise HTTPException(status_code=500, detail="Error fetching image from S3.")
    except Exception as e:
        logger.error(f"Unexpected error while fetching image with ID {image_url}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
