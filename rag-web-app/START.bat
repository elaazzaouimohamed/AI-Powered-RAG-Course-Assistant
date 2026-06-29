@echo off
echo ==========================================
echo   RAG Explicateur de Cours - Demarrage
echo ==========================================
echo.

echo [1/3] Demarrage du service RAG (FastAPI - port 8001)...
start "RAG Service" cmd /k "cd /d "%~dp0rag-service" && uvicorn main:app --host 0.0.0.0 --port 8001"

timeout /t 3 /nobreak > nul

echo [2/3] Demarrage du backend Spring Boot (port 8080)...
start "Spring Boot" cmd /k "cd /d "%~dp0backend" && mvnw.cmd spring-boot:run"

timeout /t 5 /nobreak > nul

echo [3/3] Demarrage du frontend React (port 5173)...
start "React Dev" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Ouverture dans le navigateur dans 15 secondes...
timeout /t 15 /nobreak > nul
start http://localhost:5173
