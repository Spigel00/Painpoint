#!/usr/bin/env python3
"""
RAG-Powered Reddit Tech Problems Server
FastAPI server with semantic search using vector embeddings
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
import time
from datetime import datetime

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from backend.app.services.vector_store import VectorStore

# Create FastAPI app
app = FastAPI(title="RAG Reddit Tech Problems API", version="2.0.0")

# Initialize vector store for RAG
print("🚀 Initializing RAG Vector Store...")
vector_store = VectorStore()

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    limit: Optional[int] = 10

# Mount static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def read_root():
    """Serve the frontend HTML"""
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    return FileResponse(html_path)

@app.get("/api/live_problems")
def get_live_problems(
    query: Optional[str] = Query(None, description="Search query for semantic search"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: Optional[int] = Query(20, description="Number of results to return")
):
    """Get tech problems using RAG semantic search"""
    try:
        if query:
            # Semantic search with query
            print(f"🔍 RAG Search: '{query}' (category: {category}, limit: {limit})")
            results = vector_store.search_similar(
                query=query,
                n_results=limit,
                category_filter=category
            )
            
            # Organize by category
            categories = {}
            for result in results:
                cat = result.get('category', 'General Tech')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(result)
            
            return {
                "status": "success",
                "search_query": query,
                "data": categories,
                "total_found": len(results),
                "message": f"Found {len(results)} problems matching '{query}'",
                "search_type": "semantic"
            }
        else:
            # Get random sample by category
            print(f"📦 Getting sample problems (category: {category}, limit: {limit})")
            
            # Use a generic query to get diverse results
            sample_queries = [
                "software bug error crash",
                "install setup configuration",
                "performance slow optimization", 
                "database connection issue",
                "web development problem"
            ]
            
            all_results = []
            for sq in sample_queries:
                results = vector_store.search_similar(
                    query=sq,
                    n_results=limit//len(sample_queries) + 2,
                    category_filter=category
                )
                all_results.extend(results)
            
            # Remove duplicates by ID and limit
            seen_ids = set()
            unique_results = []
            for result in all_results:
                if result['id'] not in seen_ids:
                    seen_ids.add(result['id'])
                    unique_results.append(result)
                    if len(unique_results) >= limit:
                        break
            
            # Organize by category
            categories = {}
            for result in unique_results:
                cat = result.get('category', 'General Tech')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(result)
            
            return {
                "status": "success",
                "data": categories,
                "total_found": len(unique_results),
                "message": f"Sample of {len(unique_results)} tech problems",
                "search_type": "sample"
            }
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/api/search")
def search_problems(request: SearchRequest):
    """Dedicated search endpoint for complex queries"""
    try:
        print(f"� Advanced Search: '{request.query}' (category: {request.category})")
        
        results = vector_store.search_similar(
            query=request.query,
            n_results=request.limit,
            category_filter=request.category
        )
        
        return {
            "status": "success",
            "query": request.query,
            "results": results,
            "total_found": len(results),
            "search_type": "advanced_semantic"
        }
        
    except Exception as e:
        print(f"❌ Search Error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/api/categories")
def get_categories():
    """Get available problem categories"""
    try:
        categories = vector_store.get_all_categories()
        return {
            "status": "success",
            "categories": ["All"] + categories
        }
    except Exception as e:
        print(f"❌ Categories Error: {e}")
        raise HTTPException(status_code=500, detail=f"Categories error: {str(e)}")

@app.get("/api/status")
def get_status():
    """Get RAG system status"""
    try:
        stats = vector_store.get_stats()
        
        return {
            "status": "running",
            "system_type": "RAG (Retrieval-Augmented Generation)",
            "vector_store": "ChromaDB",
            "embedding_model": stats.get("embedding_model", "unknown"),
            "total_documents": stats.get("total_documents", 0),
            "categories": stats.get("categories", []),
            "collection_name": stats.get("collection_name", "unknown"),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Status Error: {e}")
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")

@app.get("/api/similar/{problem_id}")
def get_similar_problems(problem_id: str, limit: int = 5):
    """Get problems similar to a specific problem"""
    try:
        # This would require storing problem text by ID
        # For now, return empty
        return {
            "status": "success",
            "similar_problems": [],
            "message": "Similar problems feature coming soon"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Check if vector store has data
    stats = vector_store.get_stats()
    total_docs = stats.get("total_documents", 0)
    
    if total_docs == 0:
        print("⚠️  WARNING: Vector store is empty!")
        print("💡 Run preprocessing first: python preprocess_rag.py")
        print("🔄 Starting server anyway (will return empty results)")
    else:
        print(f"✅ Vector store ready with {total_docs} documents")
    
    print("🚀 Starting RAG Reddit Tech Problems Server on http://localhost:8004")
    print("📝 Frontend: http://localhost:8004")
    print("🔗 API: http://localhost:8004/api/live_problems")
    print("🔍 Search: http://localhost:8004/api/live_problems?query=your_search")
    
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
