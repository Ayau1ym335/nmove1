# Restart Backend Server (Required after .env updates)
Write-Host "Stopping existing Python processes..."
taskkill /IM python.exe /F
Start-Sleep -Seconds 2

Write-Host "Starting Backend Server..."
# Using explicit Python path to avoid WindowsApps shim issues
$pythonPath = "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
if (-not (Test-Path $pythonPath)) {
    $pythonPath = (Get-Command python | Select-Object -ExpandProperty Source)
}

Set-Location -Path "backend/app"
$env:PYTHONPATH = ".."
& $pythonPath -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

Read-Host "Backend server stopped. Press Enter to exit..."
