@echo off
setlocal
cd /d "%~dp0"
title Preparar DrumScore Studio
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m pip install -r requirements.txt
) else (
    python -m pip install -r requirements.txt
)
if errorlevel 1 (
    echo No se pudieron instalar las dependencias. Revisa el mensaje anterior.
) else (
    echo Listo. Abri iniciar_sistema.bat para usar la aplicacion.
)
pause
