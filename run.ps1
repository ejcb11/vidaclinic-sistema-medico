# run.ps1 - Lanzador para PowerShell
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "             VIDACLINIC - CONTROL DE CONSULTA MEDICA" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Iniciando servidor web en http://127.0.0.1:5000 ..." -ForegroundColor Yellow

$pythonPath = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (Test-Path $pythonPath) {
    & $pythonPath app.py
} else {
    python app.py
}
