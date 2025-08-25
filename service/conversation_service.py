"""
대화 맥락 관리 서비스
세션별 대화 히스토리 관리 및 맥락 정보 제공
"""

from typing import List, Dict, Optional
from datetime import datetime
from core.logger import logger

class ConversationService:
    def __init__(self):
        self.conversations = {}  # session_id별 대화 히스토리
        self.max_history = 10    # 최대 저장할 대화 수
    
    def add_to_history(self, session_id: str, user_message: str, bot_response: str):
        """대화 히스토리에 사용자 메시지와 봇 응답을 추가합니다."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        conversation_entry = {
            'user': user_message,
            'bot': bot_response,
            'timestamp': datetime.now()
        }
        
        self.conversations[session_id].append(conversation_entry)
        
        # 최대 히스토리 수 제한
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
        
        logger.info(f"대화 히스토리 추가 - 세션: {session_id}, 총 대화 수: {len(self.conversations[session_id])}")
    
    def get_context(self, session_id: str, max_turns: int = 5) -> List[Dict]:
        """최근 N개 대화를 맥락으로 제공합니다."""
        if session_id in self.conversations:
            recent_conversations = self.conversations[session_id][-max_turns:]
            logger.info(f"맥락 정보 제공 - 세션: {session_id}, 제공 대화 수: {len(recent_conversations)}")
            return recent_conversations
        return []
    
    def get_conversation_summary(self, session_id: str) -> str:
        """대화 세션의 요약 정보를 제공합니다."""
        if session_id not in self.conversations:
            return ""
        
        conversations = self.conversations[session_id]
        if not conversations:
            return ""
        
        # 주요 키워드 추출
        all_text = " ".join([conv['user'] + " " + conv['bot'] for conv in conversations])
        
        # 간단한 요약 생성
        summary = f"총 {len(conversations)}개 대화, "
        if len(conversations) > 0:
            first_topic = conversations[0]['user'][:20] + "..."
            summary += f"첫 질문: {first_topic}"
        
        return summary
    
    def clear_history(self, session_id: str):
        """특정 세션의 대화 히스토리를 초기화합니다."""
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"대화 히스토리 초기화 - 세션: {session_id}")
    
    def get_all_sessions(self) -> List[str]:
        """모든 활성 세션 ID를 반환합니다."""
        return list(self.conversations.keys())

# 전역 인스턴스
_conversation_service = None

def get_conversation_service():
    """대화 맥락 관리 서비스 인스턴스를 반환합니다."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service 