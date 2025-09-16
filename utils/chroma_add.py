import os
import chromadb
from pathlib import Path
from typing import List, Dict, Any
import hashlib
from datetime import datetime


class ChromaDBUploader:
    """텍스트 파일을 ChromaDB에 업로드하는 간소화된 클래스"""
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "documents"):
        self.client = chromadb.PersistentClient(path=db_path)
        
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except:
            self.collection = self.client.create_collection(name=collection_name)
    
    def read_file(self, file_path: str) -> str:
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except:
                continue
        
        raise ValueError(f"파일을 읽을 수 없습니다: {file_path}")
    
    def split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                for delimiter in ['.', '!', '?', '\n']:
                    pos = text.rfind(delimiter, start, end)
                    if pos > start + chunk_size // 2:
                        end = pos + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def upload_file(self, file_path: str, chunk_size: int = 1000, overlap: int = 200) -> Dict[str, Any]:
        try:
            print(f"📄 처리 중: {Path(file_path).name}")
            
            # 파일 읽기
            content = self.read_file(file_path)
            chunks = self.split_text(content, chunk_size, overlap)
            
            # ChromaDB에 저장
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                doc_id = f"{Path(file_path).stem}_{i}_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
                
                documents.append(chunk)
                metadatas.append({
                    'file_name': Path(file_path).name,
                    'file_path': file_path,
                    'chunk_index': i,
                    'upload_date': datetime.now().isoformat()
                })
                ids.append(doc_id)
            
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
            
            print(f"✅ 완료: {len(chunks)}개 청크 생성")
            return {
                'success': True,
                'file_name': Path(file_path).name,
                'chunks': len(chunks),
                'total_chars': len(content)
            }
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def upload_directory(self, dir_path: str, **kwargs) -> Dict[str, Any]:
        txt_files = list(Path(dir_path).glob("**/*.txt"))
        
        if not txt_files:
            return {'success': False, 'error': 'txt 파일을 찾을 수 없음'}
        
        results = {'success': 0, 'failed': 0, 'total': len(txt_files)}
        
        for file_path in txt_files:
            result = self.upload_file(str(file_path), **kwargs)
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    def search(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """문서 검색"""
        try:
            results = self.collection.query(query_texts=[query], n_results=n_results)
            return {
                'success': True,
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0],
                'distances': results['distances'][0]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계"""
        try:
            count = self.collection.count()
            return {'total_documents': count}
        except Exception as e:
            return {'error': str(e)}


if __name__ == "__main__":
    # 업로더 초기화
    uploader = ChromaDBUploader(collection_name="test_collection")
    
    # 현재 상태 확인
    stats = uploader.get_stats()
    if 'error' not in stats:
        print(f"📊 현재 문서 수: {stats['total_documents']}")
    
    # 테스트용 텍스트 파일 생성
    test_file = "test_document.txt"
    test_content = """
    이것은 테스트 문서입니다.
    ChromaDB 업로더가 정상적으로 작동하는지 확인하기 위한 문서입니다.
    
    여러 문단으로 구성되어 있습니다.
    각 문단은 서로 다른 내용을 담고 있습니다.
    
    이 문서는 청킹되어 여러 조각으로 나뉠 것입니다.
    검색 기능도 테스트해볼 수 있습니다.
    """
    
    # 테스트 파일 생성
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print(f"📝 테스트 파일 생성: {test_file}")
        
        # 파일 업로드 테스트
        result = uploader.upload_file(test_file, chunk_size=100, overlap=20)
        
        if result['success']:
            print(f"✅ 업로드 성공: {result['chunks']}개 청크")
            
            # 검색 테스트
            search_result = uploader.search("테스트 문서", n_results=2)
            if search_result['success']:
                print(f"🔍 검색 결과: {len(search_result['documents'])}개 발견")
                for i, doc in enumerate(search_result['documents'][:2]):
                    print(f"   결과 {i+1}: {doc[:50]}...")
        
        # 최종 통계
        final_stats = uploader.get_stats()
        if 'error' not in final_stats:
            print(f"📊 최종 문서 수: {final_stats['total_documents']}")
        
        # 테스트 파일 정리
        os.remove(test_file)
        print(f"🗑️ 테스트 파일 삭제: {test_file}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")