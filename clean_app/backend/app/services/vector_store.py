#!/usr/bin/env python3
"""
Vector Store for RAG System
Handles embeddings and semantic search using ChromaDB
"""

import os
import sys
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

class VectorStore:
    """ChromaDB vector store for semantic search"""
    
    def __init__(self, collection_name: str = "reddit_tech_problems"):
        self.collection_name = collection_name
        
        # Initialize ChromaDB with persistent storage
        # Use absolute path to ensure consistency across different working directories
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../vector_db"))
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        print("🔄 Loading embedding model...")
        model_name = os.getenv("HUGGINGFACE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_model = SentenceTransformer(model_name)
        print(f"✅ Loaded embedding model: {model_name}")
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            print(f"📦 Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Reddit tech problems with AI summaries"}
            )
            print(f"🆕 Created new collection: {collection_name}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            return [[0.0] * 384] * len(texts)  # Fallback empty embeddings
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to vector store"""
        try:
            if not documents:
                print("⚠️ No documents to add")
                return False
            
            print(f"🔄 Processing {len(documents)} documents...")
            
            # Prepare data for ChromaDB
            ids = []
            embeddings_texts = []
            metadatas = []
            documents_texts = []
            
            for doc in documents:
                # Create unique ID
                doc_id = str(uuid.uuid4())
                ids.append(doc_id)
                
                # Text for embedding (title + AI summary + description)
                embedding_text = f"{doc['title']} {doc.get('ai_problem_statement', '')} {doc.get('description', '')[:200]}"
                embeddings_texts.append(embedding_text)
                
                # Document text (for retrieval)
                documents_texts.append(doc.get('ai_problem_statement', doc['title']))
                
                # Metadata
                metadata = {
                    "title": doc['title'][:500],  # ChromaDB has length limits
                    "subreddit": doc.get('subreddit', ''),
                    "category": doc.get('category', 'General Tech'),
                    "url": doc.get('url', ''),
                    "score": doc.get('score', 0),
                    "created_utc": doc.get('created_utc', 0),
                    "processed_at": doc.get('processed_at', datetime.now().isoformat()),
                    "description": doc.get('description', '')[:500]  # Truncate for storage
                }
                metadatas.append(metadata)
            
            # Generate embeddings
            print("🤖 Generating embeddings...")
            embeddings = self.generate_embeddings(embeddings_texts)
            
            # Add to ChromaDB
            print("💾 Adding to vector store...")
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents_texts
            )
            
            print(f"✅ Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            return False
    
    def search_similar(self, query: str, n_results: int = 10, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Prepare where clause for filtering
            where_clause = {}
            if category_filter and category_filter != "All":
                where_clause["category"] = category_filter
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    result = {
                        "id": results['ids'][0][i],
                        "title": results['metadatas'][0][i]['title'],
                        "ai_problem_statement": results['documents'][0][i],
                        "description": results['metadatas'][0][i]['description'],
                        "category": results['metadatas'][0][i]['category'],
                        "subreddit": results['metadatas'][0][i]['subreddit'],
                        "url": results['metadatas'][0][i]['url'],
                        "score": results['metadatas'][0][i]['score'],
                        "similarity_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                        "processed_at": results['metadatas'][0][i]['processed_at']
                    }
                    formatted_results.append(result)
            
            print(f"🔍 Found {len(formatted_results)} similar documents for query: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        try:
            # Get a sample of documents to extract categories
            results = self.collection.get(
                limit=1000,
                include=["metadatas"]
            )
            
            categories = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if 'category' in metadata:
                        categories.add(metadata['category'])
            
            return sorted(list(categories))
            
        except Exception as e:
            print(f"❌ Error getting categories: {e}")
            return ["General Tech"]
    
    def get_all_documents(self, limit: int = 1000, category_filter: Optional[str] = None, tech_only: bool = False) -> List[Dict[str, Any]]:
        """Get all documents from the collection"""
        try:
            print(f"📦 Getting all documents (limit: {limit}, category: {category_filter}, tech_only: {tech_only})")
            
            # Tech-related subreddits list
            tech_subreddits = {
                'learnprogramming', 'webdev', 'sysadmin', 'techsupport', 'softwaregore',
                'UXDesign', 'userexperience', 'SaaS', 'SideProject', 'startups', 
                'indianstartups', 'Entrepreneur', 'Notion', 'ObsidianMD', 'trello',
                'Futurology', 'productivity'
            }
            
            # Get documents from ChromaDB
            where_filter = {}
            if category_filter and category_filter != "All":
                where_filter["category"] = category_filter
            
            if tech_only:
                # Filter for tech subreddits
                if where_filter:
                    # Can't use complex AND/OR filters easily in ChromaDB, so we'll filter after retrieval
                    results = self.collection.get(
                        limit=limit,
                        where=where_filter,
                        include=["metadatas", "documents"]
                    )
                else:
                    results = self.collection.get(
                        limit=limit,
                        include=["metadatas", "documents"]
                    )
            else:
                if where_filter:
                    results = self.collection.get(
                        limit=limit,
                        where=where_filter,
                        include=["metadatas", "documents"]
                    )
                else:
                    results = self.collection.get(
                        limit=limit,
                        include=["metadatas", "documents"]
                    )
            
            documents = []
            if results['metadatas'] and results['documents']:
                for i, metadata in enumerate(results['metadatas']):
                    subreddit = metadata.get('subreddit', '').lower()
                    
                    # Apply tech filter if requested
                    if tech_only and subreddit not in tech_subreddits:
                        continue
                    
                    doc = {
                        "id": results['ids'][i] if 'ids' in results else f"doc_{i}",
                        "title": metadata.get('title', 'Untitled'),
                        "ai_problem_statement": results['documents'][i],
                        "category": metadata.get('category', 'General Tech'),
                        "subreddit": metadata.get('subreddit', ''),
                        "url": metadata.get('url', ''),
                        "score": metadata.get('score', 0),
                        "description": metadata.get('description', ''),
                        "created_utc": metadata.get('created_utc', 0),
                        "processed_at": metadata.get('processed_at', ''),
                        "similarity_score": 1.0  # All docs are 100% relevant when browsing all
                    }
                    documents.append(doc)
            
            print(f"✅ Retrieved {len(documents)} documents" + (" (tech-filtered)" if tech_only else ""))
            return documents
            
        except Exception as e:
            print(f"❌ Error getting all documents: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            count = self.collection.count()
            categories = self.get_all_categories()
            
            return {
                "total_documents": count,
                "categories": categories,
                "embedding_model": os.getenv("HUGGINGFACE_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {"total_documents": 0, "categories": [], "error": str(e)}
    
    def clear_collection(self):
        """Clear all documents from collection"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Reddit tech problems with AI summaries"}
            )
            print(f"🗑️ Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            print(f"❌ Error clearing collection: {e}")
            return False

if __name__ == "__main__":
    # Test the vector store
    print("🧪 Testing Vector Store...")
    
    vs = VectorStore()
    
    # Test with sample data
    sample_docs = [
        {
            "title": "React app crashes on build",
            "ai_problem_statement": "Debug React build error causing application crash",
            "description": "My React application crashes when I try to build it for production...",
            "category": "Web Development",
            "subreddit": "reactjs",
            "url": "https://reddit.com/test1",
            "score": 45
        },
        {
            "title": "PostgreSQL connection timeout",
            "ai_problem_statement": "Resolve PostgreSQL database connection timeout issues",
            "description": "Database connections are timing out after 30 seconds...",
            "category": "Database",
            "subreddit": "PostgreSQL", 
            "url": "https://reddit.com/test2",
            "score": 23
        }
    ]
    
    # Add documents
    success = vs.add_documents(sample_docs)
    print(f"Add documents success: {success}")
    
    # Search
    results = vs.search_similar("React build problems", n_results=5)
    print(f"Search results: {len(results)}")
    for result in results:
        print(f"  - {result['title']} (similarity: {result['similarity_score']:.3f})")
    
    # Stats
    stats = vs.get_stats()
    print(f"Stats: {stats}")
