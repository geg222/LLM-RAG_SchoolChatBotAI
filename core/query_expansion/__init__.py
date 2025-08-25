"""
쿼리 확장 및 동의어 처리를 통한 검색 정확도 향상
"""

from typing import List, Dict, Set
from core.korean_tokenizer import get_tokenizer
from core.query_expansion.data import (
    SYNONYMS, DEPARTMENT_SYNONYMS, TIME_PATTERNS, YEAR_PATTERNS,
    INTENT_PATTERNS, CONTEXT_RULES, SEMANTIC_GROUPS
)
from core.query_expansion.utils import (
    extract_keywords, get_expansion_statistics, get_related_terms,
    expand_current_context
)

class QueryExpansion:
    """
    쿼리 확장 및 동의어 처리를 통한 검색 정확도 향상
    """
    
    # Step 1: 초기화
    def __init__(self):
        """
        쿼리 확장 시스템 초기화
        1. 한국어 토크나이저 초기화
        """
        # 한국어 토크나이저 초기화
        self.tokenizer = get_tokenizer()
    
    # Step 2: 메인 쿼리 확장 함수
    def expand_query(self, query: str) -> List[str]:
        """
        쿼리를 확장하여 관련 키워드를 추가합니다.
        1. 원본 쿼리 포함
        2.  9가지 확장 방법 적용
        3. 중복 제거 및 반환
        """
        #원본 쿼리 포함
        expanded_queries = [query]
        
        # 9가지 확장 방법 적용
        # 1. 기본 동의어 확장
        expanded_queries.extend(self._expand_synonyms(query))
        
        # 2. 학과/트랙별 특화 확장
        expanded_queries.extend(self._expand_department_specific(query))
        
        # 3. 시간 패턴 확장
        expanded_queries.extend(self._expand_time_patterns(query))
        
        # 4. 연도 패턴 확장
        expanded_queries.extend(self._expand_year_patterns(query))
        
        # 5. 사용자 의도 기반 확장
        expanded_queries.extend(self._expand_intent_patterns(query))
        
        # 6. 컨텍스트 기반 확장
        expanded_queries.extend(self._expand_by_context(query))
        
        # 7. 의미적 그룹 기반 확장
        expanded_queries.extend(self._expand_semantic_groups(query))
        
        # 8. 키워드 조합 확장
        expanded_queries.extend(self._expand_keyword_combinations(query))
        
        # 9. 현재 시점 기반 동적 확장
        expanded_queries.extend(expand_current_context(query))
        
        # 중복 제거 및 반환
        return list(set(expanded_queries))  # 중복 제거
    
    # 기본 동의어 확장
    def _expand_synonyms(self, query: str) -> List[str]:
        """
        기본 동의어 확장
        1. 동의어 사전에서 매칭되는 단어 찾기
        2. 동의어로 치환하여 확장 쿼리 생성
        """
        expanded = []
        # 동의어 사전에서 매칭되는 단어 찾기
        for original, synonyms in SYNONYMS.items():
            if original in query:
                # 동의어로 치환하여 확장 쿼리 생성
                for synonym in synonyms:
                    expanded_query = query.replace(original, synonym)
                    expanded.append(expanded_query)
        return expanded
    
    # 학과/트랙별 특화 확장
    def _expand_department_specific(self, query: str) -> List[str]:
        """
        학과/트랙별 특화 확장
        1.  학과별 동의어 사전에서 매칭
        2.  학과별 특화 용어로 확장
        """
        expanded = []
        # 학과별 동의어 사전에서 매칭
        for dept, synonyms in DEPARTMENT_SYNONYMS.items():
            if dept in query:
                # 학과별 특화 용어로 확장
                for synonym in synonyms:
                    expanded_query = query.replace(dept, synonym)
                    expanded.append(expanded_query)
        return expanded
    
    # Step 5: 시간 패턴 확장
    def _expand_time_patterns(self, query: str) -> List[str]:
        """
        시간 패턴 확장
        1 시간 관련 단어 매칭
        2. 다양한 시간 표현으로 확장
        """
        expanded = []
        # 시간 관련 단어 매칭
        for time_word, patterns in TIME_PATTERNS.items():
            if time_word in query:
                # 다양한 시간 표현으로 확장
                for pattern in patterns:
                    expanded_query = query.replace(time_word, pattern)
                    expanded.append(expanded_query)
        return expanded
    
    # 연도 패턴 확장
    def _expand_year_patterns(self, query: str) -> List[str]:
        """
        연도 패턴 확장
        1. 연도 관련 단어 매칭
        2. 다양한 연도 표현으로 확장
        """
        expanded = []
        # 연도 관련 단어 매칭
        for year, patterns in YEAR_PATTERNS.items():
            if year in query:
                # 다양한 연도 표현으로 확장
                for pattern in patterns:
                    expanded_query = query.replace(year, pattern)
                    expanded.append(expanded_query)
        return expanded
    
    # Step 7: 사용자 의도 기반 확장
    def _expand_intent_patterns(self, query: str) -> List[str]:
        """
        사용자 의도 기반 확장
        1. 의도 관련 단어 매칭
        2. 의도별 관련 표현으로 확장
        """
        expanded = []
        # 의도 관련 단어 매칭
        for intent, patterns in INTENT_PATTERNS.items():
            if intent in query:
                # 의도별 관련 표현으로 확장
                for pattern in patterns:
                    expanded_query = query.replace(intent, pattern)
                    expanded.append(expanded_query)
        return expanded
    
    # Step 8: 컨텍스트 기반 확장
    def _expand_by_context(self, query: str) -> List[str]:
        """
        컨텍스트 기반으로 쿼리를 확장합니다.
        1. 쿼리에서 키워드 추출
        2. 컨텍스트 규칙에 따라 확장
        """
        expanded = []
        # 쿼리에서 키워드 추출
        keywords = extract_keywords(query)
        
        # 컨텍스트 규칙에 따라 확장
        for keyword in keywords:
            if keyword in CONTEXT_RULES:
                for context_word in CONTEXT_RULES[keyword]:
                    expanded_query = f"{query} {context_word}"
                    expanded.append(expanded_query)
        
        return expanded
    
    #  의미적 그룹 기반 확장
    def _expand_semantic_groups(self, query: str) -> List[str]:
        """
        의미적 그룹 기반 확장
        1. 쿼리에서 키워드 추출
        2. 의미적 그룹에서 관련 용어 찾기
        3. 같은 그룹의 다른 용어로 확장
        """
        expanded = []
        # 쿼리에서 키워드 추출
        keywords = extract_keywords(query)
        
        #의미적 그룹에서 관련 용어 찾기
        for keyword in keywords:
            for group_name, group_terms in SEMANTIC_GROUPS.items():
                if keyword in group_terms:
                    # 같은 그룹의 다른 용어로 확장
                    for term in group_terms:
                        if term != keyword:
                            expanded_query = query.replace(keyword, term)
                            expanded.append(expanded_query)
        
        return expanded
    
    # Step 10: 키워드 조합 확장
    def _expand_keyword_combinations(self, query: str) -> List[str]:
        """
        키워드 조합 확장
        Step 10-1: 쿼리에서 키워드 추출
        Step 10-2: 키워드 조합 생성
        """
        expanded = []
        # Step 10-1: 쿼리에서 키워드 추출
        keywords = extract_keywords(query)
        
        # Step 10-2: 키워드 조합 생성 (2개 이상 키워드가 있을 때)
        if len(keywords) >= 2:
            # 주요 키워드 조합
            for i in range(len(keywords)):
                for j in range(i+1, len(keywords)):
                    combined_query = f"{keywords[i]} {keywords[j]}"
                    expanded.append(combined_query)
        
        return expanded
    
    # Step 11: 관련 용어 조회
    def get_related_terms(self, query: str) -> Set[str]:
        """
        쿼리와 관련된 모든 용어를 반환합니다.
        Step 11-1: 모든 확장 데이터에서 관련 용어 수집
        """
        # Step 11-1: 모든 확장 데이터에서 관련 용어 수집
        return get_related_terms(
            query, SYNONYMS, DEPARTMENT_SYNONYMS, TIME_PATTERNS,
            YEAR_PATTERNS, INTENT_PATTERNS, SEMANTIC_GROUPS
        )
    
    # Step 12: 확장 통계 정보
    def get_expansion_statistics(self, query: str) -> Dict:
        """
        쿼리 확장 통계 정보 반환
        Step 12-1: 각 확장 방법별 개수 계산
        Step 12-2: 통계 정보 생성
        """
        # Step 12-1: 각 확장 방법별 개수 계산
        expanded_queries = self.expand_query(query)
        
        expansion_counts = {
            'synonyms': len(self._expand_synonyms(query)),           # 동의어 확장
            'department': len(self._expand_department_specific(query)), # 학과별 확장
            'time': len(self._expand_time_patterns(query)),          # 시간 패턴 확장
            'year': len(self._expand_year_patterns(query)),          # 연도 패턴 확장
            'intent': len(self._expand_intent_patterns(query)),      # 의도 기반 확장
            'context': len(self._expand_by_context(query)),          # 컨텍스트 확장
            'semantic': len(self._expand_semantic_groups(query)),    # 의미적 그룹 확장
            'combinations': len(self._expand_keyword_combinations(query)), # 키워드 조합 확장
            'current_context': len(expand_current_context(query)),   # 현재 컨텍스트 확장
        }
        
        # Step 12-2: 통계 정보 생성
        return get_expansion_statistics(query, expanded_queries, expansion_counts)

# Step 13: 전역 인스턴스 관리
_query_expansion = None

def get_query_expansion():
    """
    쿼리 확장 인스턴스를 반환합니다 (싱글톤 패턴).
    Step 13-1: 인스턴스 존재 확인
    Step 13-2: 없으면 새로 생성
    """
    global _query_expansion
    # Step 13-1: 인스턴스 존재 확인
    if _query_expansion is None:
        # Step 13-2: 없으면 새로 생성
        _query_expansion = QueryExpansion()
    return _query_expansion 