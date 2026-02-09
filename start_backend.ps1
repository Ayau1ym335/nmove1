# Start Backend Server
# Using explicit Python path to avoid WindowsApps shim issues
$pythonPath = "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
if (-not (Test-Path $pythonPath)) {
    Write-Host "Python not found at $pythonPath. Trying to find it..."
    # Fallback or search
    $pythonPath = (Get-Command python | Select-Object -ExpandProperty Source)
}

Write-Host "Using Python: $pythonPath"
Set-Location -Path "backend/app"
$env:PYTHONPATH = ".."
& $pythonPath -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

Read-Host "Backend server stopped. Press Enter to exit..."
