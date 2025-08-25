"""
고급 쿼리 확장 기능
사용자 컨텍스트, 계절별, 긴급도 등 고급 확장 기능
"""

from typing import List, Dict
from datetime import datetime
from core.query_expansion.data import (
    DEPARTMENT_SYNONYMS, STUDENT_TYPES, DOCUMENT_TYPES,
    URGENT_OPERATIONS, URGENT_KEYWORDS, FAQ_PATTERNS,
    ACADEMIC_CALENDAR, SEASONAL_KEYWORDS
)

class AdvancedQueryExpansion:
    """고급 쿼리 확장 기능 클래스"""
    
    def expand_query_advanced(self, query: str, user_context: Dict = None) -> List[str]:
        """
        고급 쿼리 확장 (사용자 컨텍스트 기반)
        """
        expanded_queries = [query]
        
        if user_context:
            # 사용자 컨텍스트 기반 추가 확장
            expanded_queries.extend(self._expand_by_user_context(query, user_context))
        
        return list(set(expanded_queries))
    
    def _expand_by_user_context(self, query: str, user_context: Dict) -> List[str]:
        """사용자 컨텍스트 기반 확장"""
        expanded = []
        
        # 사용자 학과/트랙 정보가 있으면 특화 확장
        if 'department' in user_context:
            dept = user_context['department']
            if dept in DEPARTMENT_SYNONYMS:
                for synonym in DEPARTMENT_SYNONYMS[dept]:
                    expanded_query = f"{query} {synonym}"
                    expanded.append(expanded_query)
        
        # 사용자 학년 정보가 있으면 학년별 특화 확장
        if 'grade' in user_context:
            grade = user_context['grade']
            if grade == 1:
                expanded.extend([f"{query} 신입생", f"{query} 1학년"])
            elif grade == 4:
                expanded.extend([f"{query} 졸업예정", f"{query} 4학년"])
        
        return expanded
    
    def expand_query_by_season(self, query: str) -> List[str]:
        """계절별 특화 쿼리 확장"""
        expanded = []
        now = datetime.now()
        month = now.month
        
        # 계절별 특화 키워드
        if 3 <= month <= 5:  # 봄
            spring_keywords = SEASONAL_KEYWORDS['spring']
            for keyword in spring_keywords:
                if keyword not in query:
                    expanded.append(f"{query} {keyword}")
        
        elif 6 <= month <= 8:  # 여름
            summer_keywords = SEASONAL_KEYWORDS['summer']
            for keyword in summer_keywords:
                if keyword not in query:
                    expanded.append(f"{query} {keyword}")
        
        elif 9 <= month <= 11:  # 가을
            fall_keywords = SEASONAL_KEYWORDS['fall']
            for keyword in fall_keywords:
                if keyword not in query:
                    expanded.append(f"{query} {keyword}")
        
        else:  # 겨울
            winter_keywords = SEASONAL_KEYWORDS['winter']
            for keyword in winter_keywords:
                if keyword not in query:
                    expanded.append(f"{query} {keyword}")
        
        return expanded
    
    def expand_query_by_urgency(self, query: str) -> List[str]:
        """긴급도 기반 쿼리 확장"""
        expanded = []
        
        for operation in URGENT_OPERATIONS:
            if operation in query:
                for urgent_keyword in URGENT_KEYWORDS:
                    expanded.append(f"{query} {urgent_keyword}")
                break
        
        return expanded
    
    def expand_query_by_frequency(self, query: str) -> List[str]:
        """빈도 기반 쿼리 확장"""
        expanded = []
        
        for question_word, answers in FAQ_PATTERNS.items():
            if question_word in query:
                for answer in answers:
                    expanded.append(f"{query} {answer}")
        
        return expanded
    
    def expand_query_by_academic_calendar(self, query: str) -> List[str]:
        """학사일정 기반 쿼리 확장"""
        expanded = []
        now = datetime.now()
        month = now.month
        
        if month in ACADEMIC_CALENDAR:
            for keyword in ACADEMIC_CALENDAR[month]:
                if keyword not in query:
                    expanded.append(f"{query} {keyword}")
        
        return expanded
    
    def expand_query_by_student_type(self, query: str, student_type: str = None) -> List[str]:
        """학생 유형별 쿼리 확장"""
        expanded = []
        
        if student_type and student_type in STUDENT_TYPES:
            for keyword in STUDENT_TYPES[student_type]:
                if keyword not in query:
                    expanded.append(f"{query} {keyword}")
        
        return expanded
    
    def expand_query_by_document_type(self, query: str) -> List[str]:
        """문서 유형별 쿼리 확장"""
        expanded = []
        
        for doc_type, keywords in DOCUMENT_TYPES.items():
            if doc_type in query:
                for keyword in keywords:
                    if keyword not in query:
                        expanded.append(f"{query} {keyword}")
        
        return expanded

# 전역 인스턴스
_advanced_expansion = None

def get_advanced_expansion():
    """고급 확장 인스턴스를 반환합니다."""
    global _advanced_expansion
    if _advanced_expansion is None:
        _advanced_expansion = AdvancedQueryExpansion()
    return _advanced_expansion 