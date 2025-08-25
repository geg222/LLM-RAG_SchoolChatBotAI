from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
from core.vectorstore import get_vectorstore
from core.korean_tokenizer import get_tokenizer
from core.logger import logger
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class HybridSearchEngine:
    """
    하이브리드 검색 엔진: 벡터 검색(의미적 검색) + BM25 검색(키워드 검색)을 결합
    """
    
    # Step 1: 초기화 및 BM25 인덱스 구축 
    def __init__(self):
        """
        하이브리드 검색 엔진 초기화
        - 벡터스토어 연결
        - 한국어 토크나이저 초기화
        - BM25 인덱스 구축
        """
        self.vectorstore = get_vectorstore()      # Pinecone 벡터스토어
        self.tokenizer = get_tokenizer()          # 한국어 토크나이저
        self.bm25_index = None                    # BM25 인덱스
        self.documents = []                       # 문서 리스트
        self._build_bm25_index()                  # BM25 인덱스 구축
    
    # Step 2: BM25 인덱스 구축
    def _build_bm25_index(self):
        """
        BM25 인덱스를 구축
        1.  벡터스토어에서 모든 문서 가져오기
        2.  한국어 토크나이저로 키워드 추출
        3.  BM25 인덱스 생성
        """
        try:
            logger.info("BM25 인덱스 구축 중...")
            
            # Step 2-1: 벡터스토어에서 모든 문서 가져오기
            all_docs = self._get_all_documents_from_vectorstore()
        
            # Step 2-2: 한국어 토크나이저를 사용하여 문서 토큰화
            tokenized_docs = []
            for doc in all_docs:
                keywords = self.tokenizer.extract_keywords(doc)  # 명사, 동사, 형용사 추출
                tokenized_docs.append(keywords)
            
            self.documents = all_docs
            
            # BM25 인덱스 생성
            self.bm25_index = BM25Okapi(tokenized_docs)
            logger.info(f"BM25 인덱스 구축 완료: {len(all_docs)}개 문서")
            
        except Exception as e:
            logger.error(f"BM25 인덱스 구축 실패: {e}")
            self.bm25_index = None
    
    # Step 3: 문서 수집
    def _get_all_documents_from_vectorstore(self) -> List[str]:
        """
        벡터스토어에서 모든 문서를 가져옵니다.
        Step 3-1: Pinecone API 연결
        Step 3-2: 모든 벡터 쿼리
        Step 3-3: 메타데이터에서 텍스트 추출
        """
        try:
            # Step 3-1: Pinecone API 연결
            import pinecone
            import os
            
            api_key = os.getenv("PINECONE_API_KEY")
            environment = os.getenv("PINECONE_ENVIRONMENT")
            
            if not api_key or not environment:
                logger.warning("Pinecone API 키 또는 환경 설정이 없습니다.")
                return []
            
            pinecone.init(api_key=api_key, environment=environment)
            
            # 인덱스 접근
            index_name = 'swpre10'  # 벡터스토어 설정과 동일
            if index_name not in pinecone.list_indexes():
                logger.warning(f"Pinecone 인덱스 '{index_name}'를 찾을 수 없습니다.")
                return []
            
            index = pinecone.Index(index_name)
            
            # Step 3-2: 모든 벡터를 가져오기 (빈 벡터로 쿼리)
            query_response = index.query(
                vector=[0.0] * 1024,  # 1024차원 벡터 (모든 차원을 0으로)
                top_k=10000,  # 충분히 큰 수
                include_metadata=True
            )
            
            # Step 3-3: 메타데이터에서 텍스트 추출
            documents = []
            for match in query_response['matches']:
                if 'metadata' in match and 'text' in match['metadata']:
                    documents.append(match['metadata']['text'])
            
            logger.info(f"Pinecone에서 {len(documents)}개 문서를 가져왔습니다.")
            return documents
                
        except Exception as e:
            logger.error(f"벡터스토어에서 문서 가져오기 실패: {e}")
            # 실패 시 벡터스토어에서 직접 가져오기 시도
            try:
                vectorstore = get_vectorstore()
                if hasattr(vectorstore, 'similarity_search'):
                    # 빈 쿼리로 검색하여 문서 구조 확인
                    sample_docs = vectorstore.similarity_search("", k=100)
                    documents = [doc.page_content for doc in sample_docs]
                    logger.info(f"벡터스토어에서 {len(documents)}개 문서를 가져왔습니다.")
                    return documents
            except Exception as e2:
                logger.error(f"벡터스토어 직접 접근도 실패: {e2}")
            
            return []
            
    # Step 4: 하이브리드 검색 메인 로직
    def search(self, query: str, top_k: int = 5, alpha: float = 0.6) -> List[Dict[str, Any]]:
        """
        하이브리드 검색을 수행
        1. 벡터 검색 (의미적 검색)
        2. BM25 검색 (키워드 검색)
        3. 결과 결합 및 재순위화
        """
        try:
            # 벡터 검색 (밀집 표현) - 의미적 유사도
            vector_results = self._vector_search(query, top_k * 2)
            
            # BM25 검색 (희소 표현) - 키워드 매칭
            bm25_results = self._bm25_search(query, top_k * 2)
            
            # 결과 결합 및 재순위화
            combined_results = self._combine_results(
                vector_results, bm25_results, alpha, top_k
            )
            
            return combined_results
            
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            # 실패 시 벡터 검색만 사용
            return self._vector_search(query, top_k)
    
    # 벡터 검색
    def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        벡터 검색을 수행합니다 (의미적 검색).
        1. 쿼리를 벡터로 변환
        2. 코사인 유사도로 검색
        3. 결과 점수 계산
        """
        try:
            # 쿼리를 벡터로 변환하여 검색
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": top_k})
            docs = retriever.invoke(query)
            
            # 결과 포맷팅 및 점수 계산
            results = []
            for i, doc in enumerate(docs):
                results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': 1.0 - (i * 0.1),  # 순위 기반 점수 (1위: 1.0, 2위: 0.9, ...)
                    'type': 'vector'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return []
    
    # BM25 검색
    def _bm25_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        BM25 검색을 수행합니다 (키워드 검색).
        1. 쿼리 토큰화
        2. BM25 점수 계산
        3. 상위 결과 선택
        """
        try:
            if self.bm25_index is None:
                return []
            
            # 한국어 토크나이저를 사용하여 쿼리 토큰화
            query_keywords = self.tokenizer.extract_keywords(query)  # 명사, 동사, 형용사 추출
            
            if not query_keywords:
                return []
            
            # BM25 점수 계산 (키워드 빈도 기반)
            scores = self.bm25_index.get_scores(query_keywords)
            
            # 상위 결과 선택
            top_indices = np.argsort(scores)[::-1][:top_k]  # 점수 내림차순 정렬
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # 점수가 있는 결과만
                    results.append({
                        'content': self.documents[idx],
                        'metadata': {'title': self.documents[idx]},
                        'score': scores[idx],
                        'type': 'bm25'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"BM25 검색 실패: {e}")
            return []
    
    # 결과 결합 및 재순위화
    def _combine_results(self, vector_results: List[Dict], bm25_results: List[Dict], 
                        alpha: float, top_k: int) -> List[Dict[str, Any]]:
        """
        벡터 검색과 BM25 검색 결과를 결합합니다.
        1. 결과 통합 (중복 제거)
        2. 가중 평균 점수 계산
        3. 최종 순위 결정
        """
        try:
            # 결과 통합 (중복 제거)
            all_results = {}
            
            # 벡터 검색 결과 처리
            for result in vector_results:
                key = result['content'][:100]  # 내용 기반 키 (중복 제거용)
                if key not in all_results:
                    all_results[key] = {
                        'content': result['content'],
                        'metadata': result['metadata'],
                        'vector_score': result['score'],
                        'bm25_score': 0.0,
                        'combined_score': alpha * result['score']  # 벡터 점수 * 가중치
                    }
            
            # BM25 검색 결과 처리
            for result in bm25_results:
                key = result['content'][:100]  # 내용 기반 키
                if key in all_results:
                    # 기존 결과에 BM25 점수 추가
                    all_results[key]['bm25_score'] = result['score']
                    all_results[key]['combined_score'] += (1 - alpha) * result['score']  # BM25 점수 * 가중치
                else:
                    # 새로운 결과 추가
                    all_results[key] = {
                        'content': result['content'],
                        'metadata': result['metadata'],
                        'vector_score': 0.0,
                        'bm25_score': result['score'],
                        'combined_score': (1 - alpha) * result['score']
                    }
            
            # 결합 점수로 정렬
            sorted_results = sorted(
                all_results.values(),
                key=lambda x: x['combined_score'],
                reverse=True  # 높은 점수 순
            )
            
            # 최종 결과 형식 변환
            final_results = []
            for result in sorted_results[:top_k]:
                final_results.append({
                    'content': result['content'],
                    'metadata': result['metadata'],
                    'score': result['combined_score'],      # 최종 결합 점수
                    'vector_score': result['vector_score'], # 벡터 검색 점수
                    'bm25_score': result['bm25_score']      # BM25 검색 점수
                })
            
            return final_results
            
        except Exception as e:
            logger.error(f"결과 결합 실패: {e}")
            return vector_results[:top_k]  # 실패 시 벡터 검색 결과만 반환

# 전역 인스턴스 관리
_hybrid_search_engine = None

def get_hybrid_search_engine():
    """
    하이브리드 검색 엔진 인스턴스를 반환 (싱글톤 패턴).
    """
    global _hybrid_search_engine
    if _hybrid_search_engine is None:
        _hybrid_search_engine = HybridSearchEngine()
    return _hybrid_search_engine 