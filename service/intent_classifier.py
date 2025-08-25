"""
의도 분류 서비스
사용자 질의의 의도를 분류하고 최적화된 응답 제공
"""

from typing import Dict, List, Tuple
import re
from core.logger import logger

class IntentClassifier:
    def __init__(self):
        # 의도별 키워드 패턴 정의
        self.intent_patterns = {
            "정보_조회": {
                "keywords": ["언제", "어디서", "어떻게", "무엇", "누가", "왜", "몇", "얼마"],
                "patterns": [
                    r"언제.*",
                    r"어디서.*",
                    r"어떻게.*",
                    r"무엇.*",
                    r"누가.*",
                    r"왜.*",
                    r"몇.*",
                    r"얼마.*"
                ]
            },
            "신청_절차": {
                "keywords": ["신청", "접수", "등록", "신고", "제출", "출원", "지원"],
                "patterns": [
                    r".*신청.*",
                    r".*접수.*",
                    r".*등록.*",
                    r".*신고.*",
                    r".*제출.*",
                    r".*출원.*",
                    r".*지원.*"
                ]
            },
            "일정_확인": {
                "keywords": ["일정", "기간", "날짜", "시기", "마감", "시작", "종료"],
                "patterns": [
                    r".*일정.*",
                    r".*기간.*",
                    r".*날짜.*",
                    r".*시기.*",
                    r".*마감.*",
                    r".*시작.*",
                    r".*종료.*"
                ]
            },
            "문의": {
                "keywords": ["문의", "질문", "궁금", "알려", "확인", "찾다"],
                "patterns": [
                    r".*문의.*",
                    r".*질문.*",
                    r".*궁금.*",
                    r".*알려.*",
                    r".*확인.*",
                    r".*찾다.*"
                ]
            },
            "장학금": {
                "keywords": ["장학금", "장학", "학비", "지원", "혜택", "혜택"],
                "patterns": [
                    r".*장학금.*",
                    r".*장학.*",
                    r".*학비.*",
                    r".*지원.*",
                    r".*혜택.*"
                ]
            },
            "졸업": {
                "keywords": ["졸업", "졸업사정", "졸업요건", "졸업조건", "졸업예정"],
                "patterns": [
                    r".*졸업.*",
                    r".*졸업사정.*",
                    r".*졸업요건.*",
                    r".*졸업조건.*",
                    r".*졸업예정.*"
                ]
            },
            "수강신청": {
                "keywords": ["수강신청", "수강", "신청", "접수", "등록", "수강정정"],
                "patterns": [
                    r".*수강신청.*",
                    r".*수강.*",
                    r".*신청.*",
                    r".*접수.*",
                    r".*등록.*",
                    r".*수강정정.*"
                ]
            },
            "계절학기": {
                "keywords": ["계절학기", "하계", "동계", "여름학기", "겨울학기"],
                "patterns": [
                    r".*계절학기.*",
                    r".*하계.*",
                    r".*동계.*",
                    r".*여름학기.*",
                    r".*겨울학기.*"
                ]
            }
        }
    
    def classify_intent(self, query: str) -> Tuple[str, float]:
        """
        사용자 질의의 의도를 분류합니다.
        
        Args:
            query: 사용자 질의
            
        Returns:
            (의도, 신뢰도): 분류된 의도와 신뢰도 점수
        """
        query_lower = query.lower()
        intent_scores = {}
        
        for intent, config in self.intent_patterns.items():
            score = 0.0
            
            # 키워드 매칭 점수
            keyword_matches = sum(1 for keyword in config["keywords"] if keyword in query_lower)
            keyword_score = keyword_matches / len(config["keywords"]) * 0.6
            
            # 패턴 매칭 점수
            pattern_matches = sum(1 for pattern in config["patterns"] if re.search(pattern, query_lower))
            pattern_score = pattern_matches / len(config["patterns"]) * 0.4
            
            score = keyword_score + pattern_score
            intent_scores[intent] = score
        
        # 가장 높은 점수의 의도 선택
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
            
            # 신뢰도가 낮으면 기본 의도로 분류
            if confidence < 0.3:
                best_intent = "일반_질문"
                confidence = 0.5
            
            logger.info(f"의도 분류: '{query}' -> {best_intent} (신뢰도: {confidence:.2f})")
            return best_intent, confidence
        
        return "일반_질문", 0.5
    
    def get_intent_specific_prompt(self, intent: str, query: str) -> str:
        """
        의도별 최적화된 프롬프트를 생성합니다.
        
        Args:
            intent: 분류된 의도
            query: 사용자 질의
            
        Returns:
            의도별 최적화된 프롬프트
        """
        base_prompt = "오늘 날짜는 {current_date}입니다. 당신의 이름은 상상부기이고, 학생들에게 한성대학교 공지사항을 요약해주는 챗봇입니다."
        
        intent_prompts = {
            "정보_조회": f"{base_prompt} 학생이 정보를 조회하고 있습니다. 정확하고 구체적인 정보를 제공해주세요.",
            "신청_절차": f"{base_prompt} 학생이 신청 절차를 문의하고 있습니다. 단계별로 명확하게 안내해주세요.",
            "일정_확인": f"{base_prompt} 학생이 일정을 확인하고 있습니다. 날짜와 시간을 명확하게 안내해주세요.",
            "문의": f"{base_prompt} 학생이 일반적인 문의를 하고 있습니다. 친근하고 도움이 되는 답변을 제공해주세요.",
            "장학금": f"{base_prompt} 학생이 장학금 관련 문의를 하고 있습니다. 장학금 종류, 신청 조건, 혜택을 자세히 안내해주세요.",
            "졸업": f"{base_prompt} 학생이 졸업 관련 문의를 하고 있습니다. 졸업 요건, 절차, 일정을 상세히 안내해주세요.",
            "수강신청": f"{base_prompt} 학생이 수강신청 관련 문의를 하고 있습니다. 수강신청 방법, 기간, 주의사항을 자세히 안내해주세요.",
            "계절학기": f"{base_prompt} 학생이 계절학기 관련 문의를 하고 있습니다. 계절학기 수강신청, 일정, 수강료를 상세히 안내해주세요.",
            "일반_질문": f"{base_prompt} 학생의 질문에 친근하고 정확한 답변을 제공해주세요."
        }
        
        return intent_prompts.get(intent, intent_prompts["일반_질문"])
    
    def get_intent_priority(self, intent: str) -> int:
        """
        의도별 우선순위를 반환합니다.
        
        Args:
            intent: 분류된 의도
            
        Returns:
            우선순위 (낮을수록 높은 우선순위)
        """
        priority_map = {
            "신청_절차": 1,      # 가장 높은 우선순위
            "일정_확인": 2,
            "졸업": 3,
            "수강신청": 4,
            "장학금": 5,
            "계절학기": 6,
            "정보_조회": 7,
            "문의": 8,
            "일반_질문": 9       # 가장 낮은 우선순위
        }
        
        return priority_map.get(intent, 9)

# 전역 인스턴스
_intent_classifier = None

def get_intent_classifier():
    """의도 분류기 인스턴스를 반환합니다."""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier 