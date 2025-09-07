import os
import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import json
import logging
from datetime import datetime


class BaseChromeDBManager:
    """ChromaDB 기본 관리 클래스"""
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = None):
        """ChromaDB 기본 매니저 초기화
        
        Args:
            db_path: ChromaDB 데이터베이스 경로
            collection_name: 사용할 컬렉션 이름 (None이면 컬렉션에 연결하지 않음)
        """
        self.db_path = db_path
        self.collection_name = collection_name
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # ChromaDB 클라이언트 초기화
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            
            # collection_name이 주어진 경우에만 컬렉션에 연결
            if collection_name:
                self.collection = self.client.get_collection(name=collection_name)
                doc_count = self.collection.count()
                self.logger.info(f"컬렉션 '{collection_name}' 연결됨 (문서 수: {doc_count})")
            else:
                self.collection = None
                self.logger.info("ChromaDB 클라이언트만 초기화됨")
                
        except Exception as e:
            if collection_name:
                self.logger.error(f"컬렉션 '{collection_name}' 연결 실패: {e}")
                raise ValueError(f"컬렉션 '{collection_name}'을 찾을 수 없습니다: {e}")
            else:
                self.logger.error(f"ChromaDB 클라이언트 초기화 실패: {e}")
                raise ValueError(f"ChromaDB 연결 실패: {e}")
    
    def __enter__(self):
        """Context manager 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        # 필요시 정리 작업 수행
        pass
    
    # ================== 기본 정보 조회 ==================
    
    def list_all_collections(self) -> List[str]:
        """데이터베이스 내 모든 컬렉션 목록"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            self.logger.error(f"컬렉션 목록 조회 실패: {e}")
            return []
    
    def get_collections_detailed_info(self) -> Dict[str, Any]:
        """모든 컬렉션의 상세 정보 조회"""
        try:
            collections = self.client.list_collections()
            detailed_info = []
            
            for collection in collections:
                try:
                    col_obj = self.client.get_collection(name=collection.name)
                    count = col_obj.count()
                    metadata = collection.metadata or {}
                    
                    # 샘플 메타데이터 키 조회
                    sample_metadata_keys = []
                    if count > 0:
                        sample_data = col_obj.peek(limit=1)
                        if sample_data['metadatas'] and len(sample_data['metadatas']) > 0:
                            sample_metadata_keys = list(sample_data['metadatas'][0].keys())
                    
                    detailed_info.append({
                        "name": collection.name,
                        "document_count": count,
                        "collection_metadata": metadata,
                        "sample_metadata_keys": sample_metadata_keys,
                        "status": "accessible"
                    })
                    
                except Exception as col_error:
                    detailed_info.append({
                        "name": collection.name,
                        "document_count": 0,
                        "collection_metadata": {},
                        "sample_metadata_keys": [],
                        "status": f"error: {col_error}",
                        "error": str(col_error)
                    })
            
            return {
                "total_collections": len(detailed_info),
                "collections": detailed_info,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"컬렉션 상세 정보 조회 실패: {e}")
            return {
                "total_collections": 0,
                "collections": [],
                "status": "error",
                "error": str(e)
            }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """컬렉션 기본 정보 조회"""
        if not self.collection:
            return {"error": "컬렉션이 연결되지 않음", "status": "error"}
            
        try:
            count = self.collection.count()
            metadata = self.collection.metadata or {}
            
            # 샘플 데이터 조회
            sample_metadata_keys = []
            if count > 0:
                sample_data = self.collection.peek(limit=1)
                if sample_data['metadatas'] and len(sample_data['metadatas']) > 0:
                    sample_metadata_keys = list(sample_data['metadatas'][0].keys())
            
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "collection_metadata": metadata,
                "sample_metadata_keys": sample_metadata_keys,
                "db_path": self.db_path,
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"컬렉션 정보 조회 실패: {e}")
            return {"error": f"정보 조회 실패: {e}", "status": "error"}
    
    def get_sample_documents(self, limit: int = 5) -> Dict[str, Any]:
        """샘플 문서 조회"""
        if not self.collection:
            return {"error": "컬렉션이 연결되지 않음", "status": "error"}
            
        try:
            if self.collection.count() == 0:
                return {"sample_count": 0, "documents": [], "status": "empty"}
            
            actual_limit = min(limit, self.collection.count())
            results = self.collection.peek(limit=actual_limit)
            
            documents = []
            for i in range(len(results['ids'])):
                doc_text = results['documents'][i] if results['documents'] else ""
                preview_text = (doc_text[:200] + "...") if len(doc_text) > 200 else doc_text
                
                documents.append({
                    "id": results['ids'][i],
                    "text": preview_text,
                    "full_length": len(doc_text),
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                })
            
            return {
                "sample_count": len(documents),
                "documents": documents,
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"샘플 조회 실패: {e}")
            return {"error": f"샘플 조회 실패: {e}", "status": "error"}


if __name__ == "__main__":
    print("🔥 ChromaDB 컬렉션 확인 도구")
    print("=" * 50)
    
    try:
        # 1. 먼저 컬렉션에 연결하지 않고 클라이언트만 초기화
        print("📁 ChromaDB 연결 중...")
        manager = BaseChromeDBManager(db_path="./chroma_db", collection_name=None)
        
        # 2. 컬렉션 목록 확인
        print("\n📋 사용 가능한 컬렉션:")
        print("-" * 30)
        available_collections = manager.list_all_collections()
        
        if not available_collections:
            print("❌ 컬렉션이 없습니다.")
        else:
            print(f"총 {len(available_collections)}개 컬렉션:")
            for i, name in enumerate(available_collections, 1):
                print(f"  {i}. {name}")
        
        # 3. 상세 정보 확인
        print("\n🗂️ 컬렉션 상세 정보:")
        print("-" * 30)
        detailed_info = manager.get_collections_detailed_info()
        
        if detailed_info['status'] == 'success':
            for collection in detailed_info['collections']:
                print(f"\n컬렉션: {collection['name']}")
                print(f"  📊 문서 수: {collection['document_count']}")
                print(f"  🔍 상태: {collection['status']}")
                if collection['sample_metadata_keys']:
                    print(f"  🏷️ 메타데이터 키: {collection['sample_metadata_keys']}")
                if collection['collection_metadata']:
                    print(f"  📝 컬렉션 메타데이터: {collection['collection_metadata']}")
        else:
            print(f"❌ 상세 정보 조회 실패: {detailed_info.get('error')}")
        
        # 4. 특정 컬렉션에 연결해서 더 자세히 보기 (첫 번째 컬렉션 사용)
        if available_collections:
            first_collection = available_collections[0]
            print(f"\n📄 '{first_collection}' 컬렉션의 샘플 문서:")
            print("-" * 30)
            
            try:
                # 특정 컬렉션에 연결
                collection_manager = BaseChromeDBManager(
                    db_path="./chroma_db", 
                    collection_name=first_collection
                )
                
                # 샘플 문서 조회
                samples = collection_manager.get_sample_documents(limit=3)
                if samples['status'] == 'success' and samples['documents']:
                    for i, doc in enumerate(samples['documents'], 1):
                        print(f"\n문서 {i}:")
                        print(f"  ID: {doc['id']}")
                        print(f"  내용: {doc['text'][:100]}...")
                        print(f"  길이: {doc['full_length']} 글자")
                        print(f"  메타데이터: {doc['metadata']}")
                else:
                    print("샘플 문서가 없습니다.")
                    
            except Exception as e:
                print(f"❌ '{first_collection}' 컬렉션 연결 실패: {e}")
        
        print("\n✨ 컬렉션 확인 완료!")
        
    except Exception as e:
        print(f"❌ ChromaDB 연결 실패: {e}")
        print("\n가능한 원인:")
        print("1. chroma_db 폴더가 존재하지 않음")
        print("2. ChromaDB가 설치되지 않음 (pip install chromadb)")
        print("3. 권한 문제")