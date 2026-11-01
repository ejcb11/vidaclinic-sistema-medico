@echo off
title Control de Consulta Medica - VidaClinic
echo ======================================================================
echo              VIDACLINIC - CONTROL DE CONSULTA MEDICA
echo ======================================================================
echo.
echo Iniciando servidor web Flask...
echo Abriendo en http://127.0.0.1:5000
echo.

python app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Intentando con ruta de Python local...
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" app.py
)
pause
