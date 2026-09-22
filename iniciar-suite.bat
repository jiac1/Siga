@echo off
REM Levanta los 3 servidores locales de Suite UNAB y abre el navegador.
REM Cada servidor corre en su propia ventana (para ver sus logs/errores).

cd /d "%~dp0"

start "Suite UNAB - shell (8791)" cmd /k python -m http.server 8791 --directory suite-unab
start "Mapa de Calor (8792)" cmd /k python suite-unab\apps\mapa-calor\manage.py runserver 127.0.0.1:8792
start "Estres de Malla (8793)" cmd /k python suite-unab\apps\estres-malla\manage.py runserver 127.0.0.1:8793

timeout /t 2 /nobreak >nul
start http://localhost:8791/index.html
