import requests
from service.rag_service import get_retriever
from service.conversation_service import get_conversation_service
from service.intent_classifier import get_intent_classifier
from core.logger import logger
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from datetime import datetime

_llm_cache = {}
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def _clean_markdown_format(text):
    """
    마크다운 형식을 정리하여 깔끔한 텍스트로 변환합니다.
    """
    import re
    
    # **텍스트** → 텍스트 (굵은 글씨 제거)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # [텍스트](링크) → 텍스트 (링크 형식 정리)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # 불필요한 마크다운 기호 제거
    text = re.sub(r'#{1,6}\s+', '', text)  # 헤딩 제거
    text = re.sub(r'\*\s+', '• ', text)    # 리스트 기호 정리
    
    # 연속된 공백 정리
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def get_llm(model='gpt-4o'):
    if model not in _llm_cache:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is not None:
            api_key = SecretStr(api_key)
        _llm_cache[model] = ChatOpenAI(model=model, api_key=api_key)
    return _llm_cache[model]

def get_ai_response(user_message, session_id="default_session"):
    """
    Gets and processes AI response using enhanced RAG approach with conversation context and intent classification.
    """
    try:
        # Get services
        llm = get_llm()
        conversation_service = get_conversation_service()
        intent_classifier = get_intent_classifier()
        
        # Get session history
        session_history = get_session_history(session_id)
        chat_history = session_history.messages
        
        # Get conversation context
        conversation_context = conversation_service.get_context(session_id, max_turns=3)
        
        # Classify user intent
        intent, confidence = intent_classifier.classify_intent(user_message)
        logger.info(f"Intent classified: {intent} (confidence: {confidence:.2f})")
        
        # Get current date
        current_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Retrieve documents using the enhanced retriever
        retrieved_docs = get_retriever(user_message)
        logger.info(f"Retrieved {len(retrieved_docs)} documents for the query.")

        if not retrieved_docs:
            logger.warning("No documents were retrieved.")
            return "정확한 정보를 찾지 못했습니다. 😅\n\n다른 키워드로 다시 물어보시거나, 한성대학교 학생지원센터에 직접 문의해보세요!"
        else:
            for i, doc in enumerate(retrieved_docs[:3]):
                logger.info(f"Retrieved Doc {i+1}: {doc.metadata.get('title', 'N/A')}")

        # Create context from documents
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        # Create enhanced system prompt with intent-specific guidance
        base_prompt = intent_classifier.get_intent_specific_prompt(intent, user_message)
        
        system_prompt = (
            f"{base_prompt} "
            "반드시 한성대학교 공식 공지사항의 URL을 포함해서, 학생이 바로 클릭할 수 있도록 안내해드리겠습니다. "
            "\n\n"
            "답변 형식을 다음과 같이 정확히 지켜서 답변해줘:\n"
            "\n"
            "여기 [질문 키워드]에 대한 공지사항이 있습니다!\n"
            "\n"
            "1. 공지사항 제목: [제목]\n"
            "\n"
            "2. 주요 내용 요약: [내용 요약]\n"
            "\n"
            "3. 중요 정보: [신청기간, 접수기간, 모집기간, 안내사항 등 공지사항에 포함된 중요 정보]\n"
            "\n"
            "4. 신청 방법: [신청/접수 방법이 있는 경우에만 포함]\n"
            "\n"
            "5. 공식 링크\n[링크 URL만 정확히 입력]\n"
            "\n"
            "[마무리 멘트]\n"
            "\n"
            "⚠️ 중요한 규칙: "
            "• 마크다운 형식(**굵은 글씨**)을 사용하지 말고 일반 텍스트로 답변해줘. "
            "• 줄바꿈을 적절히 사용해서 가독성을 높여줘. "
            "• 공지사항에 신청기간이 없으면 '3. 중요 정보'에 다른 중요 정보를 포함해줘. "
            "• 신청 방법이 없으면 해당 항목을 생략해줘. "
            "• 검색된 문서 중에서 질문과 관련된 공지사항이 있으면 반드시 답변해줘! "
            "• 제목에 정확히 일치하지 않아도 내용이 관련되면 답변해줘. "
            "• 예를 들어 '트랙변경'을 물어보면 제목에 '트랙변경'이 포함된 공지사항을 찾아서 답변해줘. "
            "• 5. 공식 링크에는 반드시 https://로 시작하는 완전한 URL만 입력해줘. "
            "검색된 문서가 전혀 관련이 없을 때는 다음과 같이 답변해줘:\n"
            "\n"
            "정확한 정보를 찾지 못했습니다. 😅\n\n"
            "[질문 내용]에 대한 공지사항은 현재 확인할 수 없습니다.\n\n"
            "한성대학교 (☎760-4219)에 직접 문의하거나, "
            "한성대학교 공식 홈페이지(https://www.hansung.ac.kr)에서 공지사항을 확인해보세요!\n\n"
            "--- 검색된 관련 공지사항 ---\n"
            "{context}"
            "--- 끝 ---\n"
        )
        
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        
        # Call the LLM directly
        response = llm.invoke(qa_prompt.format_messages(
            input=user_message,
            chat_history=chat_history,
            context=context,
            current_date=current_date_str
        ))
        
        ai_response = response.content

        # 대화 히스토리에 추가
        conversation_service.add_to_history(session_id, user_message, ai_response)
        
        # 마크다운 형식 정리 (불필요한 ** 제거)
        ai_response = _clean_markdown_format(ai_response)

        # Add messages to session history
        from langchain_core.messages import HumanMessage, AIMessage
        session_history.add_user_message(user_message)
        session_history.add_ai_message(ai_response)

        if not ai_response.strip():
            logger.warning("LLM response was empty.")
            return "찾은 정보가 부족해서 정확한 답변을 드리기 어렵습니다. 😅\n\n다른 키워드로 다시 물어보시거나, 한성대학교 학생지원센터에 직접 문의해보세요!"

        return ai_response

    except Exception as e:
        logger.error(f"Error during AI response generation: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return "챗봇 응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요!" 