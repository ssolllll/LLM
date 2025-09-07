from datetime import datetime
from typing import Dict, Any
from .base_manager import BaseChromeDBManager
from .search_manager import SearchManager
from .filter_manager import FilterManager
from .document_manager import DocumentManager
from .rag_manager import RAGManager
from .analytics_manager import AnalyticsManager


class ChromaDBQueryManager(
    SearchManager,
    FilterManager,
    DocumentManager, 
    RAGManager,
    AnalyticsManager
):
    """ChromaDB 쿼리 및 검색을 위한 통합 관리 클래스
    
    모든 기능을 포함한 메인 클래스입니다.
    각 기능별 클래스를 상속받아 완전한 기능을 제공합니다.
    """
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "documents"):
        """ChromaDB 쿼리 매니저 초기화
        
        Args:
            db_path: ChromaDB 데이터베이스 경로
            collection_name: 사용할 컬렉션 이름
        """
        # 기본 클래스 초기화
        super().__init__(db_path, collection_name)
        
        self.logger.info(f"ChromaDBQueryManager 초기화 완료")
        self.logger.info(f"사용 가능한 기능: 검색, 필터링, 문서관리, RAG, 분석")
    
    def get_manager_info(self) -> Dict[str, Any]:
        """매니저 정보 및 사용 가능한 기능 목록"""
        return {
            "manager_type": "ChromaDBQueryManager",
            "version": "1.0.0",
            "available_features": {
                "search": [
                    "similarity_search", 
                    "batch_similarity_search", 
                    "hybrid_search"
                ],
                "filter": [
                    "filter_by_metadata",
                    "get_by_source_file",
                    "get_by_chunk_strategy", 
                    "get_by_date_range",
                    "get_by_metadata_value",
                    "get_documents_with_metadata_keys"
                ],
                "document_management": [
                    "get_document_by_id",
                    "get_multiple_documents_by_ids",
                    "delete_documents",
                    "delete_by_metadata",
                    "update_document_metadata",
                    "get_documents_by_content_search"
                ],
                "rag": [
                    "get_context_for_rag",
                    "prepare_for_llm",
                    "get_contextual_chunks"
                ],
                "analytics": [
                    "get_statistics",
                    "get_source_file_statistics",
                    "get_chunk_strategy_analysis",
                    "export_to_dataframe",
                    "get_similarity_distribution_analysis"
                ],
                "utilities": [
                    "health_check",
                    "validate_query_parameters",
                    "create_backup_info"
                ]
            },
            "collection_info": self.get_collection_info(),
            "status": "ready"
        }
    
    def create_backup_info(self) -> Dict[str, Any]:
        """백업을 위한 정보 생성"""
        try:
            info = self.get_collection_info()
            stats = self.get_statistics()
            
            return {
                "backup_timestamp": datetime.now().isoformat(),
                "collection_info": info,
                "statistics": stats,
                "db_path": self.db_path,
                "collection_name": self.collection_name,
                "manager_version": "1.0.0"
            }
        except Exception as e:
            return {"error": f"백업 정보 생성 실패: {e}"}


# ================== 사용 예시 ==================

def main():
    """사용 예시"""
    try:
        # ChromaDB 쿼리 매니저 초기화 (context manager 사용)
        with ChromaDBQueryManager(
            db_path="./chroma_db",
            collection_name="testCollection"
        ) as query_manager:
            
            print("=== 시스템 상태 확인 ===")
            health = query_manager.health_check()
            print(f"상태: {health.get('status')}")
            if health.get('status') == 'unhealthy':
                print(f"오류: {health.get('error')}")
                return
            
            # 1. 매니저 정보 확인
            manager_info = query_manager.get_manager_info()
            print(f"\n=== 매니저 정보 ===")
            print(f"버전: {manager_info.get('version')}")
            print(f"사용 가능한 기능 수: {len(manager_info.get('available_features', {}))}")
            
            # 2. 컬렉션 정보 확인
            info = query_manager.get_collection_info()
            print(f"\n=== 컬렉션 정보 ===")
            print(f"총 문서 수: {info.get('total_documents', 0)}")
            print(f"메타데이터 키: {info.get('sample_metadata_keys', [])}")
            
            if info.get('total_documents', 0) == 0:
                print("컬렉션이 비어있습니다.")
                return
            
            # 3. 샘플 문서 확인
            samples = query_manager.get_sample_documents(limit=2)
            print(f"\n=== 샘플 문서 ({samples.get('sample_count', 0)}개) ===")
            for i, doc in enumerate(samples.get('documents', []), 1):
                print(f"{i}. ID: {doc.get('id')}")
                print(f"   길이: {doc.get('full_length')} 문자")
                print(f"   내용: {doc.get('text', '')[:100]}...")
                if doc.get('metadata'):
                    print(f"   메타데이터: {doc.get('metadata')}")
            
            # 4. 유사도 검색 테스트
            test_queries = ["인공지능", "machine learning", "데이터 분석", "python"]
            for query in test_queries:
                search_results = query_manager.similarity_search(query, n_results=2)
                if search_results.get("status") == "success" and search_results.get("results"):
                    print(f"\n=== '{query}' 검색 결과 ===")
                    for i, result in enumerate(search_results["results"][:1], 1):
                        print(f"{i}. 유사도: {result.get('similarity', 0):.3f}")
                        print(f"   내용: {result['document'][:150]}...")
                    break
            
            # 5. 통계 정보
            stats = query_manager.get_statistics()
            print(f"\n=== 통계 정보 ===")
            if stats.get("status") == "success":
                print(f"총 문서: {stats.get('total_documents', 0)}")
                doc_stats = stats.get('document_statistics', {})
                if doc_stats:
                    print(f"평균 길이: {doc_stats.get('average_length', 0):.0f} 문자")
                    print(f"길이 범위: {doc_stats.get('min_length', 0)} ~ {doc_stats.get('max_length', 0)} 문자")
                
                meta_stats = stats.get('metadata_statistics', {})
                if meta_stats:
                    print(f"메타데이터 키 수: {len(meta_stats)}")
                    for key, stat in list(meta_stats.items())[:3]:
                        print(f"  {key}: {stat.get('unique_count', 0)}개 고유값")
            
            # 6. RAG 컨텍스트 구성 테스트
            if info.get('total_documents', 0) > 0:
                rag_context = query_manager.get_context_for_rag(
                    "데이터 처리 방법", 
                    max_context_length=1000
                )
                if rag_context.get("status") == "success":
                    print(f"\n=== RAG 컨텍스트 ===")
                    print(f"컨텍스트 길이: {rag_context.get('context_length', 0)} 문자")
                    print(f"사용된 문서: {rag_context.get('used_documents', 0)}개")
                    print(f"컨텍스트 미리보기:\n{rag_context.get('context', '')[:200]}...")
            
            print("\n=== 모든 테스트 완료 ===")
            
    except Exception as e:
        print(f"실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 