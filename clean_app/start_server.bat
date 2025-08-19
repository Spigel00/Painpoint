@echo off
echo 🚀 Starting Reddit Tech Problems Server...
echo.
echo 📂 Activating Python environment...
call ..\.venv\Scripts\activate.bat

echo 📡 Starting server on http://localhost:8003...
cd app
python server.py

pause
