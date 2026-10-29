# Lance l'application complete : API (port 8000) + interface (port 5173)
#   powershell -ExecutionPolicy Bypass -File .\lancer.ps1
#   ajouter -Entrainer pour re-entrainer les modeles avant le lancement

param([switch]$Entrainer)

$racine = $PSScriptRoot

if ($Entrainer -or -not (Test-Path "$racine\models\metadata.json")) {
    Write-Host "Entrainement des modeles..." -ForegroundColor Green
    Push-Location $racine
    py -3.12 train.py
    Pop-Location
}

if (-not (Test-Path "$racine\frontend\node_modules")) {
    Write-Host "Installation des dependances du frontend..." -ForegroundColor Green
    Push-Location "$racine\frontend"
    npm install
    Pop-Location
}

Write-Host "Demarrage de l'API sur http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$racine\backend'; py -3.12 -m uvicorn main:app --port 8000"

Write-Host "Demarrage de l'interface sur http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$racine\frontend'; npm run dev"

# Attend que l'API reponde avant d'ouvrir le navigateur
for ($i = 0; $i -lt 60; $i++) {
    try {
        Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/health" -TimeoutSec 2 | Out-Null
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}
Start-Process "http://localhost:5173"
Write-Host "Application prete. Fermer les deux fenetres PowerShell pour l'arreter." -ForegroundColor Green
