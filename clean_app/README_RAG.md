# 🤖 RAG-Powered Reddit Tech Problems Pipeline

A sophisticated **Retrieval-Augmented Generation (RAG)** system that fetches Reddit tech problems, processes them with AI (Flan-T5), generates semantic embeddings, and provides intelligent search capabilities.

## 🚀 Features

- **🔍 Semantic Search**: AI-powered search using vector embeddings
- **🤖 Flan-T5 Processing**: Advanced NLP for problem statement generation
- **📊 Vector Database**: ChromaDB for fast similarity search
- **🎯 Smart Categorization**: Automatic tech problem categorization
- **⚡ Pre-processing**: All processing done before hosting (no delays)
- **🌐 Modern UI**: React-style frontend with search capabilities

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Reddit API    │ -> │   Flan-T5 NLP   │ -> │  Vector Store   │
│  (30+ subs)     │    │   Processing     │    │   (ChromaDB)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐              │
│   Frontend UI   │ <- │   FastAPI RAG    │ <────────────┘
│  (Search + UI)  │    │     Server       │
└─────────────────┘    └──────────────────┘
```

## 📁 Project Structure

```
clean_app/
├── app/
│   └── server.py              # RAG FastAPI server
├── backend/
│   └── app/
│       ├── services/
│       │   ├── nlp_processor.py    # Flan-T5 processing
│       │   └── vector_store.py     # ChromaDB operations
│       ├── utils/
│       │   └── reddit_search.py    # Reddit API client
│       └── config/
│           └── subreddits.py       # Target subreddits
├── frontend/
│   └── index.html             # Modern search UI
├── preprocess_rag.py          # RAG preprocessing script
├── start_rag_system.py        # Complete setup script
├── .env.example               # Environment template
└── requirements.txt           # Python dependencies
```

## 🛠️ Quick Setup

### Option 1: Automated Setup
```bash
python start_rag_system.py
```

### Option 2: Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API credentials

# 3. Run preprocessing (5-10 minutes)
python preprocess_rag.py

# 4. Start server
cd app && python server.py
```

## 🔧 Configuration

### Environment Variables (.env)
```env
# Reddit API (required)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=your_app_name
REDDIT_USERNAME=your_username

# Hugging Face (optional - uses default model)
HUGGINGFACEHUB_API_TOKEN=your_token
HUGGINGFACE_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Database
DATABASE_URL=sqlite:///painpoint_data.db
```

## 🤖 RAG System Details

### 1. **Data Collection**
- **Sources**: 30+ tech subreddits (r/programming, r/webdev, etc.)
- **Volume**: ~50 posts per subreddit (1500+ total)
- **Filtering**: Advanced tech-only content filtering

### 2. **AI Processing**
- **Model**: Google Flan-T5-base for text generation
- **Task**: Convert verbose complaints → concise problem statements
- **Fallback**: Enhanced rule-based processing

### 3. **Vector Store**
- **Database**: ChromaDB (persistent storage)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Search**: Semantic similarity with cosine distance

### 4. **Categorization**
- Web Development
- Mobile Development  
- Software Development
- System Administration
- Database Issues
- Hardware/Performance
- Cloud/DevOps
- Security

## 🔍 API Endpoints

### GET `/api/live_problems`
Browse or search problems
```
# Browse all
GET /api/live_problems?limit=20

# Semantic search
GET /api/live_problems?query=React+build+error&category=Web+Development&limit=10
```

### POST `/api/search`
Advanced search
```json
{
  "query": "PostgreSQL connection timeout",
  "category": "Database",
  "limit": 5
}
```

### GET `/api/categories`
Get available categories

### GET `/api/status`
System status and stats

## 🎯 Search Examples

Try these semantic searches:
- `"React build error"` → Finds webpack, compilation, deployment issues
- `"PostgreSQL timeout"` → Finds connection, performance, config issues  
- `"Docker crashes"` → Finds container, memory, startup issues
- `"Python performance"` → Finds optimization, slow code issues

## 🔄 Preprocessing Pipeline

```python
# Run full preprocessing
python preprocess_rag.py

# Clear and reprocess
python preprocess_rag.py --clear
```

**Process**:
1. Fetch posts from 30+ subreddits
2. Filter tech-relevant problems
3. Generate AI summaries with Flan-T5
4. Create vector embeddings
5. Store in ChromaDB
6. Create backup JSON

## 🌐 Frontend Features

- **🔍 Real-time Search**: Type and search instantly
- **📂 Category Filtering**: Filter by tech domain
- **🎯 Similarity Scores**: See relevance percentages
- **📱 Responsive Design**: Works on all devices
- **🔗 Direct Links**: Jump to original Reddit posts

## 📊 Performance

- **Search Speed**: <100ms for semantic queries
- **Vector Store**: Persistent disk storage
- **Embedding Model**: 384-dimensional vectors
- **Memory Usage**: ~500MB for full dataset
- **Preprocessing**: ~5-10 minutes for 1500+ posts

## 🔧 Troubleshooting

### Vector Store Empty
```bash
# Check if preprocessing ran
python preprocess_rag.py

# Check vector store stats
python -c "from backend.app.services.vector_store import VectorStore; print(VectorStore().get_stats())"
```

### Search Not Working
1. Verify vector store has data
2. Check server logs for embedding errors
3. Ensure ChromaDB dependencies installed

### Preprocessing Fails
1. Check Reddit API credentials in .env
2. Verify internet connection
3. Check Hugging Face model download

## 🚀 Deployment

### Local Development
```bash
cd app && python server.py
# Access: http://localhost:8003
```

### Production (Docker)
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN python preprocess_rag.py
CMD ["python", "app/server.py"]
```

## 📈 Future Enhancements

- [ ] Real-time Reddit stream processing
- [ ] Multiple embedding models
- [ ] User feedback for relevance tuning
- [ ] Advanced filtering (date, score, etc.)
- [ ] Export search results
- [ ] Similar problem recommendations

## 🤝 Contributing

1. Fork the repository
2. Run preprocessing: `python preprocess_rag.py`
3. Make changes
4. Test search functionality
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

---

**🎯 Key Difference from Previous Version:**
- **Before**: Simple cache with 2-hour refresh cycles
- **Now**: Full RAG system with semantic search, pre-processing, and vector embeddings
- **Search**: Intelligent similarity matching vs. simple category browsing
- **Performance**: Instant search vs. periodic delays
