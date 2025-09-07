import pandas as pd
from typing import Dict, Any, Optional
from collections import defaultdict
from .base_manager import BaseChromeDBManager


class AnalyticsManager(BaseChromeDBManager):
    """분석 및 통계 전담 관리 클래스"""
    
    def get_statistics(self) -> Dict[str, Any]:
        """컬렉션 통계 정보"""
        try:
            total_docs = self.collection.count()
            
            if total_docs == 0:
                return {
                    "total_documents": 0,
                    "status": "empty"
                }
            
            # 전체 데이터 조회 (중간 규모 컬렉션까지)
            if total_docs <= 5000:  # 임계값 조정
                all_data = self.collection.get(include=["documents", "metadatas"])
                
                # 메타데이터 분석
                metadata_stats = defaultdict(lambda: {"values": defaultdict(int), "count": 0})
                
                if all_data['metadatas']:
                    for metadata in all_data['metadatas']:
                        if metadata:  # None 체크
                            for key, value in metadata.items():
                                metadata_stats[key]["values"][str(value)] += 1
                                metadata_stats[key]["count"] += 1
                
                # 결과 정리
                final_metadata_stats = {}
                for key, stats in metadata_stats.items():
                    final_metadata_stats[key] = {
                        "unique_values": list(stats["values"].keys()),
                        "unique_count": len(stats["values"]),
                        "total_count": stats["count"],
                        "value_distribution": dict(stats["values"])
                    }
                
                # 문서 길이 분석
                doc_lengths = []
                if all_data['documents']:
                    doc_lengths = [len(doc) for doc in all_data['documents'] if doc]
                
                if doc_lengths:
                    avg_length = sum(doc_lengths) / len(doc_lengths)
                    return {
                        "total_documents": total_docs,
                        "document_statistics": {
                            "average_length": round(avg_length, 2),
                            "min_length": min(doc_lengths),
                            "max_length": max(doc_lengths),
                            "total_characters": sum(doc_lengths)
                        },
                        "metadata_statistics": final_metadata_stats,
                        "status": "success"
                    }
                else:
                    return {
                        "total_documents": total_docs,
                        "metadata_statistics": final_metadata_stats,
                        "note": "문서 내용이 없습니다",
                        "status": "success"
                    }
            else:
                # 대용량 컬렉션의 경우 샘플링
                sample_size = 1000
                sample_data = self.collection.peek(limit=sample_size)
                
                return {
                    "total_documents": total_docs,
                    "note": f"대용량 컬렉션으로 인해 {sample_size}개 샘플 기반 통계",
                    "sampled_statistics": self._analyze_sample_data(sample_data),
                    "status": "sampled"
                }
                
        except Exception as e:
            self.logger.error(f"통계 생성 실패: {e}")
            return {"error": f"통계 생성 실패: {e}", "status": "error"}
    
    def _analyze_sample_data(self, sample_data: Dict) -> Dict[str, Any]:
        """샘플 데이터 분석"""
        stats = {}
        
        # 문서 길이 분석
        if sample_data['documents']:
            doc_lengths = [len(doc) for doc in sample_data['documents'] if doc]
            if doc_lengths:
                stats["document_lengths"] = {
                    "average": round(sum(doc_lengths) / len(doc_lengths), 2),
                    "min": min(doc_lengths),
                    "max": max(doc_lengths)
                }
        
        # 메타데이터 키 분석
        if sample_data['metadatas']:
            all_keys = set()
            for metadata in sample_data['metadatas']:
                if metadata:
                    all_keys.update(metadata.keys())
            stats["metadata_keys"] = list(all_keys)
        
        return stats
    
    def get_source_file_statistics(self) -> Dict[str, Any]:
        """소스 파일별 통계"""
        try:
            all_data = self.collection.get(
                limit=10000,  # 안전한 제한
                include=["documents", "metadatas"]
            )
            
            file_stats = defaultdict(lambda: {
                "chunk_count": 0,
                "total_length": 0,
                "avg_chunk_length": 0,
                "chunks": []
            })
            
            if all_data['metadatas']:
                for i, metadata in enumerate(all_data['metadatas']):
                    if metadata and "source_file" in metadata:
                        source_file = metadata["source_file"]
                        doc_length = len(all_data['documents'][i]) if all_data['documents'] else 0
                        
                        file_stats[source_file]["chunk_count"] += 1
                        file_stats[source_file]["total_length"] += doc_length
                        file_stats[source_file]["chunks"].append({
                            "id": all_data['ids'][i],
                            "length": doc_length,
                            "chunk_index": metadata.get("chunk_index", 0)
                        })
            
            # 평균 계산
            for file_name, stats in file_stats.items():
                if stats["chunk_count"] > 0:
                    stats["avg_chunk_length"] = round(
                        stats["total_length"] / stats["chunk_count"], 2
                    )
            
            return { 
                "total_files": len(file_stats),
                "file_statistics": dict(file_stats),
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"파일별 통계 생성 실패: {e}")
            return {"error": f"파일별 통계 생성 실패: {e}", "status": "error"}
    
    def get_chunk_strategy_analysis(self) -> Dict[str, Any]:
        """청킹 전략별 분석"""
        try:
            all_data = self.collection.get(
                limit=10000,
                include=["documents", "metadatas"]
            )
            
            strategy_stats = defaultdict(lambda: {
                "document_count": 0,
                "total_length": 0,
                "avg_length": 0,
                "length_distribution": defaultdict(int)
            })
            
            if all_data['metadatas']:
                for i, metadata in enumerate(all_data['metadatas']):
                    if metadata and "chunk_strategy" in metadata:
                        strategy = metadata["chunk_strategy"]
                        doc_length = len(all_data['documents'][i]) if all_data['documents'] else 0
                        
                        strategy_stats[strategy]["document_count"] += 1
                        strategy_stats[strategy]["total_length"] += doc_length
                        
                        # 길이 범위별 분포
                        length_range = self._get_length_range(doc_length)
                        strategy_stats[strategy]["length_distribution"][length_range] += 1
            
            # 평균 계산
            for strategy, stats in strategy_stats.items():
                if stats["document_count"] > 0:
                    stats["avg_length"] = round(
                        stats["total_length"] / stats["document_count"], 2
                    )
                    stats["length_distribution"] = dict(stats["length_distribution"])
            
            return {
                "total_strategies": len(strategy_stats),
                "strategy_analysis": dict(strategy_stats),
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"청킹 전략 분석 실패: {e}")
            return {"error": f"청킹 전략 분석 실패: {e}", "status": "error"}
    
    def _get_length_range(self, length: int) -> str:
        """문서 길이를 범위로 분류"""
        if length < 100:
            return "0-99"
        elif length < 500:
            return "100-499"
        elif length < 1000:
            return "500-999"
        elif length < 2000:
            return "1000-1999"
        elif length < 5000:
            return "2000-4999"
        else:
            return "5000+"
    
    def export_to_dataframe(self, 
                           limit: Optional[int] = None, 
                           include_embeddings: bool = False) -> pd.DataFrame:
        """데이터를 pandas DataFrame으로 내보내기"""
        try:
            total_count = self.collection.count()
            if total_count == 0:
                return pd.DataFrame()
            
            if limit is None:
                limit = min(total_count, 10000)  # 안전한 기본값
            
            actual_limit = min(limit, total_count)
            
            include_list = ["documents", "metadatas"]
            if include_embeddings:
                include_list.append("embeddings")
            
            results = self.collection.get(limit=actual_limit, include=include_list)
            
            # DataFrame 생성
            data = []
            for i in range(len(results['ids'])):
                row = {
                    'id': results['ids'][i],
                    'document': results['documents'][i] if results['documents'] else "",
                    'document_length': len(results['documents'][i]) if results['documents'] else 0
                }
                
                # 메타데이터 컬럼 추가
                if results['metadatas'] and i < len(results['metadatas']) and results['metadatas'][i]:
                    metadata = results['metadatas'][i]
                    for key, value in metadata.items():
                        row[f'metadata_{key}'] = value
                
                # 임베딩 추가 (옵션)
                if include_embeddings and results.get('embeddings') and i < len(results['embeddings']):
                    row['embedding'] = results['embeddings'][i]
                
                data.append(row)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            self.logger.error(f"DataFrame 변환 실패: {e}")
            return pd.DataFrame()
    
    def get_similarity_distribution_analysis(self, 
                                           sample_queries: list,
                                           n_results: int = 10) -> Dict[str, Any]:
        """유사도 분포 분석"""
        if not sample_queries:
            return {"error": "샘플 쿼리가 없습니다", "status": "error"}
        
        try:
            from .search_manager import SearchManager
            search_manager = SearchManager(self.db_path, self.collection_name)
            
            similarity_data = []
            
            for query in sample_queries:
                results = search_manager.similarity_search(query, n_results)
                if results.get("status") == "success":
                    for result in results["results"]:
                        similarity = result.get("similarity", 0)
                        similarity_data.append({
                            "query": query,
                            "similarity": similarity,
                            "similarity_range": self._get_similarity_range(similarity)
                        })
            
            if not similarity_data:
                return {"error": "유사도 데이터를 수집할 수 없습니다", "status": "error"}
            
            # 분포 분석
            range_distribution = defaultdict(int)
            similarities = [data["similarity"] for data in similarity_data]
            
            for data in similarity_data:
                range_distribution[data["similarity_range"]] += 1
            
            return {
                "total_samples": len(similarity_data),
                "sample_queries": sample_queries,
                "similarity_stats": {
                    "min": round(min(similarities), 4),
                    "max": round(max(similarities), 4),
                    "average": round(sum(similarities) / len(similarities), 4)
                },
                "distribution": dict(range_distribution),
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"유사도 분포 분석 실패: {e}")
            return {"error": f"유사도 분포 분석 실패: {e}", "status": "error"}
    
    def _get_similarity_range(self, similarity: float) -> str:
        """유사도를 범위로 분류"""
        if similarity >= 0.9:
            return "0.9-1.0"
        elif similarity >= 0.8:
            return "0.8-0.9"
        elif similarity >= 0.7:
            return "0.7-0.8"
        elif similarity >= 0.6:
            return "0.6-0.7"
        elif similarity >= 0.5:
            return "0.5-0.6"
        else:
            return "0.0-0.5"