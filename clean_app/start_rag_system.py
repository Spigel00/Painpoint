#!/usr/bin/env python3
"""
RAG System Startup Script
1. Install dependencies
2. Run preprocessing
3. Start server
"""

import os
import sys
import subprocess
import time

def run_command(command, description):
    """Run a command with description"""
    print(f"\n🔄 {description}...")
    print(f"💻 Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"📋 Output: {result.stdout[:200]}...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def main():
    print("🚀 RAG System Startup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found!")
        print("💡 Copy .env.example to .env and fill in your credentials")
        
        if os.path.exists('.env.example'):
            response = input("Would you like me to copy .env.example to .env? (y/n): ")
            if response.lower() == 'y':
                import shutil
                shutil.copy('.env.example', '.env')
                print("✅ .env.example copied to .env")
                print("📝 Please edit .env with your API credentials before continuing")
                return 1
        else:
            print("❌ .env.example not found either")
            return 1
    
    print("✅ .env file found")
    
    # Step 1: Install dependencies
    print("\n📦 Step 1: Installing Dependencies")
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        print("❌ Dependency installation failed")
        return 1
    
    # Step 2: Run preprocessing
    print("\n🤖 Step 2: RAG Preprocessing")
    print("This will fetch Reddit posts, process with Flan-T5, and create vector embeddings...")
    
    response = input("Run preprocessing now? This may take 5-10 minutes (y/n): ")
    if response.lower() == 'y':
        if not run_command("python preprocess_rag.py", "RAG preprocessing"):
            print("❌ Preprocessing failed")
            print("💡 You can run preprocessing later with: python preprocess_rag.py")
    else:
        print("⏸️ Skipping preprocessing")
        print("💡 Run preprocessing later with: python preprocess_rag.py")
    
    # Step 3: Start server
    print("\n🚀 Step 3: Starting RAG Server")
    
    response = input("Start the server now? (y/n): ")
    if response.lower() == 'y':
        print("\n🌐 Starting FastAPI server...")
        print("📝 Frontend: http://localhost:8003")
        print("🔗 API: http://localhost:8003/api/live_problems")
        print("🔍 Search: http://localhost:8003/api/live_problems?query=your_search")
        print("\n💡 Press Ctrl+C to stop the server")
        
        # Change to app directory and start server
        os.chdir('app')
        try:
            subprocess.run("python server.py", shell=True, check=True)
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
        except subprocess.CalledProcessError as e:
            print(f"❌ Server failed to start: {e}")
            return 1
    else:
        print("💡 Start server manually with: cd app && python server.py")
    
    print("\n✅ RAG system setup complete!")
    return 0

if __name__ == "__main__":
    exit(main())
