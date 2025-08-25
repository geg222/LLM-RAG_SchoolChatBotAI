from fastapi import APIRouter, Request
from service.chat_service import get_ai_response
from core.logger import logger

router = APIRouter()

@router.post("/")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message", "")
        language = data.get("language", "한국어")
        session_id = data.get("session_id", "default_session")
        
        if not user_message:
            return {"error": "message 파라미터가 필요합니다."}
        
        # AI 응답 생성
        response_text = get_ai_response(user_message, session_id)
        
        # 빈 응답 체크 개선
        if not response_text or not response_text.strip():
            logger.warning(f"빈 응답 생성됨 - 사용자 메시지: '{user_message}'")
            return {"error": "관련 정보를 찾지 못했습니다. 다른 키워드로 다시 시도해보세요."}
        
        # 응답이 너무 짧은 경우 (10자 미만)
        if len(response_text.strip()) < 10:
            logger.warning(f"응답이 너무 짧음: '{response_text}'")
            return {"error": "충분한 정보를 찾지 못했습니다. 다른 키워드로 다시 시도해보세요."}
            
        return {"answer": response_text}
        
    except Exception as e:
        logger.error(f"채팅 엔드포인트 오류: {e}")
        return {"error": f"서버 오류가 발생했습니다: {str(e)}"} 