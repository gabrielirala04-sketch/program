@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
where py >nul 2>nul
if errorlevel 1 (
    echo Instala Python 3.12 o 3.13 de 64 bits con el lanzador py y vuelve a intentar.
    pause
    exit /b 1
)
py -3 -m venv .venv
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 goto failed
echo Instalacion completa. Abri iniciar_windows.bat.
pause
exit /b 0
:failed
echo No se pudo instalar. Revisa el error anterior y las instrucciones del README.
pause
exit /b 1
