#!/usr/bin/env python3
"""
한성대학교 챗봇 증분 벡터 DB 업로드 스크립트
새로 추가된 공지사항만 벡터 데이터베이스에 업로드
"""

import mysql.connector
import time
from datetime import datetime, timedelta
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
import os
from dotenv import load_dotenv

class Document:
    def __init__(self, page_content, metadata=None, id=None):
        self.page_content = page_content
        self.metadata = metadata if metadata is not None else {}
        self.id = id
        
load_dotenv()

def get_latest_upload_time(cursor):
    """마지막 벡터 DB 업로드 시간을 가져옵니다."""
    try:
        # Pinecone에 업로드된 가장 최근 공지사항의 날짜를 확인
        cursor.execute("SELECT MAX(date) FROM swpre WHERE id IN (SELECT DISTINCT id FROM swpre WHERE date IS NOT NULL)")
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        else:
            # 업로드된 데이터가 없으면 7일 전으로 설정
            return datetime.now() - timedelta(days=7)
    except Exception as e:
        print(f"최근 업로드 시간 조회 오류: {e}")
        return datetime.now() - timedelta(days=7)

def get_new_notices(cursor, latest_upload_time):
    """새로 추가된 공지사항을 가져옵니다."""
    try:
        query = """
        SELECT id, title, link, content, date 
        FROM swpre 
        WHERE date > %s 
        AND content IS NOT NULL 
        AND content != '' 
        AND content != 'No content found'
        ORDER BY date DESC
        """
        cursor.execute(query, (latest_upload_time,))
        return cursor.fetchall()
    except Exception as e:
        print(f"새 공지사항 조회 오류: {e}")
        return []

def main():
    """메인 증분 업로드 함수"""
    print("한성대학교 챗봇 증분 벡터 DB 업로드 시작")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: MySQL에 연결
    try:
        db = mysql.connector.connect(
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
    
    # 최근 업로드 시간 가져오기
    latest_upload_time = get_latest_upload_time(cursor)
    print(f"최근 업로드 시간: {latest_upload_time}")
    print(f"이 시간 이후의 새로운 공지사항만 업로드합니다.")
    
    # 새로 추가된 공지사항 가져오기
    new_notices = get_new_notices(cursor, latest_upload_time)
    
    if not new_notices:
        print("새로 추가된 공지사항이 없습니다.")
        cursor.close()
        db.close()
        return True
    
    print(f"새로 추가된 공지사항 {len(new_notices)}개를 벡터 DB에 업로드합니다.")
    
    # Step 2: 임베딩 모델 설정
    try:
        embedding = HuggingFaceEmbeddings(
            model_name="intfloat/e5-large-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("임베딩 모델 로드 완료")
    except Exception as e:
        print(f"임베딩 모델 로드 오류: {e}")
        cursor.close()
        db.close()
        return False
    
    # Step 3: Pinecone 인덱스 설정
    index_name = os.getenv('PINECONE_INDEX_NAME', 'swpre10')
    print(f"Pinecone 인덱스 '{index_name}' (차원: 1024)를 사용합니다.")
    
    # Step 4: 새 공지사항을 문서로 변환
    documents = []
    for id, title, link, content, pub_date in new_notices:
        try:
            # 날짜를 UNIX 타임스탬프로 변환
            date_object = datetime.strptime(str(pub_date), "%Y-%m-%d %H:%M:%S")
            unix_timestamp = int(time.mktime(date_object.replace(hour=0, minute=0, second=0, microsecond=0).timetuple()))
            
            # 문서 내용 생성
            combined_content = f"Title: {title}\nLink: {link}\nContent: {content}"
            metadata = {
                'title': title,
                'link': link,
                'expiry_date': unix_timestamp
            }
            documents.append(Document(combined_content, metadata, id=str(id)))
            
            print(f"문서 변환 완료: {title}")
            
        except Exception as e:
            print(f"문서 변환 오류 (ID {id}): {e}")
            continue
    
    if not documents:
        print("업로드할 문서가 없습니다.")
        cursor.close()
        db.close()
        return True
    
    # Step 5: Pinecone에 업로드
    try:
        print(f"{len(documents)}개의 새 문서를 Pinecone에 업로드 중...")
        
        # 기존 Pinecone 인덱스에 새 문서 추가
        vectorstore = PineconeVectorStore.from_documents(
            documents, 
            embedding, 
            index_name=index_name
        )
        
        print(f"{len(documents)}개의 새 문서가 Pinecone 인덱스 '{index_name}'에 성공적으로 업로드되었습니다.")
        print(f"임베딩 차원: 1024")
        
    except Exception as e:
        print(f"Pinecone 업로드 오류: {e}")
        cursor.close()
        db.close()
        return False
    
    # 연결 종료
    cursor.close()
    db.close()
    
    # 결과 요약
    print(f"\n{'='*60}")
    print(f"증분 벡터 DB 업로드 완료")
    print(f"{'='*60}")
    print(f"업로드된 공지사항: {len(documents)}개")
    print(f"최근 업로드 시간: {latest_upload_time}")
    print(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if len(documents) > 0:
        print(f"새로운 공지사항 {len(documents)}개가 성공적으로 벡터 DB에 업로드되었습니다!")
        return True
    else:
        print(f"새로운 공지사항이 없습니다.")
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