@echo off
REM Cierra los 3 servidores locales de Suite UNAB (busca por puerto).

for %%P in (8791 8792 8793) do (
  for /f "tokens=5" %%I in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
    taskkill /PID %%I /F >nul 2>&1
  )
)
echo Servidores detenidos.
pause
