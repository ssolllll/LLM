from typing import List, Dict, Any
from .base_manager import BaseChromeDBManager


class DocumentManager(BaseChromeDBManager):
    """문서 관리 전담 클래스"""
    
    def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """ID로 특정 문서 조회"""
        if not doc_id.strip():
            return {"error": f"메타데이터 업데이트 실패: {e}", "status": "error"}
    
    def get_documents_by_content_search(self, 
                                       search_text: str, 
                                       case_sensitive: bool = False,
                                       limit: int = 100) -> Dict[str, Any]:
        """문서 내용에서 텍스트 검색 (단순 문자열 매칭)"""
        if not search_text.strip():
            return {"error": "검색 텍스트가 비어있습니다", "status": "error"}
        
        try:
            # 모든 문서 조회 후 필터링
            all_results = self.collection.get(
                limit=min(limit * 5, 10000),  # 여유분을 두고 조회
                include=["documents", "metadatas"]
            )
            
            matching_docs = []
            search_target = search_text if case_sensitive else search_text.lower()
            
            for i in range(len(all_results['ids'])):
                doc_content = all_results['documents'][i] if all_results['documents'] else ""
                content_target = doc_content if case_sensitive else doc_content.lower()
                
                if search_target in content_target:
                    matching_docs.append({
                        "id": all_results['ids'][i],
                        "document": doc_content,
                        "metadata": all_results['metadatas'][i] if all_results['metadatas'] else {},
                        "match_positions": self._find_match_positions(content_target, search_target)
                    })
                    
                    if len(matching_docs) >= limit:
                        break
            
            return {
                "search_text": search_text,
                "case_sensitive": case_sensitive,
                "total_matches": len(matching_docs),
                "results": matching_docs,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"내용 검색 실패: {e}")
            return {"error": f"내용 검색 실패: {e}", "status": "error"}
    
    def _find_match_positions(self, text: str, search_term: str) -> List[int]:
        """텍스트에서 검색어 위치 찾기"""
        positions = []
        start = 0
        while True:
            pos = text.find(search_term, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        return {"positionserror": "문서 ID가 비어있습니다", "status": "error"}
        
        try:
            results = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            
            if not results['ids']:
                return {
                    "error": f"ID '{doc_id}'를 찾을 수 없습니다", 
                    "status": "not_found"
                }
            
            return {
                "id": results['ids'][0],
                "document": results['documents'][0] if results['documents'] else "",
                "metadata": results['metadatas'][0] if results['metadatas'] else {},
                "document_length": len(results['documents'][0]) if results['documents'] else 0,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"문서 조회 실패: {e}")
            return {"error": f"문서 조회 실패: {e}", "status": "error"}
    
    def get_multiple_documents_by_ids(self, doc_ids: List[str]) -> Dict[str, Any]:
        """여러 ID로 문서들 조회"""
        if not doc_ids:
            return {"error": "문서 ID 목록이 비어있습니다", "status": "error"}
        
        try:
            results = self.collection.get(
                ids=doc_ids,
                include=["documents", "metadatas"]
            )
            
            documents = []
            found_ids = set(results['ids'])
            
            for i, doc_id in enumerate(doc_ids):
                if doc_id in found_ids:
                    idx = results['ids'].index(doc_id)
                    documents.append({
                        "id": doc_id,
                        "document": results['documents'][idx] if results['documents'] else "",
                        "metadata": results['metadatas'][idx] if results['metadatas'] else {},
                        "found": True
                    })
                else:
                    documents.append({
                        "id": doc_id,
                        "document": "",
                        "metadata": {},
                        "found": False
                    })
            
            return {
                "requested_count": len(doc_ids),
                "found_count": len(results['ids']),
                "documents": documents,
                "status": "success"
            }
             
        except Exception as e:
            self.logger.error(f"다중 문서 조회 실패: {e}")
            return {"error": f"다중 문서 조회 실패: {e}", "status": "error"}
    
    def delete_documents(self, doc_ids: List[str]) -> Dict[str, Any]:
        """특정 문서들 삭제"""
        if not doc_ids:
            return {"error": "삭제할 문서 ID가 없습니다", "status": "error"}
        
        try:
            # 먼저 존재하는 문서들 확인
            existing_docs = self.collection.get(ids=doc_ids)
            existing_ids = set(existing_docs['ids'])
            
            if existing_ids:
                self.collection.delete(ids=list(existing_ids))
            
            return {
                "requested_deletions": len(doc_ids),
                "actual_deletions": len(existing_ids),
                "deleted_ids": list(existing_ids),
                "not_found_ids": [doc_id for doc_id in doc_ids if doc_id not in existing_ids],
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"문서 삭제 실패: {e}")
            return {"error": f"문서 삭제 실패: {e}", "status": "error"}
    
    def delete_by_metadata(self, where: Dict[str, Any]) -> Dict[str, Any]:
        """메타데이터 조건으로 문서 삭제"""
        if not where:
            return {"error": "삭제 조건이 비어있습니다", "status": "error"}
        
        try:
            # 먼저 삭제할 문서들 조회
            to_delete = self.collection.get(where=where)
            delete_count = len(to_delete['ids'])
            
            # 삭제 실행
            if delete_count > 0:
                self.collection.delete(where=where)
            
            return {
                "deleted_count": delete_count,
                "deleted_ids": to_delete['ids'],
                "filter_condition": where,
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"조건부 삭제 실패: {e}")
            return {"error": f"조건부 삭제 실패: {e}", "status": "error"}
    
    def update_document_metadata(self, 
                               doc_id: str, 
                               new_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """문서의 메타데이터 업데이트"""
        if not doc_id.strip():
            return {"error": "문서 ID가 비어있습니다", "status": "error"}
        
        if not new_metadata:
            return {"error": "새 메타데이터가 비어있습니다", "status": "error"}
        
        try:
            # 문서 존재 여부 확인
            existing = self.collection.get(ids=[doc_id])
            if not existing['ids']:
                return {"error": f"ID '{doc_id}'를 찾을 수 없습니다", "status": "not_found"}
            
            # ChromaDB에서는 직접 메타데이터 업데이트가 어려우므로
            # 문서를 다시 추가하는 방식으로 처리해야 할 수 있습니다.
            # 이는 ChromaDB의 제약사항입니다.
            
            return {
                "error": "ChromaDB는 직접적인 메타데이터 업데이트를 지원하지 않습니다. 문서를 삭제 후 재추가해야 합니다.",
                "status": "not_supported",
                "suggestion": "delete_documents()와 collection.add()를 순차적으로 사용하세요."
            }
            
        except Exception as e:
            self.logger.error(f"메타데이터 업데이트 실패: {e}")
            return {""}