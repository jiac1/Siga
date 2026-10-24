@echo off
REM Suite UNAB - detiene los servidores locales (gateway, servicios y modo independiente)
for %%P in (8080 8001 8002 8003 8791 8792 8793) do (
  for /f "tokens=5" %%I in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
    taskkill /PID %%I /F >nul 2>&1
  )
)
echo Servidores de Suite UNAB detenidos.
pause
