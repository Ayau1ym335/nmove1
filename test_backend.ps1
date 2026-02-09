Set-Location -Path "backend/app"
$env:PYTHONPATH = ".."
python -u test_import.py
