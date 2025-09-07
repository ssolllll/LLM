from typing import List, Dict, Any, Optional
from .base_manager import BaseChromeDBManager


class FilterManager(BaseChromeDBManager):
    """메타데이터 필터링 전담 관리 클래스"""
    
    def filter_by_metadata(self, 
                          where: Dict[str, Any], 
                          limit: Optional[int] = None) -> Dict[str, Any]:
        """메타데이터 조건으로 필터링"""
        if not where:
            return {"error": "필터 조건이 비어있습니다", "status": "error"}
        
        try:
            # limit이 없으면 전체 조회하되 안전한 제한 설정
            if limit is None:
                limit = min(self.collection.count(), 10000)  # 최대 10000개로 제한
            
            results = self.collection.get(
                where=where,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            formatted_results = []
            for i in range(len(results['ids'])):
                formatted_results.append({
                    "id": results['ids'][i],
                    "document": results['documents'][i] if results['documents'] else "",
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                })
            
            return {
                "filter_condition": where,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"필터링 실패: {e}")
            return {"error": f"필터링 실패: {e}", "status": "error"}
    
    def get_by_source_file(self, source_file: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """특정 소스 파일의 모든 청크 조회"""
        if not source_file.strip():
            return {"error": "소스 파일명이 비어있습니다", "status": "error"}
        
        return self.filter_by_metadata(
            where={"source_file": source_file},
            limit=limit
        )
    
    def get_by_chunk_strategy(self, strategy: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """특정 청킹 전략으로 생성된 문서들 조회"""
        if not strategy.strip():
            return {"error": "청킹 전략명이 비어있습니다", "status": "error"}
        
        return self.filter_by_metadata(
            where={"chunk_strategy": strategy},
            limit=limit
        )
    
    def get_by_date_range(self, 
                         start_date: Optional[str] = None, 
                         end_date: Optional[str] = None,
                         date_field: str = "created_at",
                         limit: Optional[int] = None) -> Dict[str, Any]:
        """날짜 범위로 문서 필터링"""
        where_conditions = {}
        
        if start_date:
            where_conditions[f"{date_field}"] = {"$gte": start_date}
        
        if end_date:
            if date_field in where_conditions:
                where_conditions[date_field]["$lte"] = end_date
            else:
                where_conditions[date_field] = {"$lte": end_date}
        
        if not where_conditions:
            return {"error": "시작일 또는 종료일 중 하나는 필수입니다", "status": "error"}
        
        return self.filter_by_metadata(where_conditions, limit)
    
    def get_by_metadata_value(self, 
                             field: str, 
                             value: Any, 
                             operator: str = "eq",
                             limit: Optional[int] = None) -> Dict[str, Any]:
        """특정 메타데이터 필드 값으로 필터링
        
        Args:
            field: 메타데이터 필드명
            value: 검색할 값
            operator: 연산자 (eq, ne, gt, gte, lt, lte, in, nin)
            limit: 결과 제한 수
        """
        if not field.strip():
            return {"error": "필드명이 비어있습니다", "status": "error"}
        
        # 연산자에 따른 where 조건 구성
        operator_mapping = {
            "eq": value,
            "ne": {"$ne": value},
            "gt": {"$gt": value},
            "gte": {"$gte": value},
            "lt": {"$lt": value},
            "lte": {"$lte": value},
            "in": {"$in": value if isinstance(value, list) else [value]},
            "nin": {"$nin": value if isinstance(value, list) else [value]}
        }
        
        if operator not in operator_mapping:
            return {
                "error": f"지원하지 않는 연산자: {operator}. 사용 가능: {list(operator_mapping.keys())}",
                "status": "error"
            }
        
        where_condition = {field: operator_mapping[operator]}
        
        return self.filter_by_metadata(where_condition, limit)
    
    def get_documents_with_metadata_keys(self, 
                                        required_keys: List[str],
                                        limit: Optional[int] = None) -> Dict[str, Any]:
        """특정 메타데이터 키들을 가진 문서들 조회"""
        if not required_keys:
            return {"error": "필수 키 목록이 비어있습니다", "status": "error"}
        
        try:
            # 모든 문서 조회 후 필터링 (ChromaDB에서 키 존재 여부 쿼리는 제한적)
            all_results = self.collection.get(
                limit=limit or 10000,
                include=["documents", "metadatas"]
            )
            
            filtered_results = []
            for i in range(len(all_results['ids'])):
                metadata = all_results['metadatas'][i] if all_results['metadatas'] else {}
                
                # 모든 필수 키가 있는지 확인
                if metadata and all(key in metadata for key in required_keys):
                    filtered_results.append({
                        "id": all_results['ids'][i],
                        "document": all_results['documents'][i] if all_results['documents'] else "",
                        "metadata": metadata
                    })
            
            return {
                "required_keys": required_keys,
                "total_results": len(filtered_results),
                "results": filtered_results[:limit] if limit else filtered_results,
                "status": "success"
            }
            
        except Exception as e: 
            self.logger.error(f"메타데이터 키 필터링 실패: {e}")
            return {"error": f"메타데이터 키 필터링 실패: {e}", "status": "error"}