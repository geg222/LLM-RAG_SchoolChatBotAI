"""
쿼리 확장 유틸리티 및 통계 기능
"""

from typing import List, Dict, Set
import re
from datetime import datetime

def extract_keywords(text: str) -> List[str]:
    """
    텍스트에서 주요 키워드를 추출합니다.
    """
    # 특수문자 제거
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # 단어 분리 및 필터링
    words = text.split()
    keywords = []
    
    for word in words:
        if len(word) > 1 and word not in ['이', '가', '을', '를', '의', '에', '에서']:
            keywords.append(word)
    
    return keywords

def get_expansion_statistics(query: str, expanded_queries: List[str], 
                           expansion_counts: Dict[str, int]) -> Dict:
    """
    쿼리 확장 통계 정보 반환
    """
    stats = {
        'original_query': query,
        'total_expanded': len(expanded_queries),
        'expansion_ratio': len(expanded_queries) / 1,  # 원본 대비 확장 비율
        'expansion_types': expansion_counts,
        'timestamp': datetime.now().isoformat()
    }
    
    return stats

def get_related_terms(query: str, synonyms: Dict, department_synonyms: Dict,
                     time_patterns: Dict, year_patterns: Dict, intent_patterns: Dict,
                     semantic_groups: Dict) -> Set[str]:
    """
    쿼리와 관련된 모든 용어를 반환합니다.
    """
    related_terms = set()
    
    # 원본 쿼리의 키워드
    keywords = extract_keywords(query)
    related_terms.update(keywords)
    
    # 동의어 추가
    for keyword in keywords:
        if keyword in synonyms:
            related_terms.update(synonyms[keyword])
    
    # 학과/트랙별 동의어 추가
    for dept, dept_synonyms in department_synonyms.items():
        if dept in query:
            related_terms.update(dept_synonyms)
    
    # 시간 패턴 추가
    for time_word, patterns in time_patterns.items():
        if time_word in query:
            related_terms.update(patterns)
    
    # 연도 패턴 추가
    for year, patterns in year_patterns.items():
        if year in query:
            related_terms.update(patterns)
    
    # 사용자 의도 패턴 추가
    for intent, patterns in intent_patterns.items():
        if intent in query:
            related_terms.update(patterns)
    
    # 의미적 그룹 추가
    for group_name, group_terms in semantic_groups.items():
        if any(term in query for term in group_terms):
            related_terms.update(group_terms)
    
    return related_terms

def expand_current_context(query: str) -> List[str]:
    """
    현재 시점 기반 동적 확장
    """
    expanded = []
    now = datetime.now()
    
    # 현재 학기 정보
    current_month = now.month
    if 3 <= current_month <= 7:
        current_semester = "1학기"
    else:
        current_semester = "2학기"
    
    # 현재 연도
    current_year = str(now.year)
    
    # 쿼리에 학기나 연도가 없으면 현재 정보 추가
    if '학기' in query and current_semester not in query:
        expanded.append(f"{query} {current_semester}")
    
    if current_year not in query and any(year in query for year in ['2024', '2025', '2023']):
        # 연도가 있지만 현재 연도가 없으면 추가
        expanded.append(f"{query} {current_year}")
    
    return expanded

def normalize_query(query: str) -> str:
    """
    쿼리를 정규화합니다.
    """
    # 기본 정규화
    normalized = query.strip()
    
    # 연속된 공백 제거
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized

def calculate_expansion_effectiveness(original_results: List, expanded_results: List) -> Dict:
    """
    확장 효과성 계산
    """
    if not original_results:
        return {'improvement': 0.0, 'new_results': len(expanded_results)}
    
    # 새로운 결과 수
    new_results = len(set(expanded_results) - set(original_results))
    
    # 개선율 계산
    improvement = (new_results / len(original_results)) * 100 if original_results else 0
    
    return {
        'improvement': improvement,
        'new_results': new_results,
        'original_count': len(original_results),
        'expanded_count': len(expanded_results)
    }

def filter_relevant_expansions(expanded_queries: List[str], 
                             relevance_threshold: float = 0.5) -> List[str]:
    """
    관련성 기준으로 확장된 쿼리를 필터링합니다.
    """
    # 간단한 관련성 점수 계산 (키워드 중복도 기반)
    scored_queries = []
    
    for query in expanded_queries:
        keywords = extract_keywords(query)
        # 키워드 수가 적절한 범위에 있는지 확인
        if 2 <= len(keywords) <= 8:  # 너무 짧거나 긴 쿼리 제외
            scored_queries.append(query)
    
    return scored_queries[:20]  # 상위 20개만 반환

def generate_expansion_report(query: str, expanded_queries: List[str], 
                            stats: Dict) -> str:
    """
    확장 결과 리포트 생성
    """
    report = f"""
=== 쿼리 확장 리포트 ===
원본 쿼리: {query}
확장된 쿼리 수: {len(expanded_queries)}
확장 비율: {stats.get('expansion_ratio', 0):.1f}

확장 유형별 통계:
"""
    
    for exp_type, count in stats.get('expansion_types', {}).items():
        if count > 0:
            report += f"  - {exp_type}: {count}개\n"
    
    report += f"\n상위 확장 쿼리들:\n"
    for i, expanded_query in enumerate(expanded_queries[:5], 1):
        report += f"  {i}. {expanded_query}\n"
    
    return report 