# PainPoint AI - System Flow & Integration Guide

## 🌊 Complete System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PAINPOINT AI SYSTEM FLOW                              │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   REDDIT API    │────│  Data Collection │────│   Raw Tech Posts    │
│   30+ Subreddits│    │  (preprocess_rag │    │   (Title + Content) │
│   Technical Only │    │     .py)         │    │                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                │                           │
                                ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          NLP PROCESSING PIPELINE                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────────────┐│
│  │  Text Cleaning  │─▶│   Flan-T5-Base  │─▶│    "Users..." Problem Statements ││
│  │   & Validation  │  │  AI Generation  │  │     Enhanced Format Output       ││
│  │                 │  │                 │  │                                  ││
│  └─────────────────┘  └─────────────────┘  └──────────────────────────────────┘│
│                                │                           │                    │
│                                ▼                           ▼                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                    FALLBACK MECHANISMS                                      │
│  │  Rule-Based Processing │ Error Handling │ Quality Validation               │
│  └─────────────────────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         EMBEDDING GENERATION                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │              Sentence-Transformers (all-MiniLM-L6-v2)                      │
│  │                     768-dimensional embeddings                             │
│  └─────────────────────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           VECTOR STORAGE                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                         ChromaDB                                           │
│  │  • 296 Enhanced Problem Statements                                         │
│  │  • Persistent vector database                                              │
│  │  • Metadata: subreddit, category, tech_flag                               │
│  │  • Cosine similarity search ready                                          │
│  └─────────────────────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          SEARCH & RETRIEVAL                                     │
│                                                                                 │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐│
│  │   User Query    │───▶│  Query Embedding │───▶│    Semantic Similarity      ││
│  │   "performance" │    │  (Same Model)    │    │    Search (ChromaDB)        ││
│  └─────────────────┘    └──────────────────┘    └─────────────────────────────┘│
│                                                              │                  │
│                                                              ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                         RESULT RANKING                                     │
│  │  • Cosine similarity scores (0.0-1.0)                                      │
│  │  • Tech-only filtering (157/296 documents)                                 │
│  │  • Category-based organization                                             │
│  │  • Configurable result limits                                              │
│  └─────────────────────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            WEB INTERFACE                                        │
│                                                                                 │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐│
│  │   Frontend      │    │   FastAPI Server │    │      API Endpoints          ││
│  │   (React-like)  │◄──▶│   (server.py)    │◄──▶│  /api/live_problems         ││
│  │   Interactive   │    │   Port 8004      │    │  JSON responses             ││
│  │   Search UI     │    │                  │    │                             ││
│  └─────────────────┘    └──────────────────┘    └─────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘

```

## 🗂️ File Integration Map

### Core Processing Files:

```
preprocess_rag.py
    ├── Imports: backend.app.services.nlp_processor
    ├── Imports: backend.app.services.vector_store
    ├── Function: process_reddit_data()
    ├── Calls: generate_problem_statement() ◄── AI Processing
    └── Calls: VectorStore.add_document() ◄── Storage

backend/app/services/nlp_processor.py
    ├── Model: Flan-T5-Base (google/flan-t5-base)
    ├── Function: generate_problem_statement()
    ├── Function: _ai_generate_problem_statement()
    ├── Function: _clean_text()
    └── Fallback: _rule_based_summary()

backend/app/services/vector_store.py
    ├── Model: sentence-transformers/all-MiniLM-L6-v2
    ├── Database: ChromaDB (persistent)
    ├── Function: add_document()
    ├── Function: search_problems()
    └── Function: get_tech_only_results()

app/server.py
    ├── Framework: FastAPI
    ├── Imports: backend.app.services.vector_store
    ├── Endpoint: /api/live_problems
    ├── Serves: frontend/ static files
    └── Port: 8004
```

### Frontend Integration:

```
app/frontend/index.html
    ├── Includes: app.js, styles.css
    ├── Search form with tech-only checkbox
    └── Results display container

app/frontend/app.js
    ├── Function: searchProblems()
    ├── Calls: /api/live_problems?query=...&tech_only=...
    ├── Function: displayResults()
    └── Event: Real-time search on input

app/frontend/styles.css
    ├── Modern UI styling
    ├── Category-based color coding
    └── Responsive design
```

## 🔄 Data Flow Sequence

### 1. Initial Setup (One-time):
```
1. Reddit API → Raw posts (30+ subreddits)
2. nlp_processor.py → AI problem statements
3. vector_store.py → Embeddings + ChromaDB storage
4. Result: 296 enhanced documents ready for search
```

### 2. User Search (Real-time):
```
1. User types query → frontend/app.js
2. JavaScript → AJAX call → server.py
3. server.py → vector_store.py → ChromaDB search
4. ChromaDB → similarity results → server.py
5. server.py → JSON response → frontend
6. frontend → display formatted results
```

### 3. Enhanced NLP Processing Flow:
```
Raw Reddit Post
    ↓
"Python code is running slowly. I have a script that processes large CSV files..."
    ↓ (Text Cleaning)
Cleaned text: "python code running slowly script processes large csv files hours complete using pandas numpy performance terrible suggestions optimization"
    ↓ (Flan-T5 AI Processing)
Prompt: "Convert this technical problem into a clear problem statement that starts with 'Users'..."
    ↓ (AI Generation)
Result: "Users experience slow performance that impacts productivity and system usability."
    ↓ (Validation & Embedding)
Final stored document with vector representation
```

## 🎯 Model Integration Details

### Flan-T5 Integration:
```python
# Location: nlp_processor.py
from transformers import pipeline

generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

def _ai_generate_problem_statement(clean_text):
    prompt = f"""Convert this technical problem into a clear problem statement that starts with "Users":

{clean_text}

Problem statement:"""
    
    result = generator(prompt, max_length=100, num_return_sequences=1)
    return result[0]['generated_text']
```

### Sentence-Transformers Integration:
```python
# Location: vector_store.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def _generate_embedding(self, text):
    return self.embedding_model.encode([text])[0].tolist()
```

### ChromaDB Integration:
```python
# Location: vector_store.py
import chromadb

client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection(
    name="reddit_tech_problems",
    embedding_function=None  # We handle embeddings manually
)
```

## 🔧 Configuration Flow

### Environment Setup:
```
1. Install dependencies (requirements.txt)
2. Models auto-download on first run:
   - Flan-T5-Base (~1GB)
   - all-MiniLM-L6-v2 (~400MB)
3. ChromaDB creates persistent storage
4. Server starts on localhost:8004
```

### Model Loading Sequence:
```
1. server.py starts
2. Imports vector_store.py
3. vector_store.py loads sentence-transformers
4. Imports nlp_processor.py (if needed)
5. nlp_processor.py loads Flan-T5
6. ChromaDB connects to persistent database
7. FastAPI server ready to serve requests
```

This integration creates a seamless flow from raw Reddit data through AI processing to user-friendly search results, with each component optimized for its specific role in the pipeline.
