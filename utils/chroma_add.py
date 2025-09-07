import os
import chromadb
from pathlib import Path
from typing import List, Dict, Any
import uuid
import hashlib
from datetime import datetime
import re


class ChromaDBUploader:
    """텍스트 파일을 ChromaDB에 업로드하는 클래스"""
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "documents"):
        """
        Args:
            db_path: ChromaDB 데이터베이스 경로
            collection_name: 저장할 컬렉션 이름
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 컬렉션 생성 또는 가져오기
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✅ 기존 컬렉션 '{collection_name}' 연결됨")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": f"텍스트 파일 저장소 - {datetime.now().isoformat()}"}
            )
            print(f"✅ 새 컬렉션 '{collection_name}' 생성됨")
    
    def read_txt_file(self, file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """텍스트 파일 읽기"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            file_info = {
                'content': content,
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'file_size': os.path.getsize(file_path),
                'encoding': encoding,
                'success': True
            }
            return file_info
            
        except UnicodeDecodeError:
            # UTF-8 실패 시 다른 인코딩 시도
            encodings = ['cp949', 'euc-kr', 'latin1']
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    print(f"⚠️ {enc} 인코딩으로 읽음: {file_path}")
                    return {
                        'content': content,
                        'file_path': file_path,
                        'file_name': Path(file_path).name,
                        'file_size': os.path.getsize(file_path),
                        'encoding': enc,
                        'success': True
                    }
                except:
                    continue
            
            return {'success': False, 'error': f'인코딩 오류: {file_path}'}
            
        except Exception as e:
            return {'success': False, 'error': f'파일 읽기 실패 {file_path}: {e}'}
    
    def split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """텍스트를 청크로 분할"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 문장 경계에서 자르기 시도
            if end < len(text):
                # 마지막 마침표, 느낌표, 물음표 찾기
                last_sentence_end = max(
                    text.rfind('.', start, end),
                    text.rfind('!', start, end),
                    text.rfind('?', start, end),
                    text.rfind('\n', start, end)
                )
                
                if last_sentence_end > start + chunk_size // 2:
                    end = last_sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, end - overlap)
            if start >= len(text):
                break
        
        return chunks
    
    def generate_chunk_id(self, file_path: str, chunk_index: int, chunk_text: str) -> str:
        """청크 고유 ID 생성"""
        # 파일 경로와 청크 내용으로 해시 생성
        content_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:8]
        file_name = Path(file_path).stem
        return f"{file_name}_chunk_{chunk_index:03d}_{content_hash}"
    
    def upload_single_file(self, file_path: str, chunk_size: int = 1000, overlap: int = 200) -> Dict[str, Any]:
        """단일 파일을 ChromaDB에 업로드"""
        print(f"📄 처리 중: {file_path}")
        
        # 파일 읽기
        file_info = self.read_txt_file(file_path)
        if not file_info['success']:
            return file_info
        
        # 텍스트 청킹
        chunks = self.split_text_into_chunks(
            file_info['content'], 
            chunk_size=chunk_size, 
            overlap=overlap
        )
        
        if not chunks:
            return {'success': False, 'error': '빈 파일'}
        
        # ChromaDB에 저장
        chunk_ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = self.generate_chunk_id(file_path, i, chunk)
            chunk_ids.append(chunk_id)
            documents.append(chunk)
            
            metadata = {
                'file_path': file_path,
                'file_name': file_info['file_name'],
                'file_size': file_info['file_size'],
                'encoding': file_info['encoding'],
                'chunk_index': i,
                'chunk_count': len(chunks),
                'chunk_size': len(chunk),
                'upload_date': datetime.now().isoformat(),
                'chunk_overlap': overlap
            }
            metadatas.append(metadata)
        
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=chunk_ids
            )
            
            result = {
                'success': True,
                'file_path': file_path,
                'file_name': file_info['file_name'],
                'chunks_created': len(chunks),
                'total_characters': len(file_info['content']),
                'encoding': file_info['encoding']
            }
            print(f"✅ 완료: {len(chunks)}개 청크로 저장됨")
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'ChromaDB 저장 실패: {e}'}
    
    def upload_multiple_files(self, file_paths: List[str], **kwargs) -> Dict[str, Any]:
        """여러 파일을 일괄 업로드"""
        results = {
            'successful_files': [],
            'failed_files': [],
            'total_chunks': 0,
            'total_files': len(file_paths)
        }
        
        for file_path in file_paths:
            result = self.upload_single_file(file_path, **kwargs)
            
            if result['success']:
                results['successful_files'].append(result)
                results['total_chunks'] += result['chunks_created']
            else:
                results['failed_files'].append({
                    'file_path': file_path,
                    'error': result['error']
                })
        
        return results
    
    def upload_directory(self, directory_path: str, **kwargs) -> Dict[str, Any]:
        """디렉토리 내 모든 txt 파일 업로드"""
        txt_files = []
        
        # .txt 파일 찾기
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith('.txt'):
                    txt_files.append(os.path.join(root, file))
        
        if not txt_files:
            return {'success': False, 'error': 'txt 파일을 찾을 수 없음'}
        
        print(f"📁 {directory_path}에서 {len(txt_files)}개 txt 파일 발견")
        return self.upload_multiple_files(txt_files, **kwargs)
    
    def get_upload_stats(self) -> Dict[str, Any]:
        """업로드 통계 조회"""
        try:
            total_docs = self.collection.count()
            
            if total_docs == 0:
                return {'total_documents': 0, 'files': []}
            
            # 모든 문서의 메타데이터 조회
            all_data = self.collection.get(include=['metadatas'])
            metadatas = all_data['metadatas']
            
            # 파일별 통계
            file_stats = {}
            for metadata in metadatas:
                file_name = metadata.get('file_name', 'unknown')
                if file_name not in file_stats:
                    file_stats[file_name] = {
                        'file_name': file_name,
                        'file_path': metadata.get('file_path', ''),
                        'chunk_count': 0,
                        'total_size': metadata.get('file_size', 0),
                        'upload_date': metadata.get('upload_date', ''),
                        'encoding': metadata.get('encoding', '')
                    }
                file_stats[file_name]['chunk_count'] += 1
            
            return {
                'total_documents': total_docs,
                'total_files': len(file_stats),
                'files': list(file_stats.values())
            }
            
        except Exception as e:
            return {'error': f'통계 조회 실패: {e}'}


def main():
    """메인 실행 함수"""
    print("📚 TXT 파일을 ChromaDB에 업로드")
    print("=" * 50)
    
    # 업로더 초기화
    uploader = ChromaDBUploader(
        db_path="./chroma_db",
        collection_name="txt_documents"
    )
    
    # 현재 통계 확인
    # print("\n📊 현재 상태:")
    # stats = uploader.get_upload_stats()
    # if 'error' not in stats:
    #     print(f"총 문서: {stats['total_documents']}개")
    #     print(f"총 파일: {stats['total_files']}개")
    #     if stats['files']:
    #         print("기존 파일들:")
    #         for file_info in stats['files'][:5]:  # 처음 5개만 표시
    #             print(f"  - {file_info['file_name']} ({file_info['chunk_count']} 청크)")
    
    print("\n" + "=" * 50)
    
    # 예제 1: 단일 파일 업로드
    single_file = "/Users/hansol/llm/LLM/data/txt/finance.txt"  # 여기에 실제 txt 파일 경로 입력
    if os.path.exists(single_file):
        print(f"\n🔄 단일 파일 업로드: {single_file}")
        result = uploader.upload_single_file(single_file, chunk_size=500, overlap=100)
        if result['success']:
            print(f"✅ 성공: {result['chunks_created']}개 청크 생성")
        else:
            print(f"❌ 실패: {result['error']}")    
    
    # 예제 3: 특정 파일들 지정
    # specific_files = ["file1.txt", "file2.txt", "file3.txt"]  # 실제 파일 경로로 변경
    # existing_files = [f for f in specific_files if os.path.exists(f)]
    
    # if existing_files:
    #     print(f"\n🔄 지정된 파일들 업로드: {len(existing_files)}개")
    #     result = uploader.upload_multiple_files(existing_files)
    #     print(f"업로드 완료: {len(result['successful_files'])}/{result['total_files']}")
    
    # 최종 통계
    # print("\n📊 최종 통계:")
    # final_stats = uploader.get_upload_stats()
    # if 'error' not in final_stats:
    #     print(f"총 문서: {final_stats['total_documents']}개")
    #     print(f"총 파일: {final_stats['total_files']}개")
    
    # print("\n✨ 업로드 완료!")


if __name__ == "__main__":
    main()