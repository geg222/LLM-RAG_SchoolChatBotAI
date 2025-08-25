from core.vectorstore import get_vectorstore
from core.hybrid_search import get_hybrid_search_engine
from core.korean_tokenizer import get_tokenizer
from core.query_expansion import get_query_expansion
from core.logger import logger

def get_retriever(user_message):
    """
    향상된 검색: 하이브리드 서치, 쿼리 확장, 재순위화를 통한 정확도 향상
    """
    try:
        # 하이브리드 서치 사용 (벡터 + BM25)
        hybrid_engine = get_hybrid_search_engine()
        hybrid_results = hybrid_engine.search(user_message, top_k=8, alpha=0.6)
        
        # 쿼리 확장을 통한 추가 검색
        query_expansion = get_query_expansion()
        expanded_queries = query_expansion.expand_query(user_message)
        logger.info(f"쿼리 확장: '{user_message}' -> {expanded_queries}")
        
        # 확장된 쿼리로 추가 검색
        vectorstore = get_vectorstore()
        additional_docs = []
        for query in expanded_queries[:2]:  # 상위 2개 확장 쿼리만 사용
            search_kwargs = {"k": 5}
            retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
            docs = retriever.invoke(query)
            additional_docs.extend(docs)
        
        # 하이브리드 결과를 LangChain Document 형식으로 변환
        from langchain_core.documents import Document
        hybrid_docs = []
        for result in hybrid_results:
            doc = Document(
                page_content=result['content'],
                metadata=result['metadata']
            )
            hybrid_docs.append(doc)
        
        # 모든 결과 통합
        all_docs = hybrid_docs + additional_docs
        
        # 중복 제거
        unique_docs = _remove_duplicates(all_docs)
        
        # 향상된 재순위화
        re_ranked_docs = _re_rank_by_keywords(unique_docs, user_message)
        
        logger.info(f"하이브리드 검색 완료: {len(hybrid_results)}개 하이브리드 결과, {len(additional_docs)}개 추가 결과")
        
        return re_ranked_docs[:5]
        
    except Exception as e:
        logger.error(f"하이브리드 검색 실패, 벡터 검색으로 폴백: {e}")
        # 실패 시 기존 벡터 검색 사용
        return _fallback_vector_search(user_message)

def _fallback_vector_search(user_message):
    """
    하이브리드 검색 실패 시 사용하는 벡터 검색 폴백
    """
    vectorstore = get_vectorstore()
    query_expansion = get_query_expansion()
    
    # 쿼리 확장
    expanded_queries = query_expansion.expand_query(user_message)
    
    # 다중 쿼리 검색
    all_docs = []
    for query in expanded_queries[:3]:
        search_kwargs = {"k": 8}
        retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
        docs = retriever.invoke(query)
        all_docs.extend(docs)
    
    # 중복 제거 및 재순위화
    unique_docs = _remove_duplicates(all_docs)
    re_ranked_docs = _re_rank_by_keywords(unique_docs, user_message)
    
    return re_ranked_docs[:5]

def _remove_duplicates(docs):
    """
    중복 문서를 제거합니다.
    """
    seen = set()
    unique_docs = []
    
    for doc in docs:
        # 제목과 내용의 해시를 사용하여 중복 판단
        doc_hash = hash(f"{doc.metadata.get('title', '')}:{doc.page_content[:100]}")
        if doc_hash not in seen:
            seen.add(doc_hash)
            unique_docs.append(doc)
    
    return unique_docs

def _re_rank_by_keywords(docs, query):
    """
    키워드 매칭 및 의미적 유사도를 기반으로 검색 결과를 재순위화합니다.
    """
    tokenizer = get_tokenizer()
    
    # 쿼리 정규화 및 키워드 추출
    normalized_query = tokenizer.normalize_query(query)
    query_keywords = tokenizer.extract_keywords(normalized_query)
    
    def calculate_enhanced_score(doc):
        title = doc.metadata.get('title', '')
        content = doc.page_content
        
        # 제목과 내용에서 키워드 추출
        title_keywords = tokenizer.extract_keywords(title)
        content_keywords = tokenizer.extract_keywords(content)
        
        # 1. 제목 키워드 매칭 점수 (가중치: 0.35)
        title_semantic_score = tokenizer.calculate_semantic_similarity(query_keywords, title_keywords) * 0.35
        
        # 2. 내용 키워드 매칭 점수 (가중치: 0.40)
        content_semantic_score = tokenizer.calculate_semantic_similarity(query_keywords, content_keywords) * 0.40
        
        # 3. 정확한 키워드 매칭 점수 (가중치: 0.25)
        exact_title_matches = sum(1 for keyword in query_keywords if keyword in title.lower())
        exact_content_matches = sum(1 for keyword in query_keywords if keyword in content.lower())
        exact_score = (exact_title_matches * 2 + exact_content_matches) * 0.25
        
        # 최종 점수 (날짜 가중치 제거)
        total_score = title_semantic_score + content_semantic_score + exact_score
        
        return total_score
    
    # 향상된 점수로 정렬
    re_ranked = sorted(docs, key=calculate_enhanced_score, reverse=True)
    
    # 로그로 재순위화 결과 기록
    logger.info(f"검색 쿼리: '{query}' -> 정규화: '{normalized_query}' -> 키워드: {query_keywords}")
    for i, doc in enumerate(re_ranked[:3], 1):
        score = calculate_enhanced_score(doc)
        title = doc.metadata.get('title', '제목 없음')
        logger.info(f"  {i}위: {title} (점수: {score:.3f})")
    
    return re_ranked

def get_hybrid_retriever(user_message, alpha: float = 0.6):
    """
    하이브리드 검색을 수행하는 리트리버를 반환합니다.
    
    Args:
        user_message: 사용자 메시지
        alpha: 벡터 검색 가중치 (0.0 ~ 1.0)
    
    Returns:
        하이브리드 검색 결과
    """
    try:
        hybrid_engine = get_hybrid_search_engine()
        results = hybrid_engine.search(user_message, top_k=5, alpha=alpha)
        
        # LangChain Document 형식으로 변환
        from langchain_core.documents import Document
        documents = []
        for result in results:
            doc = Document(
                page_content=result['content'],
                metadata=result['metadata']
            )
            documents.append(doc)
        
        return documents
        
    except Exception as e:
        logger.error(f"하이브리드 검색 실패: {e}")
        # 실패 시 기존 벡터 검색 사용
        return get_retriever(user_message).invoke(user_message) 

def get_retriever_for_chain():
    """
    Creates a retriever function that can be used with create_history_aware_retriever.
    This function takes a query string and returns documents.
    """
    def retriever_function(query: str):
        vectorstore = get_vectorstore()
        search_kwargs = {"k": 10}
        retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

        docs = retriever.invoke(query)
        logger.info(f"Retrieved {len(docs)} documents for query: '{query}'")

        # Re-ranking
        query_keywords = query.split()
        re_ranked_docs = sorted(
            docs,
            key=lambda doc: sum(1 for keyword in query_keywords if keyword in doc.metadata.get('title', '').lower()),
            reverse=True
        )
        
        return re_ranked_docs

    return retriever_function 
