# instalar_dependencias.ps1
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "         INSTALADOR DE DEPENDENCIAS - VIDACLINIC (PYTHON)" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python detectado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python no está instalado o no se encuentra en el PATH." -ForegroundColor Red
    Write-Host "Descárgalo desde https://www.python.org/ y marca 'Add Python to PATH'." -ForegroundColor Yellow
    Exit 1
}

Write-Host "Instalando dependencias desde requirements.txt..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "  ¡DEPENDENCIAS INSTALADAS CON ÉXITO!" -ForegroundColor Green
    Write-Host "  Inicia el sistema ejecutando: python app.py" -ForegroundColor Cyan
    Write-Host "======================================================================" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] Hubo un error durante la instalación de paquetes." -ForegroundColor Red
}
