@echo off
setlocal
cd /d "%~dp0"
title DrumScore Studio
where py >nul 2>nul
if not errorlevel 1 (
    py -3 server.py
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo No se encontro Python. Instala Python 3.10 o superior y activa Add Python to PATH.
    ) else (
        python server.py
    )
)
pause
