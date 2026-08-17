$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pyinstaller

pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --noconsole `
  --name "IELTS-Vocabulary-Bridge" `
  --hidden-import "keyring.backends.Windows" `
  launcher.py

Write-Host "Build complete: dist/IELTS-Vocabulary-Bridge.exe"
