@echo off
cd /d "%~dp0"
echo Démarrage du service RAG (FastAPI)...
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
