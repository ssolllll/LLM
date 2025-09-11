import os
import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import json
import logging
from datetime import datetime


class BaseChromeDBManager:
    """ChromaDB Base Management Class"""
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = None, log_path: str = "./logs"):
        """Initialize ChromaDB Base Manager
        
        Args:
            db_path: ChromaDB database path
            collection_name: Collection name to use (if None, does not connect to collection)
            log_path: Directory path where log files will be stored
        """
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Create log directory
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            
            # Connect to collection only if collection_name is provided
            if collection_name:
                self.collection = self.client.get_collection(name=collection_name)
                doc_count = self.collection.count()
                self.logger.info(f"Connected to collection '{collection_name}' (document count: {doc_count})")
            else:
                self.collection = None
                self.logger.info("ChromaDB client initialized only")
                
        except Exception as e:
            if collection_name:
                self.logger.error(f"Failed to connect to collection '{collection_name}': {e}")
                raise ValueError(f"Cannot find collection '{collection_name}': {e}")
            else:
                self.logger.error(f"Failed to initialize ChromaDB client: {e}")
                raise ValueError(f"ChromaDB connection failed: {e}")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Generate log filename with current timestamp
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"chromadb_{current_time}.log"
        log_file_path = self.log_path / log_filename
        
        # Create logger
        self.logger = logging.getLogger(f"ChromaDBManager_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to prevent duplication
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create file handler (save logs to file)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create console handler (output to console)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Log file path information
        self.logger.info(f"Log file created: {log_file_path}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        pass
    
    # ================== Basic Information Retrieval ==================
    
    def list_all_collections(self) -> List[str]:
        """List all collections in the database"""
        try:
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]
            self.logger.info(f"Collection list retrieved successfully: {len(collection_names)} collections")
            return collection_names
        except Exception as e:
            self.logger.error(f"Failed to retrieve collection list: {e}")
            return []
    
    def get_collections_detailed_info(self) -> Dict[str, Any]:
        """Retrieve detailed information for all collections"""
        try:
            collections = self.client.list_collections()
            detailed_info = []
            
            for collection in collections:
                try:
                    col_obj = self.client.get_collection(name=collection.name)
                    count = col_obj.count()
                    metadata = collection.metadata or {}
                    
                    # Retrieve sample metadata keys
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
                    
                    self.logger.info(f"Collection '{collection.name}' info collected successfully (document count: {count})")
                    
                except Exception as col_error:
                    detailed_info.append({
                        "name": collection.name,
                        "document_count": 0,
                        "collection_metadata": {},
                        "sample_metadata_keys": [],
                        "status": f"error: {col_error}",
                        "error": str(col_error)
                    })
                    self.logger.error(f"Failed to collect info for collection '{collection.name}': {col_error}")
            
            self.logger.info(f"Detailed info retrieval completed for all collections: {len(detailed_info)} collections")
            return {
                "total_collections": len(detailed_info),
                "collections": detailed_info,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve detailed collection information: {e}")
            return {
                "total_collections": 0,
                "collections": [],
                "status": "error",
                "error": str(e)
            }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Retrieve basic collection information"""
        if not self.collection:
            self.logger.warning("Cannot retrieve collection info - no collection connected")
            return {"error": "No collection connected", "status": "error"}
            
        try:
            count = self.collection.count()
            metadata = self.collection.metadata or {}
            
            # Retrieve sample data
            sample_metadata_keys = []
            if count > 0:
                sample_data = self.collection.peek(limit=1)
                if sample_data['metadatas'] and len(sample_data['metadatas']) > 0:
                    sample_metadata_keys = list(sample_data['metadatas'][0].keys())
            
            self.logger.info(f"Collection '{self.collection_name}' info retrieved successfully (document count: {count})")
            
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "collection_metadata": metadata,
                "sample_metadata_keys": sample_metadata_keys,
                "db_path": self.db_path,
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"Failed to retrieve collection information: {e}")
            return {"error": f"Info retrieval failed: {e}", "status": "error"}
    
    def get_sample_documents(self, limit: int = 5) -> Dict[str, Any]:
        """Retrieve sample documents"""
        if not self.collection:
            self.logger.warning("Cannot retrieve sample documents - no collection connected")
            return {"error": "No collection connected", "status": "error"}
            
        try:
            if self.collection.count() == 0:
                self.logger.info("Collection is empty")
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
            
            self.logger.info(f"Sample documents retrieved successfully: {len(documents)} documents")
            
            return {
                "sample_count": len(documents),
                "documents": documents,
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"Sample retrieval failed: {e}")
            return {"error": f"Sample retrieval failed: {e}", "status": "error"}

if __name__ == "__main__":
    try:
        # 1. Initialize client only without connecting to collection
        manager = BaseChromeDBManager(db_path="./chroma_db", collection_name=None)
        
        # 2. Check collection list
        available_collections = manager.list_all_collections()
        
        if not available_collections:
            print("No collections found")
        else:
            print(f"Total {len(available_collections)} collections:")
            for i, name in enumerate(available_collections, 1):
                print(f"  {i}. {name}")
        
        # 3. Check detailed information
        print("\nCollection detailed information:")
        detailed_info = manager.get_collections_detailed_info()
        
        if detailed_info['status'] == 'success':
            for collection in detailed_info['collections']:
                print(f"Collection: {collection['name']}")
                print(f"Document count: {collection['document_count']}")
                print(f"Status: {collection['status']}")
                if collection['sample_metadata_keys']:
                    print(f"Metadata keys: {collection['sample_metadata_keys']}")
                if collection['collection_metadata']:
                    print(f"Collection metadata: {collection['collection_metadata']}")
                print("-" * 40)
        else:
            print(f"Failed to retrieve detailed information: {detailed_info.get('error')}")
        
        # 4. Connect to specific collection for more details (using first collection)
        if available_collections:
            first_collection = available_collections[0]
            print(f"\nSample documents from '{first_collection}' collection:")
            try:
                # Connect to specific collection
                collection_manager = BaseChromeDBManager(
                    db_path="./chroma_db", 
                    collection_name=first_collection
                )
                
                # Retrieve sample documents
                samples = collection_manager.get_sample_documents(limit=3)
                if samples['status'] == 'success' and samples['documents']:
                    for i, doc in enumerate(samples['documents'], 1):
                        print(f"Document {i}:")
                        print(f"ID: {doc['id']}")
                        print(f"Content: {doc['text'][:100]}...")
                        print(f"Length: {doc['full_length']} characters")
                        print(f"Metadata: {doc['metadata']}")
                        print("-" * 30)
                else:
                    print("No sample documents available.")
                    
            except Exception as e:
                print(f"Failed to connect to '{first_collection}' collection: {e}")
        
        print("\nCollection inspection completed!")
        
    except Exception as e:
        print(f"ChromaDB connection failed: {e}")