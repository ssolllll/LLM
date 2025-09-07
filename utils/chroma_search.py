from typing import List, Dict, Any, Optional
from .base_manager import BaseChromeDBManager


class SearchManager(BaseChromeDBManager):
    """검색 기능 전담 관리 클래스"""
    
    def similarity_search(self, 
                         query_text: str, 
                         n_results: int = 5,
                         where: Optional[Dict[str, Any]] = None,
                         where_document: Optional[Dict[str, str]] = None,
                         include_embeddings: bool = False) -> Dict[str, Any]:
        """유사도 기반 검색
        
        Args:
            query_text: 검색할 텍스트
            n_results: 반환할 결과 수
            where: 메타데이터 필터 조건
            where_document: 문서 내용 필터 조건
            include_embeddings: 임베딩 포함 여부
        """
        if not query_text.strip():
            return {"error": "검색어가 비어있습니다", "status": "error"}
        
        try:
            # 실제 문서 수보다 많이 요청하지 않도록 제한
            actual_n_results = min(n_results, self.collection.count())
            if actual_n_results == 0:
                return {"query": query_text, "total_results": 0, "results": [], "status": "empty"}
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=actual_n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"] + (["embeddings"] if include_embeddings else [])
            )
            
            # 결과 정리
            formatted_results = []
            for i in range(len(results['ids'][0])):
                result_item = {
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None,
                    "similarity": 1 - results['distances'][0][i] if results['distances'] else None
                }
                
                if include_embeddings and results.get('embeddings'):
                    result_item["embedding"] = results['embeddings'][0][i]
                
                formatted_results.append(result_item)
            
            return {
                "query": query_text,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "filters": {
                    "where": where,
                    "where_document": where_document
                },
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"검색 실패: {e}")
            return {"error": f"검색 실패: {e}", "status": "error"}
    
    def batch_similarity_search(self, 
                               query_texts: List[str], 
                               n_results: int = 5) -> Dict[str, Any]:
        """여러 쿼리 동시 검색"""
        if not query_texts or not any(q.strip() for q in query_texts):
            return {"error": "유효한 검색어가 없습니다", "status": "error"}
        
        try:
            # 빈 쿼리 제거
            valid_queries = [q for q in query_texts if q.strip()]
            
            results = self.collection.query(
                query_texts=valid_queries,
                n_results=min(n_results, self.collection.count())
            )
            
            # 쿼리별 결과 정리
            batch_results = {}
            for query_idx, query_text in enumerate(valid_queries):
                query_results = []
                if query_idx < len(results['ids']):
                    for i in range(len(results['ids'][query_idx])):
                        query_results.append({
                            "id": results['ids'][query_idx][i],
                            "document": results['documents'][query_idx][i],
                            "metadata": results['metadatas'][query_idx][i] if results['metadatas'] else {},
                            "distance": results['distances'][query_idx][i] if results['distances'] else None,
                            "similarity": 1 - results['distances'][query_idx][i] if results['distances'] else None
                        })
                
                batch_results[query_text] = query_results
            
            return {
                "queries": valid_queries,
                "total_queries": len(valid_queries),
                "results": batch_results,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"배치 검색 실패: {e}")
            return {"error": f"배치 검색 실패: {e}", "status": "error"}
    
    def hybrid_search(self, 
                     query_text: str,
                     metadata_filter: Optional[Dict[str, Any]] = None,
                     n_results: int = 5,
                     min_similarity_threshold: float = 0.0) -> Dict[str, Any]:
        """하이브리드 검색 (유사도 + 메타데이터 필터)"""
        if not query_text.strip():
            return {"error": "검색어가 비어있습니다", "status": "error"}
        
        if min_similarity_threshold < 0 or min_similarity_threshold > 1:
            return {"error": "유사도 임계값은 0~1 사이여야 합니다", "status": "error"}
        
        try:
            # 여유분을 두고 검색
            search_limit = min(n_results * 3, self.collection.count())
            results = self.collection.query(
                query_texts=[query_text],
                n_results=search_limit,
                where=metadata_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # 유사도 임계값 적용
            filtered_results = []
            for i in range(len(results['ids'][0])):
                distance = results['distances'][0][i] if results['distances'] else 0
                similarity = max(0, 1 - distance)  # 음수 방지
                
                if similarity >= min_similarity_threshold:
                    filtered_results.append({
                        "id": results['ids'][0][i],
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "similarity": round(similarity, 4),
                        "distance": round(distance, 4)
                    })
            
            # 유사도 순으로 정렬 후 상위 n_results 반환
            filtered_results.sort(key=lambda x: x['similarity'], reverse=True)
            final_results = filtered_results[:n_results]
            
            return {
                "query": query_text,
                "metadata_filter": metadata_filter,
                "min_similarity_threshold": min_similarity_threshold,
                "total_candidates": len(results['ids'][0]),
                "filtered_results": len(final_results),
                "results": final_results,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"하이브리드 검색 실패: {e}")
            return {"error": f"하이브리드 검색 실패: {e}", "status": "error"} 