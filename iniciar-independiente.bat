@echo off
REM Suite UNAB - cada aplicacion por separado (sin inicio de sesion unico), como el prototipo
cd /d "%~dp0"
python scripts\dev\suite.py independiente
