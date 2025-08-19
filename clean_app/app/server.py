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
    limit: Optional[int] = Query(20, description="Number of results to return"),
    tech_only: Optional[bool] = Query(True, description="Show only tech-related subreddits")
):
    """Get tech problems using RAG semantic search"""
    try:
        if query:
            # Semantic search with query
            print(f"🔍 RAG Search: '{query}' (category: {category}, limit: {limit}, tech_only: {tech_only})")
            results = vector_store.search_similar(
                query=query,
                n_results=limit,
                category_filter=category
            )
            
            # Apply tech filter if requested
            if tech_only:
                tech_subreddits = {
                    'learnprogramming', 'webdev', 'sysadmin', 'techsupport', 'softwaregore',
                    'uxdesign', 'userexperience', 'saas', 'sideproject', 'startups', 
                    'indianstartups', 'entrepreneur', 'notion', 'obsidianmd', 'trello',
                    'futurology', 'productivity'
                }
                results = [r for r in results if r.get('subreddit', '').lower() in tech_subreddits]
            
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
                "message": f"Found {len(results)} problems matching '{query}'" + (" (tech subreddits only)" if tech_only else ""),
                "search_type": "semantic",
                "tech_only": tech_only
            }
        else:
            # Get all documents or browse by category
            print(f"📦 Getting all problems (category: {category}, limit: {limit}, tech_only: {tech_only})")
            
            # Get all documents from vector store
            all_results = vector_store.get_all_documents(
                limit=limit if limit <= 100 else 1000,  # Safety limit
                category_filter=category,
                tech_only=tech_only
            )
            
            # If no specific limit, show more results
            if limit == 20:  # Default limit
                limit = min(100, len(all_results))  # Show up to 100 by default
                all_results = all_results[:limit]
            
            # Organize by category
            categories = {}
            for result in all_results:
                cat = result.get('category', 'General Tech')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(result)
            
            total_found = len(all_results)
            message = f"Showing {total_found} problems"
            if category and category != "All":
                message += f" in {category}"
            if tech_only:
                message += " (tech subreddits only)"
            
            return {
                "status": "success",
                "data": categories,
                "total_found": total_found,
                "message": message,
                "search_type": "browse_all",
                "tech_only": tech_only
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
