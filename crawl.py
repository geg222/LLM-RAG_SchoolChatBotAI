import requests
from bs4 import BeautifulSoup as bs
import pymysql  # pymysql로 변경

# 공지사항 내용을 크롤링하는 함수
# 공지사항 상세 페이지에서 내용 텍스트 추출
#이미지 URL 추출 (OCR 처리를 위해)
#BeautifulSoup을 사용한 HTML 파싱
def content_croll(url):
    page = requests.get(url)
    soup = bs(page.text, 'html.parser')
    view_con_div = soup.find('div', class_='view-con')
    
    content = ""
    image_url = None
    if view_con_div:
        content = view_con_div.get_text(strip=True)
        
        # 이미지 URL을 찾기 (content와 상관없이 이미지 URL을 추출)
        image_tag = view_con_div.find('img')
        if image_tag and 'src' in image_tag.attrs:
            image_url = image_tag['src']
    
    else:
        content = "No content found"
    
    return content, image_url

# 학사 공지사항 필터링 함수
def is_academic_notice(category):
    """카테고리가 '학사'인지 확인"""
    return category == '학사'

# MySQL 연결 설정
db = pymysql.connect(
    host="localhost",
    user="root",
    password="dnjswnsdud1.",
    database="swpre6"
)
cursor = db.cursor()

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

# 학사 공지사항만 가져오는 RSS URL (카테고리 필터링)
base_url = 'https://www.hansung.ac.kr/bbs/hansung/143/rssList.do?page={}&category=학사'

academic_count = 0
consecutive_empty_pages = 0  # 연속으로 빈 페이지가 나온 횟수

for page_number in range(1, 92):
    url = base_url.format(page_number)
    page = requests.get(url)
    soup = bs(page.text, 'xml')
    articles = soup.find_all('item')
    base_domain = "https://www.hansung.ac.kr"

    # 학사 공지사항이 없으면 연속 빈 페이지 카운트
    if not articles:
        consecutive_empty_pages += 1
        print(f"페이지 {page_number}에서 학사 공지사항을 찾을 수 없습니다. (연속 {consecutive_empty_pages}번째 빈 페이지)")
        
        # 연속 3번 빈 페이지가 나오면 크롤링 중단
        if consecutive_empty_pages >= 3:
            print(f"연속 {consecutive_empty_pages}번 빈 페이지가 나와서 크롤링을 중단합니다.")
            break
        continue
    else:
        consecutive_empty_pages = 0  # 학사 공지사항이 있으면 카운트 리셋

    # 학사 공지사항만 먼저 필터링
    academic_articles = []
    for article in articles:
        category = article.find('category').get_text(strip=True) if article.find('category') else ""
        if category == "학사":
            academic_articles.append(article)
    
    # 학사 공지사항이 없으면 다음 페이지로
    if not academic_articles:
        continue
    
    print(f"페이지 {page_number}에서 {len(academic_articles)}개의 학사 공지사항을 찾았습니다.")
    
    for article in academic_articles:
        title = article.find('title').get_text(strip=True) if article.find('title') else "No Title"
        link = article.find('link').get_text() if article.find('link') else "No Link"
        pub_date = article.find('pubDate').get_text(strip=True) if article.find('pubDate') else "No Date"

        # 2025년의 공지사항만 처리
        if '2025' not in pub_date:
            continue

        if link.startswith("/"):
            link = f"{base_domain}{link}"

        content, image_url = content_croll(link)

        # 중복 체크
        cursor.execute("SELECT COUNT(*) FROM swpre WHERE link = %s", (link,))
        if cursor.fetchone()[0] > 0:
            print(f"이미 저장된 링크 건너뛰기: {title}")
            continue
            
        # MySQL 테이블에 저장
        sql = "INSERT INTO swpre (title, link, content, image, date) VALUES (%s, %s, %s, %s, %s)"
        val = (title, link, content, image_url, pub_date)
        cursor.execute(sql, val)
        db.commit()

        academic_count += 1

        # 저장된 데이터 출력
        print(f"제목: {title}")
        print(f"링크: {link}")
        print(f"내용: {content[:100]}...")  # 내용의 앞 100자만 출력
        print(f"이미지 URL: {image_url}")
        print(f"게시 날짜: {pub_date}")
        print(f"카테고리: {category}")
        print("-" * 40)  # 구분선 출력

# MySQL 연결 종료
cursor.close()
db.close()

print(f"{academic_count}개의 학사 공지사항이 성공적으로 저장되었습니다.")
