from typing import Dict, Any, Optional
from .search_manager import SearchManager


class RAGManager(SearchManager):
    """RAG 및 LLM 통합을 위한 관리 클래스"""
    
    def get_context_for_rag(self, 
                           query: str, 
                           max_context_length: int = 4000,
                           n_results: int = 5,
                           include_metadata: bool = True,
                           separator: str = "\n\n---\n\n") -> Dict[str, Any]:
        """RAG를 위한 컨텍스트 구성"""
        if not query.strip():
            return {"error": "쿼리가 비어있습니다", "status": "error"}
        
        try:
            # 유사도 검색
            search_results = self.similarity_search(query, n_results)
            
            if search_results.get("status") == "error":
                return search_results
            
            # 컨텍스트 구성
            context_parts = []
            current_length = 0
            used_docs = []
            separator_length = len(separator)
            
            for result in search_results["results"]:
                doc_text = result["document"]
                
                # 메타데이터 포함 형식 결정
                if include_metadata and result.get("metadata"):
                    source = result["metadata"].get("source_file", "unknown")
                    chunk_idx = result["metadata"].get("chunk_index", "unknown")
                    context_part = f"[출처: {source}, 청크: {chunk_idx}]\n{doc_text}"
                else:
                    context_part = doc_text
                
                # 길이 계산 (구분자 포함)
                part_length = len(context_part)
                total_addition = part_length + (separator_length if context_parts else 0)
                
                # 길이 제한 확인
                if current_length + total_addition <= max_context_length:
                    context_parts.append(context_part)
                    current_length += total_addition
                    used_docs.append({
                        "id": result["id"],
                        "similarity": result.get("similarity", 0),
                        "length": part_length,
                        "metadata": result.get("metadata", {})
                    })
                else:
                    # 남은 공간이 있으면 부분적으로라도 포함
                    remaining_space = max_context_length - current_length - (separator_length if context_parts else 0)
                    if remaining_space > 100:  # 최소 100자 이상일 때만
                        truncated_part = context_part[:remaining_space-3] + "..."
                        context_parts.append(truncated_part)
                        used_docs.append({
                            "id": result["id"],
                            "similarity": result.get("similarity", 0),
                            "length": len(truncated_part),
                            "metadata": result.get("metadata", {}),
                            "truncated": True
                        })
                    break
            
            # 최종 컨텍스트 생성
            final_context = separator.join(context_parts)
            
            return {
                "query": query,
                "context": final_context,
                "context_length": len(final_context),
                "used_documents": len(used_docs),
                "document_info": used_docs,
                "total_available": len(search_results["results"]),
                "max_context_length": max_context_length,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"RAG 컨텍스트 구성 실패: {e}")
            return {"error": f"RAG 컨텍스트 구성 실패: {e}", "status": "error"}
    
    def prepare_for_llm(self, 
                       query: str, 
                       context_type: str = "rag",
                       max_tokens: int = 4000,
                       n_results: int = 5) -> Dict[str, Any]:
        """LLM 사용을 위한 데이터 준비
        
        Args:
            query: 쿼리 텍스트
            context_type: 컨텍스트 타입 ("rag", "summarization", "qa")
            max_tokens: 최대 토큰 수
            n_results: 검색 결과 수
        """
        if not query.strip():
            return {"error": "쿼리가 비어있습니다", "status": "error"}
        
        try:
            if context_type == "rag":
                # RAG용 컨텍스트
                return self.get_context_for_rag(query, max_tokens, n_results)
            
            elif context_type == "summarization":
                # 요약용 문서들
                search_results = self.similarity_search(query, n_results=min(n_results * 2, 20))
                if search_results.get("status") == "error":
                    return search_results
                
                documents = [result["document"] for result in search_results["results"]]
                combined_text = "\n\n".join(documents)
                
                # 토큰 제한 적용 (대략적으로 문자 수로 추정)
                if len(combined_text) > max_tokens:
                    combined_text = combined_text[:max_tokens-100] + "\n...(내용 생략)"
                
                return {
                    "query": query,
                    "documents": documents,
                    "combined_text": combined_text,
                    "document_count": len(documents),
                    "context_length": len(combined_text),
                    "context_type": context_type,
                    "status": "success"
                }
            
            elif context_type == "qa":
                # Q&A용 관련 문서들
                search_results = self.similarity_search(query, n_results=n_results)
                if search_results.get("status") == "error":
                    return search_results
                
                # 결과에 추가 메타데이터 포함
                for result in search_results["results"]:
                    result["relevance_score"] = result.get("similarity", 0)
                
                search_results["context_type"] = context_type
                return search_results
            
            else:
                return {
                    "error": f"지원하지 않는 컨텍스트 타입: {context_type}. 사용 가능한 타입: rag, summarization, qa",
                    "status": "error"
                }
                
        except Exception as e:
            self.logger.error(f"LLM 데이터 준비 실패: {e}")
            return {"error": f"LLM 데이터 준비 실패: {e}", "status": "error"}
    
    def get_contextual_chunks(self, 
                             query: str,
                             chunk_window: int = 1,
                             n_results: int = 5) -> Dict[str, Any]:
        """컨텍스트를 고려한 청크 검색 (앞뒤 청크 포함)"""
        if not query.strip():
            return {"error": "쿼리가 비어있습니다", "status": "error"}
        
        try:
            # 기본 검색 수행
            search_results = self.similarity_search(query, n_results)
            
            if search_results.get("status") == "error":
                return search_results
            
            # 각 결과에 대해 앞뒤 청크 찾기
            contextual_results = []
            
            for result in search_results["results"]:
                metadata = result.get("metadata", {})
                source_file = metadata.get("source_file")
                chunk_index = metadata.get("chunk_index")
                
                if source_file and chunk_index is not None:
                    # 앞뒤 청크 검색
                    related_chunks = self._get_surrounding_chunks(
                        source_file, chunk_index, chunk_window
                    )
                    
                    contextual_results.append({
                        "main_chunk": result,
                        "surrounding_chunks": related_chunks,
                        "total_context_length": sum(len(chunk.get("document", "")) for chunk in related_chunks)
                    })
                else:
                    # 메타데이터가 없는 경우 원본만 포함
                    contextual_results.append({
                        "main_chunk": result,
                        "surrounding_chunks": [result],
                        "total_context_length": len(result.get("document", ""))
                    })
            
            return {
                "query": query,
                "chunk_window": chunk_window,
                "total_results": len(contextual_results),
                "results": contextual_results,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"컨텍스트 청크 검색 실패: {e}")
            return {"error": f"컨텍스트 청크 검색 실패: {e}", "status": "error"}
    
    def _get_surrounding_chunks(self, 
                               source_file: str, 
                               center_index: int, 
                               window: int) -> list:
        """특정 청크 주변의 청크들 가져오기"""
        try:
            # 범위 계산
            start_index = max(0, center_index - window)
            end_index = center_index + window
            
            # 해당 범위의 청크들 검색
            surrounding_chunks = []
            for i in range(start_index, end_index + 1):
                chunk_result = self.collection.get(
                    where={
                        "source_file": source_file,
                        "chunk_index": i
                    },
                    include=["documents", "metadatas"]
                )
                
                if chunk_result['ids']:
                    surrounding_chunks.append({
                        "id": chunk_result['ids'][0],
                        "document": chunk_result['documents'][0] if chunk_result['documents'] else "",
                        "metadata": chunk_result['metadatas'][0] if chunk_result['metadatas'] else {},
                        "chunk_index": i,
                        "is_center": i == center_index
                    })
             
            return surrounding_chunks
            
        except Exception as e:
            self.logger.error(f"주변 청크 검색 실패: {e}")
            return []