# Reddit Tech Problems Pipeline

A clean, simple Reddit NLP pipeline that fetches tech problems from Reddit, processes them with AI, and displays them in a web interface.

## Features

- 🚀 **Instant Loading**: Pre-processed Reddit data for immediate display
- 🤖 **AI Summaries**: Each problem gets an AI-generated problem statement
- 🎯 **Tech Focused**: Filters only technology-related posts
- 📊 **Categorized**: Problems organized by category (Web Dev, Mobile, etc.)
- ⚡ **Fast**: Background processing with cache for instant serving

## Project Structure

```
clean_app/
├── app/
│   └── server.py              # Main FastAPI server
├── frontend/
│   └── index.html            # Web interface
├── services/
│   └── reddit_processor.py   # Reddit processing & NLP
├── backend/                  # Supporting modules
│   └── app/
│       ├── config/
│       │   └── subreddits.py
│       ├── services/
│       │   └── nlp_processor.py
│       └── utils/
│           └── reddit_search.py
├── .env                      # Environment variables
├── requirements.txt          # Dependencies
└── processed_reddit_cache.json  # Pre-processed data cache
```

## Setup & Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**:
   - Ensure `.env` file has Reddit API credentials
   - Make sure the virtual environment is activated

3. **Run the Server**:
   ```bash
   cd app
   python server.py
   ```

4. **Access the Application**:
   - Open http://localhost:8003 in your browser
   - Click "Load Tech Problems" to see live data

## How It Works

1. **Background Processing**: The `reddit_processor.py` fetches posts from 30+ tech subreddits
2. **AI Enhancement**: Each post is processed through Flan-T5 model to generate problem statements
3. **Smart Filtering**: Only tech-related problems are kept, non-tech content is filtered out
4. **Instant Serving**: Processed data is cached and served instantly via FastAPI
5. **Clean Display**: Frontend shows categorized problems with AI summaries

## API Endpoints

- `GET /` - Serves the frontend interface
- `GET /api/live_problems` - Returns processed Reddit problems with AI summaries
- `GET /api/status` - Server status and cache information

## Technologies Used

- **Backend**: FastAPI, Python
- **NLP**: Hugging Face Transformers (Flan-T5)
- **Reddit API**: PRAW (Python Reddit API Wrapper)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Data**: JSON cache for instant serving

## Performance

- **Processing**: ~1,400 Reddit posts → 301 quality tech problems
- **Response Time**: Instant (served from cache)
- **Refresh Rate**: Background refresh every 2 hours
- **Filtering Accuracy**: High-precision tech problem detection

This is a clean, production-ready version of the Reddit NLP pipeline with all unnecessary files removed.
