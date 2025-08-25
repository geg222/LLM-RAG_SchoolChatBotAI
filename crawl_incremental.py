#!/usr/bin/env python3
"""
한성대학교 챗봇 증분 업데이트 스크립트
기존 공지사항을 제외하고 새로 올라온 학사 공지사항만 크롤링
"""

import requests
from bs4 import BeautifulSoup as bs
import pymysql
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def content_croll(url):
    """공지사항 내용을 크롤링하는 함수"""
    try:
        page = requests.get(url, timeout=10)
        soup = bs(page.text, 'html.parser')
        view_con_div = soup.find('div', class_='view-con')
        
        content = ""
        image_url = None
        if view_con_div:
            content = view_con_div.get_text(strip=True)
            
            # 이미지 URL을 찾기
            image_tag = view_con_div.find('img')
            if image_tag and 'src' in image_tag.attrs:
                image_url = image_tag['src']
        else:
            content = "No content found"
        
        return content, image_url
    except Exception as e:
        print(f"내용 크롤링 오류 ({url}): {e}")
        return "Error loading content", None

def get_latest_update_time(cursor):
    """데이터베이스에서 가장 최근 업데이트 시간을 가져옵니다."""
    try:
        cursor.execute("SELECT MAX(date) FROM swpre")
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        else:
            # 데이터가 없으면 7일 전으로 설정
            return datetime.now() - timedelta(days=7)
    except Exception as e:
        print(f"최근 업데이트 시간 조회 오류: {e}")
        return datetime.now() - timedelta(days=7)

def is_new_notice(pub_date_str, latest_update_time):
    """공지사항이 최근 업데이트 이후에 올라온 것인지 확인합니다."""
    try:
        # RSS 날짜 형식 파싱 (예: "2025-01-20 15:30:00.0")
        pub_date = datetime.strptime(pub_date_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
        return pub_date > latest_update_time
    except Exception as e:
        print(f"날짜 파싱 오류 ({pub_date_str}): {e}")
        return False

def main():
    """메인 증분 업데이트 함수"""
    print("한성대학교 챗봇 증분 업데이트 시작")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # MySQL 연결
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
    
    # 테이블이 없으면 생성
    create_table_query = """
    CREATE TABLE IF NOT EXISTS swpre (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        link TEXT,
        content TEXT,
        image TEXT,
        date DATETIME
    )
    """
    cursor.execute(create_table_query)
    
    # 최근 업데이트 시간 가져오기
    latest_update_time = get_latest_update_time(cursor)
    print(f"최근 업데이트 시간: {latest_update_time}")
    print(f"이 시간 이후의 새로운 공지사항만 크롤링합니다.")
    
    # 학사 공지사항 RSS URL
    base_url = 'https://www.hansung.ac.kr/bbs/hansung/143/rssList.do?page={}&category=학사'
    
    new_count = 0
    total_checked = 0
    consecutive_old_pages = 0  # 연속으로 오래된 페이지가 나온 횟수
    
    # 최근 페이지부터 확인 (새 공지사항이 위쪽에 있을 가능성이 높음)
    for page_number in range(1, 20):  # 최근 20페이지만 확인
        url = base_url.format(page_number)
        
        try:
            page = requests.get(url, timeout=10)
            soup = bs(page.text, 'xml')
            articles = soup.find_all('item')
        except Exception as e:
            print(f"페이지 {page_number} 로딩 오류: {e}")
            continue
        
        if not articles:
            consecutive_old_pages += 1
            if consecutive_old_pages >= 3:
                print(f"연속 {consecutive_old_pages}번 빈 페이지가 나와서 크롤링을 중단합니다.")
                break
            continue
        
        # 학사 공지사항만 필터링
        academic_articles = []
        for article in articles:
            category = article.find('category').get_text(strip=True) if article.find('category') else ""
            if category == "학사":
                academic_articles.append(article)
        
        if not academic_articles:
            continue
        
        print(f"페이지 {page_number}에서 {len(academic_articles)}개의 학사 공지사항을 확인합니다.")
        
        page_has_new = False
        for article in academic_articles:
            title = article.find('title').get_text(strip=True) if article.find('title') else "No Title"
            link = article.find('link').get_text() if article.find('link') else "No Link"
            pub_date = article.find('pubDate').get_text(strip=True) if article.find('pubDate') else "No Date"
            
            total_checked += 1
            
            # 2025년 공지사항만 처리
            if '2025' not in pub_date:
                continue
            
            # 새로운 공지사항인지 확인
            if not is_new_notice(pub_date, latest_update_time):
                continue
            
            # 링크 정규화
            if link.startswith("/"):
                link = f"https://www.hansung.ac.kr{link}"
            
            # 중복 체크 (추가 안전장치)
            cursor.execute("SELECT COUNT(*) FROM swpre WHERE link = %s", (link,))
            if cursor.fetchone()[0] > 0:
                print(f"이미 저장된 링크 건너뛰기: {title}")
                continue
            
            # 내용 크롤링
            content, image_url = content_croll(link)
            
            # 데이터베이스에 저장
            try:
                sql = "INSERT INTO swpre (title, link, content, image, date) VALUES (%s, %s, %s, %s, %s)"
                val = (title, link, content, image_url, pub_date)
                cursor.execute(sql, val)
                db.commit()
                
                new_count += 1
                page_has_new = True
                
                print(f"새 공지사항 저장: {title}")
                print(f"링크: {link}")
                print(f"게시 날짜: {pub_date}")
                print("-" * 40)
                
            except Exception as e:
                print(f"데이터베이스 저장 오류 ({title}): {e}")
        
        # 페이지에 새로운 공지사항이 없으면 카운트 증가
        if not page_has_new:
            consecutive_old_pages += 1
        else:
            consecutive_old_pages = 0
        
        # 연속 5페이지에 새로운 공지사항이 없으면 중단
        if consecutive_old_pages >= 5:
            print(f"연속 {consecutive_old_pages}페이지에 새로운 공지사항이 없어서 크롤링을 중단합니다.")
            break
    
    # 연결 종료
    cursor.close()
    db.close()
    
    # 결과 요약
    print(f"\n{'='*60}")
    print(f"증분 업데이트 완료")
    print(f"{'='*60}")
    print(f"확인한 공지사항: {total_checked}개")
    print(f"새로 저장된 공지사항: {new_count}개")
    print(f"최근 업데이트 시간: {latest_update_time}")
    print(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if new_count > 0:
        print(f"새로운 공지사항 {new_count}개가 성공적으로 저장되었습니다!")
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