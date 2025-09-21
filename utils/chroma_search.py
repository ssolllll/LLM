from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .chroma_base import BaseChromeDBManager


@dataclass
class SearchResult:
    """검색 결과 데이터 클래스"""
    id: str
    document: str
    metadata: Dict[str, Any]
    distance: Optional[float] = None
    similarity: Optional[float] = None
    embedding: Optional[List[float]] = None

    @classmethod
    def from_chromadb_result(cls, idx: int, results: Dict[str, Any], 
                           include_embeddings: bool = False) -> 'SearchResult':
        """ChromaDB 결과를 SearchResult로 변환"""
        distance = results.get('distances', [None])[0][idx] if results.get('distances') else None
        similarity = (1 - distance) if distance is not None else None
        
        return cls(
            id=results['ids'][0][idx],
            document=results['documents'][0][idx],
            metadata=results.get('metadatas', [{}])[0][idx] or {},
            distance=round(distance, 4) if distance is not None else None,
            similarity=round(similarity, 4) if similarity is not None else None,
            embedding=results.get('embeddings', [None])[0][idx] if include_embeddings else None
        )


@dataclass
class SearchResponse:
    """검색 응답 데이터 클래스"""
    query: str
    total_results: int
    results: List[SearchResult]
    status: str = "success"
    error: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class SearchManager(BaseChromeDBManager):
    """검색 기능 전담 관리 클래스"""
    
    MIN_SIMILARITY = 0.0
    MAX_SIMILARITY = 1.0
    
    def _validate_query(self, query_text: str) -> Optional[str]:
        """쿼리 유효성 검사"""
        if not query_text or not query_text.strip():
            return "검색어가 비어있습니다"
        return None
    
    def _validate_similarity_threshold(self, threshold: float) -> Optional[str]:
        """유사도 임계값 유효성 검사"""
        if threshold < self.MIN_SIMILARITY or threshold > self.MAX_SIMILARITY:
            return f"유사도 임계값은 {self.MIN_SIMILARITY}~{self.MAX_SIMILARITY} 사이여야 합니다"
        return None
    
    def _get_safe_result_count(self, requested: int) -> int:
        """안전한 결과 수 반환"""
        collection_count = self.collection.count()
        return min(requested, collection_count) if collection_count > 0 else 0
    
    def _execute_search(self, query_texts: List[str], n_results: int, 
                       where: Optional[Dict[str, Any]] = None,
                       where_document: Optional[Dict[str, str]] = None,
                       include_embeddings: bool = False) -> Dict[str, Any]:
        """실제 검색 실행"""
        include_params = ["documents", "metadatas", "distances"]
        if include_embeddings:
            include_params.append("embeddings")
            
        return self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include_params
        )
    
    def _format_single_search_results(self, results: Dict[str, Any], 
                                    query_idx: int = 0, 
                                    include_embeddings: bool = False) -> List[SearchResult]:
        """단일 검색 결과 포매팅"""
        formatted_results = []
        if not results.get('ids') or query_idx >= len(results['ids']):
            return formatted_results
            
        for i in range(len(results['ids'][query_idx])):
            result = SearchResult.from_chromadb_result(i, {
                'ids': [results['ids'][query_idx]],
                'documents': [results['documents'][query_idx]],
                'metadatas': [results.get('metadatas', [None])[query_idx]],
                'distances': [results.get('distances', [None])[query_idx]],
                'embeddings': [results.get('embeddings', [None])[query_idx]] if include_embeddings else None
            }, include_embeddings)
            formatted_results.append(result)
            
        return formatted_results
    
    def similarity_search(self, 
                         query_text: str, 
                         n_results: int = 5,
                         where: Optional[Dict[str, Any]] = None,
                         where_document: Optional[Dict[str, str]] = None,
                         include_embeddings: bool = False) -> SearchResponse:
        """유사도 기반 검색"""
        # 입력 유효성 검사
        error = self._validate_query(query_text)
        if error:
            return SearchResponse(query=query_text, total_results=0, results=[], 
                               status="error", error=error)
        
        try:
            safe_n_results = self._get_safe_result_count(n_results)
            if safe_n_results == 0:
                return SearchResponse(query=query_text, total_results=0, results=[], 
                                   status="empty")
            
            # 검색 실행
            results = self._execute_search(
                [query_text], safe_n_results, where, where_document, include_embeddings
            )
            
            # 결과 포매팅
            formatted_results = self._format_single_search_results(results, 0, include_embeddings)
            
            return SearchResponse(
                query=query_text,
                total_results=len(formatted_results),
                results=formatted_results,
                filters={"where": where, "where_document": where_document}
            )
            
        except Exception as e:
            self.logger.error(f"검색 실패: {e}")
            return SearchResponse(query=query_text, total_results=0, results=[], 
                               status="error", error=f"검색 실패: {e}")
    
    def batch_similarity_search(self, 
                               query_texts: List[str], 
                               n_results: int = 5) -> Dict[str, Any]:
        """여러 쿼리 동시 검색"""
        # 유효한 쿼리만 추출
        valid_queries = [q.strip() for q in query_texts if q and q.strip()]
        
        if not valid_queries:
            return {
                "error": "유효한 검색어가 없습니다", 
                "status": "error",
                "queries": [],
                "total_queries": 0,
                "results": {}
            }
        
        try:
            safe_n_results = self._get_safe_result_count(n_results)
            results = self._execute_search(valid_queries, safe_n_results)
            
            # 쿼리별 결과 정리
            batch_results = {}
            for query_idx, query_text in enumerate(valid_queries):
                query_results = self._format_single_search_results(results, query_idx)
                batch_results[query_text] = [result.__dict__ for result in query_results]
            
            return {
                "queries": valid_queries,
                "total_queries": len(valid_queries),
                "results": batch_results,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"배치 검색 실패: {e}")
            return {
                "error": f"배치 검색 실패: {e}", 
                "status": "error",
                "queries": valid_queries,
                "total_queries": len(valid_queries),
                "results": {}
            }
    
    def hybrid_search(self, 
                     query_text: str,
                     metadata_filter: Optional[Dict[str, Any]] = None,
                     n_results: int = 5,
                     min_similarity_threshold: float = 0.0) -> Dict[str, Any]:
        """하이브리드 검색 (유사도 + 메타데이터 필터)"""
        # 입력 유효성 검사
        query_error = self._validate_query(query_text)
        if query_error:
            return {"error": query_error, "status": "error"}
        
        threshold_error = self._validate_similarity_threshold(min_similarity_threshold)
        if threshold_error:
            return {"error": threshold_error, "status": "error"}
        
        try:
            # 여유분을 두고 검색 (임계값 필터링을 위해)
            search_limit = self._get_safe_result_count(n_results * 3)
            if search_limit == 0:
                return {
                    "query": query_text,
                    "metadata_filter": metadata_filter,
                    "min_similarity_threshold": min_similarity_threshold,
                    "total_candidates": 0,
                    "filtered_results": 0,
                    "results": [],
                    "status": "empty"
                }
            
            results = self._execute_search([query_text], search_limit, metadata_filter)
            
            # 유사도 임계값 적용 및 필터링
            filtered_results = []
            for result in self._format_single_search_results(results, 0):
                if result.similarity is not None and result.similarity >= min_similarity_threshold:
                    filtered_results.append({
                        "id": result.id,
                        "document": result.document,
                        "metadata": result.metadata,
                        "similarity": result.similarity,
                        "distance": result.distance
                    })
            
            # 유사도 순으로 정렬 후 상위 n_results 반환
            filtered_results.sort(key=lambda x: x['similarity'], reverse=True)
            final_results = filtered_results[:n_results]
            
            return {
                "query": query_text,
                "metadata_filter": metadata_filter,
                "min_similarity_threshold": min_similarity_threshold,
                "total_candidates": len(results['ids'][0]) if results.get('ids') else 0,
                "filtered_results": len(final_results),
                "results": final_results,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"하이브리드 검색 실패: {e}")
            return {"error": f"하이브리드 검색 실패: {e}", "status": "error"}
    
    def get_search_stats(self) -> Dict[str, Any]:
        """검색 통계 정보 반환"""
        try:
            collection_count = self.collection.count()
            return {
                "total_documents": collection_count,
                "collection_name": self.collection.name,
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"검색 통계 조회 실패: {e}")
            return {"error": f"검색 통계 조회 실패: {e}", "status": "error"}
