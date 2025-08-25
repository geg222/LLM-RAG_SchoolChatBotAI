from konlpy.tag import Okt
import re
from typing import List
from functools import lru_cache
import time

class KoreanTokenizer:
    """
    한국어 형태소 분석을 통한 키워드 추출 및 정규화
    """
    
    # Step 1: 초기화 및 설정
    def __init__(self):
        """
        한국어 토크나이저 초기화
        Step 1-1: KoNLPy Okt 형태소 분석기 초기화
        Step 1-2: 불용어(stop words) 설정
        Step 1-3: 캐싱 시스템 설정
        """
        # Step 1-1: KoNLPy Okt 형태소 분석기 초기화
        self.okt = Okt()  # Open Korean Text 형태소 분석기
        
        # Step 1-2: 불용어(stop words) 설정 - 의미가 없는 조사, 접미사 등
        self.stop_words = {
            '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '는', '은', '이', '가',
            '있', '하', '되', '것', '들', '그', '수', '이', '보', '않', '없', '나', '사람', '주', '아니', '등',
            '같', '우리', '때', '년', '월', '일', '분', '시', '초', '년도', '학기', '학년', '학과', '학부'
        }
        
        # Step 1-3: 캐싱 시스템 설정 (성능 최적화)
        self._cache = {}
        self._cache_size = 1000      # 최대 캐시 크기
        self._cache_ttl = 3600       # 캐시 유효 시간 (1시간)
    
    # Step 2: 키워드 추출 메인 로직
    @lru_cache(maxsize=1000)
    def extract_keywords(self, text: str) -> List[str]:
        """
        텍스트에서 의미있는 키워드를 추출합니다.
        Step 2-1: 특수문자 제거 및 전처리
        Step 2-2: 형태소 분석 수행
        Step 2-3: 명사, 동사, 형용사만 필터링
        Step 2-4: 불용어 제거
        캐싱을 통해 성능을 최적화합니다.
        """
        # Step 2-1: 특수문자 제거 및 전처리
        text = re.sub(r'[^\w\s]', ' ', text)  # 특수문자를 공백으로 변환
        
        # Step 2-2: 형태소 분석 수행
        pos_tags = self.okt.pos(text, norm=True, stem=True)  # 정규화 및 어간 추출
        
        # Step 2-3: 명사, 동사, 형용사만 추출
        keywords = []
        for word, pos in pos_tags:
            # 명사(Noun), 동사(Verb), 형용사(Adjective)만 선택
            if pos in ['Noun', 'Verb', 'Adjective'] and len(word) > 1:
                # Step 2-4: 불용어 제거
                if word not in self.stop_words:
                    keywords.append(word)
        
        return keywords
    
    # Step 3: 배치 처리
    def extract_keywords_batch(self, texts: List[str]) -> List[List[str]]:
        """
        여러 텍스트의 키워드를 배치로 추출합니다.
        Step 3-1: 텍스트 리스트 순회
        Step 3-2: 각 텍스트에 대해 키워드 추출
        """
        results = []
        # Step 3-1: 텍스트 리스트 순회
        for text in texts:
            # Step 3-2: 각 텍스트에 대해 키워드 추출
            results.append(self.extract_keywords(text))
        return results
    
    # Step 4: 쿼리 정규화
    def normalize_query(self, query: str) -> str:
        """
        쿼리를 정규화합니다 (동의어 처리).
        Step 4-1: 동의어 사전 정의
        Step 4-2: 동의어 치환 수행
        """
        # Step 4-1: 동의어 사전 정의
        synonyms = {
            '수강신청': '수강신청',
            '수강': '수강신청',           # '수강' → '수강신청'으로 통일
            '신청': '신청',
            '접수': '신청',               # '접수' → '신청'으로 통일
            '장학금': '장학금',
            '장학': '장학금',             # '장학' → '장학금'으로 통일
            '졸업': '졸업',
            '졸업사정': '졸업',           # '졸업사정' → '졸업'으로 통일
            '계절학기': '계절학기',
            '하계': '계절학기',           # '하계' → '계절학기'로 통일
            '동계': '계절학기',           # '동계' → '계절학기'로 통일
            '상상더학기': '상상더학기',
            '상상더': '상상더학기'        # '상상더' → '상상더학기'로 통일
        }
        
        # Step 4-2: 동의어 치환 수행
        normalized = query
        for original, synonym in synonyms.items():
            normalized = normalized.replace(original, synonym)
        
        return normalized
    
    # Step 5: 의미적 유사도 계산
    def calculate_semantic_similarity(self, query_keywords: List[str], doc_keywords: List[str]) -> float:
        """
        쿼리와 문서 간의 의미적 유사도를 계산합니다.
        Step 5-1: 완전 매칭 점수 계산
        Step 5-2: 부분 매칭 점수 계산
        Step 5-3: 최종 점수 결합
        """
        if not query_keywords or not doc_keywords:
            return 0.0
        
        # Step 5-1: 완전 매칭 점수 계산 (정확히 일치하는 키워드)
        matches = set(query_keywords) & set(doc_keywords)  # 교집합
        match_score = len(matches) / len(query_keywords)   # 매칭 비율
        
        # Step 5-2: 부분 매칭 점수 계산 (포함 관계)
        partial_matches = 0
        for q_keyword in query_keywords:
            for d_keyword in doc_keywords:
                # 포함 관계 확인 (예: '수강'이 '수강신청'에 포함됨)
                if q_keyword in d_keyword or d_keyword in q_keyword:
                    partial_matches += 1
                    break
        
        partial_score = partial_matches / len(query_keywords)  # 부분 매칭 비율
        
        # Step 5-3: 최종 점수 결합 (완전 매칭 70%, 부분 매칭 30%)
        final_score = 0.7 * match_score + 0.3 * partial_score
        
        return final_score

# Step 6: 전역 인스턴스 관리
_tokenizer = None

def get_tokenizer():
    """
    토크나이저 인스턴스를 반환합니다 (싱글톤 패턴).
    Step 6-1: 인스턴스 존재 확인
    Step 6-2: 없으면 새로 생성
    """
    global _tokenizer
    # Step 6-1: 인스턴스 존재 확인
    if _tokenizer is None:
        # Step 6-2: 없으면 새로 생성
        _tokenizer = KoreanTokenizer()
    return _tokenizer 