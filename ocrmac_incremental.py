#!/usr/bin/env python3
"""
한성대학교 챗봇 증분 OCR 처리 스크립트
새로 추가된 이미지가 있는 공지사항만 OCR 처리
"""

import pymysql
import requests
import io
import objc
from PIL import Image
import Vision
from typing import List, Tuple
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

def pil2buf(pil_image: Image.Image):
    """Convert PIL image to buffer"""
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return buffer.getvalue()

def load_image_from_url(url: str) -> Image.Image:
    """Load image from a URL into PIL format"""
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        image = Image.open(io.BytesIO(response.content))
        return image
    else:
        raise Exception(f"Failed to retrieve image from {url}")

def text_from_image(
    image, recognition_level="accurate", language_preference=None, confidence_threshold=0.0
) -> List[Tuple[str, float, Tuple[float, float, float, float]]]:
    """Extract text from image using Apple's Vision framework."""
    if not isinstance(image, Image.Image):
        raise ValueError("Invalid image format. Image must be a PIL image.")

    if recognition_level not in {"accurate", "fast"}:
        raise ValueError("Invalid recognition level. Must be 'accurate' or 'fast'.")

    if language_preference is not None and not isinstance(language_preference, list):
        raise ValueError("Language preference must be a list.")

    with objc.autorelease_pool():
        req = Vision.VNRecognizeTextRequest.alloc().init()
        req.setRecognitionLevel_(1 if recognition_level == "fast" else 0)

        if language_preference is not None:
            available_languages = req.supportedRecognitionLanguagesAndReturnError_(None)[0]
            if not set(language_preference).issubset(set(available_languages)):
                raise ValueError(
                    f"Invalid language preference. Must be a subset of {available_languages}."
                )
            req.setRecognitionLanguages_(language_preference)

        handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(
            pil2buf(image), None
        )

        success = handler.performRequests_error_([req], None)
        res = []
        if success:
            for result in req.results():
                confidence = result.confidence()
                if confidence >= confidence_threshold:
                    bbox = result.boundingBox()
                    x, y = bbox.origin.x, bbox.origin.y
                    w, h = bbox.size.width, bbox.size.height
                    res.append((result.text(), confidence, (x, y, w, h)))
            
        return res

def get_latest_ocr_time(cursor):
    """마지막 OCR 처리 시간을 가져옵니다."""
    try:
        cursor.execute("SELECT MAX(updated_at) FROM swpre WHERE content IS NOT NULL AND content != ''")
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        else:
            # OCR 처리된 데이터가 없으면 7일 전으로 설정
            return datetime.now() - timedelta(days=7)
    except Exception as e:
        print(f"최근 OCR 시간 조회 오류: {e}")
        return datetime.now() - timedelta(days=7)

def main():
    """메인 증분 OCR 처리 함수"""
    print("한성대학교 챗봇 증분 OCR 처리 시작")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Database connection
    try:
        db = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'dnjswnsdud1.'),
            database=os.getenv('DB_NAME', 'swpre6'),
            port=int(os.getenv('DB_PORT', '3306'))
        )
        cursor = db.cursor()
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        return False
    
    # 테이블에 updated_at 컬럼이 없으면 추가
    try:
        cursor.execute("SHOW COLUMNS FROM swpre LIKE 'updated_at'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE swpre ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
            db.commit()
            print("updated_at 컬럼이 추가되었습니다.")
        else:
            print("updated_at 컬럼이 이미 존재합니다.")
    except Exception as e:
        print(f"테이블 구조 업데이트 오류: {e}")
    
    # 최근 OCR 처리 시간 가져오기
    latest_ocr_time = get_latest_ocr_time(cursor)
    print(f"최근 OCR 처리 시간: {latest_ocr_time}")
    print(f"이 시간 이후의 새로운 이미지만 OCR 처리합니다.")
    
    # 새로 추가된 이미지가 있는 공지사항만 조회 (OCR이 처리되지 않은 것)
    query = """
    SELECT id, image, content, title 
    FROM swpre 
    WHERE image IS NOT NULL 
    AND image != '' 
    AND (content IS NULL OR content = '' OR content = 'No content found')
    AND date > %s
    ORDER BY date DESC
    """
    
    cursor.execute(query, (latest_ocr_time,))
    image_rows = cursor.fetchall()
    
    if not image_rows:
        print("새로 추가된 이미지가 있는 공지사항이 없습니다.")
        cursor.close()
        db.close()
        return True
    
    print(f"새로 추가된 이미지가 있는 공지사항 {len(image_rows)}개를 OCR 처리합니다.")
    
    processed_count = 0
    error_count = 0
    
    for row in image_rows:
        id, image_url, existing_content, title = row
        try:
            print(f"OCR 처리 중: {title}")
            
            # Load image from URL
            image = load_image_from_url(image_url)

            # Perform OCR
            recognized_text = text_from_image(
                image, 
                recognition_level="accurate", 
                language_preference=["ko-KR"], 
                confidence_threshold=0.8
            )
            extracted_text = " ".join([text for text, _, _ in recognized_text])

            # Prepare new content
            if existing_content and existing_content != "No content found":
                new_content = f"{existing_content} {extracted_text}"
            else:
                new_content = extracted_text

            # Update content in the database
            cursor.execute(
                "UPDATE swpre SET content = %s, updated_at = NOW() WHERE id = %s", 
                (new_content, id)
            )
            db.commit()
            
            processed_count += 1
            print(f"OCR 처리 완료 (ID {id}): {extracted_text[:100]}...")

        except requests.exceptions.RequestException as e:
            print(f"이미지 다운로드 실패 (ID {id}): {e}")
            error_count += 1
        except Exception as e:
            print(f"OCR 처리 오류 (ID {id}): {e}")
            error_count += 1
    
    # Close database connection
    cursor.close()
    db.close()
    
    # 결과 요약
    print(f"\n{'='*60}")
    print(f"증분 OCR 처리 완료")
    print(f"{'='*60}")
    print(f"처리된 공지사항: {processed_count}개")
    print(f"오류 발생: {error_count}개")
    print(f"총 확인된 공지사항: {len(image_rows)}개")
    
    if processed_count > 0:
        print(f"새로운 이미지 {processed_count}개가 성공적으로 OCR 처리되었습니다!")
        return True
    else:
        print(f"새로운 이미지가 없습니다.")
        return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n사용자에 의해 중단되었습니다.")
        exit(1)
    except Exception as e:
        print(f"\n예상치 못한 오류: {e}")
        exit(1) 