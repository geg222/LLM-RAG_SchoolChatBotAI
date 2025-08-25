import mysql.connector
import time
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os
from pinecone import Pinecone, ServerlessSpec
from langchain_core.embeddings import Embeddings

load_dotenv()

class Document:
    def __init__(self, page_content, metadata=None, id=None):
        self.page_content = page_content
        self.metadata = metadata if metadata is not None else {}
        self.id = id

# Pinecone 초기화 및 인덱스 생성
def create_pinecone_index(index_name, dimension=1024):
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    
    # 인덱스가 존재하지 않으면 생성
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'  # 무료 플랜에서 지원하는 리전
            )
        )
        print(f"새로운 Pinecone 인덱스 '{index_name}' (차원: {dimension})가 생성되었습니다.")
    else:
        print(f"기존 Pinecone 인덱스 '{index_name}'를 사용합니다.")

# Step 1: MySQL에 연결
db = mysql.connector.connect(
    host="localhost",        
    user="root",            
    password="dnjswnsdud1.",    
    database="swpre6"      
)

cursor = db.cursor()

# Step 2: 테이블에서 데이터를 배열로 변환
def crawled_data_to_array():
    fetch_query = "SELECT id, title, link, content, date FROM swpre"
    cursor.execute(fetch_query)
    rows = cursor.fetchall()
    return rows

# Step 3: 메타데이터와 함께 임베딩 생성 및 저장
def store_array_to_vector_db():
    # 기존 1024 차원 Pinecone 인덱스 사용
    index_name = 'swpre10'
    print(f"기존 Pinecone 인덱스 '{index_name}' (차원: 1024)를 사용합니다.")
    
    # 1024 차원을 생성하는 HuggingFace 임베딩 모델 사용
    embedding = HuggingFaceEmbeddings(
        model_name="intfloat/e5-large-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    rows = crawled_data_to_array()
    documents = []
    print(f"처리할 데이터: {len(rows)}개")
    
    for id, title, link, content, pub_date in rows:
        # 날짜를 UNIX 타임스탬프로 변환
        date_object = datetime.strptime(str(pub_date), "%Y-%m-%d %H:%M:%S")
        unix_timestamp = int(time.mktime(date_object.replace(hour=0, minute=0, second=0, microsecond=0).timetuple()))
        
        # 문서 내용 생성
        combined_content = f"Title: {title}\nLink: {link}\nContent: {content}"
        metadata = {
            'title': title,
            'link': link,
            'expiry_date': unix_timestamp  # UNIX 타임스탬프 저장
        }
        documents.append(Document(combined_content, metadata, id=str(id)))

    # 문서를 Pinecone에 저장
    database = PineconeVectorStore.from_documents(documents, embedding, index_name=index_name)

    print(f"{len(documents)}개의 문서가 Pinecone 인덱스 '{index_name}'에 업로드되었습니다.")
    print(f"임베딩 차원: 1024")

store_array_to_vector_db()

cursor.close()
db.close()
