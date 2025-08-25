import pymysql  # pymysql로 변경
import requests
import io
import objc
from PIL import Image
import Vision
from typing import List, Tuple
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database credentials from environment variables
db = pymysql.connect(
    host="localhost",
    user="root",
    password="dnjswnsdud1.",  # 환경변수 활용으로 보안 강화
    database="swpre6"
)
cursor = db.cursor()

# PIL 이미지를 Apple Vision 프레임워크가 사용할 수 있는 바이트 버퍼로 변환
def pil2buf(pil_image: Image.Image):
    """Convert PIL image to buffer"""
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return buffer.getvalue()

#공지사항의 이미지 URL에서 이미지를 다운로드하여 PIL 형식으로 변환
def load_image_from_url(url: str) -> Image.Image:
    """Load image from a URL into PIL format"""
    response = requests.get(url)
    if response.status_code == 200:
        image = Image.open(io.BytesIO(response.content))
        return image
    else:
        raise Exception(f"Failed to retrieve image from {url}")

def text_from_image(
    image, recognition_level="accurate", language_preference=None, confidence_threshold=0.0
) -> List[Tuple[str, float, Tuple[float, float, float, float]]]: # str: 인식된 텍스트, float: 신뢰도 점수 (0.0~1.0), Tuple[float, float, float, float]: 바운딩 박스 좌표 (x, y, width, height)
    """Extract text from image using Apple's Vision framework."""
    if not isinstance(image, Image.Image): #PIL Image 객체
        raise ValueError("Invalid image format. Image must be a PIL image.")

    if recognition_level not in {"accurate", "fast"}: #"accurate" 또는 "fast" (기본값: "accurate")
        raise ValueError("Invalid recognition level. Must be 'accurate' or 'fast'.")

    if language_preference is not None and not isinstance(language_preference, list): #언어 코드 리스트
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

# Query images with content field that needs to be updated (OCR이 처리되지 않은 이미지)
cursor.execute("SELECT id, image, content FROM swpre WHERE image IS NOT NULL")
image_rows = cursor.fetchall()

if not image_rows:
    print("No images found.")
else:
    for row in image_rows:
        id, image_url, existing_content = row
        try:
            # Load image from URL
            image = load_image_from_url(image_url)

            # Perform OCR
            recognized_text = text_from_image(image, recognition_level="accurate", language_preference=["ko-KR"], confidence_threshold=0.8)
            extracted_text = " ".join([text for text, _, _ in recognized_text])

            # Prepare SQL query to concatenate existing content with extracted text
            if existing_content:
                new_content = f"{existing_content} {extracted_text}"
            else:
                new_content = extracted_text

            # Print and update content in the database
            print(f"Extracted text for ID {id}: {extracted_text}")
            cursor.execute("UPDATE swpre SET content = CONCAT(content, %s) WHERE id = %s", (f" {extracted_text.strip()}", id))
            db.commit()
            print(f"Updated content for ID {id}")

        except requests.exceptions.RequestException as e:
            print(f"Failed to download image for ID {id}: {e}")
        except Exception as e:
            print(f"Error for ID {id}: {e}")

# Close database connection
cursor.close()
db.close()
