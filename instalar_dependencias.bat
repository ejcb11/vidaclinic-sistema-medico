@echo off
title Instalador de Dependencias - VidaClinic
echo ======================================================================
echo    INSTALANDO DEPENDENCIAS DE PYTHON PARA VIDACLINIC
echo ======================================================================
echo.
echo Verificando Python en el equipo...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No se encontro Python en el PATH del sistema.
    echo Asegurate de tener Python instalado y marcar la opcion:
    echo "Add Python to PATH" durante la instalacion.
    echo Descarga: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Python detectado correctamente.
echo Instalando Flask, Openpyxl y ReportLab desde requirements.txt...
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo   TODAS LAS DEPENDENCIAS SE INSTALARON CON EXITO!
    echo   Ya puedes iniciar el sistema ejecutando run.bat o: python app.py
    echo ======================================================================
) else (
    echo.
    echo [ERROR] Hubo un problema al instalar las dependencias.
)
echo.
pause
