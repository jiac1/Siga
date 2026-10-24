@echo off
REM Suite UNAB - inicia la Suite completa en http://localhost:8080
REM Primera vez:  pip install -r requirements-dev.txt  y luego  python scripts\dev\suite.py preparar
cd /d "%~dp0"
if not exist .env copy .env.example .env >nul
python scripts\dev\suite.py iniciar
