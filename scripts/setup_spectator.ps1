# One-time setup for spectator mode (run from repo root)
Write-Host "Installing Python dependencies..."
pip install -e ".[spectator]"

Write-Host "Building frontend..."
Push-Location frontend
npm install
npm run build
Pop-Location

if (-not (Test-Path "Config\secrets.yaml")) {
    Copy-Item "Config\secrets.yaml.example" "Config\secrets.yaml"
    Write-Host ""
    Write-Host "Created Config\secrets.yaml — please edit and add your llm.api_key"
} else {
    Write-Host "Config\secrets.yaml already exists"
}

Write-Host ""
Write-Host "Done. Next steps:"
Write-Host "  1. Edit Config\secrets.yaml and set llm.api_key"
Write-Host "  2. python -m aiwerewolf.api.server"
Write-Host "  3. Open http://127.0.0.1:8000/"
