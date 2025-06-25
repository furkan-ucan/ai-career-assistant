# Akilli Kariyer Asistani - Modern Kod Kalitesi Otomasyonu
# =========================================================
# Modern Python tooling: Ruff + MyPy + Bandit

param(
    [switch]$Check,
    [switch]$Fix,
    [switch]$All
)

# Ana Baslik
Write-Host ""
Write-Host "Akilli Kariyer Asistani - Kod Kalitesi Otomasyonu" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

if ($Check) {
    Write-Host "Kod kalitesi kontrol ediliyor..." -ForegroundColor Cyan

    # Ruff kontrolu (linting + formatting)
    Write-Host "Ruff kod kalitesi kontrolu..." -ForegroundColor White
    ruff check main.py src/ tree_generator.py --diff
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Ruff kod kalitesi sorunlari bulundu!" -ForegroundColor Red
    } else {
        Write-Host "Ruff kod kalitesi OK" -ForegroundColor Green
    }

    # Ruff format kontrolu
    Write-Host "Ruff format kontrolu..." -ForegroundColor White
    ruff format main.py src/ tree_generator.py --check --diff
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Format duzeltilmeli!" -ForegroundColor Red
    } else {
        Write-Host "Format OK" -ForegroundColor Green
    }

    # MyPy tip kontrolu
    Write-Host "MyPy tip kontrolu..." -ForegroundColor White
    mypy main.py src/ tree_generator.py --config-file=pyproject.toml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "MyPy tip uyarilari var (kritik degil)" -ForegroundColor Yellow
    } else {
        Write-Host "MyPy OK" -ForegroundColor Green
    }

    # Bandit guvenlik taramasi
    Write-Host "Bandit guvenlik taramasi..." -ForegroundColor White
    bandit -c pyproject.toml -r main.py src/ tree_generator.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Guvenlik uyarilari var (kontrol edin)" -ForegroundColor Yellow
    } else {
        Write-Host "Guvenlik taramasi OK" -ForegroundColor Green
    }

    # SonarQube analizi (ek kod kalitesi kontrol)
    Write-Host "SonarQube kod kalite analizi..." -ForegroundColor White
    Write-Host "SonarQube analizi VS Code Problems panel'inde goruntulenebilir" -ForegroundColor Yellow
    Write-Host "SonarQube destegi aktif (manuel VS Code analizi)" -ForegroundColor Green
}

if ($Fix) {
    Write-Host "Kod kalitesi sorunlari duzeltiliyor..." -ForegroundColor Cyan

    # Ruff ile otomatik duzeltme
    Write-Host "Ruff otomatik duzeltmeler..." -ForegroundColor White
    ruff check main.py src/ tree_generator.py --fix
    Write-Host "Ruff lint sorunlari duzeltildi" -ForegroundColor Green

    # Ruff ile format duzeltme
    Write-Host "Ruff format duzeltiliyor..." -ForegroundColor White
    ruff format main.py src/ tree_generator.py
    Write-Host "Format duzeltildi" -ForegroundColor Green

    Write-Host "Modern Ruff ile tum duzeltmeler tamamlandi!" -ForegroundColor Green
}

if ($All) {
    Write-Host "Tam kalite kontrolu baslatiliyor..." -ForegroundColor Cyan

    # Once duzelt
    & $PSScriptRoot\quality-check.ps1 -Fix

    # Sonra kontrol et
    & $PSScriptRoot\quality-check.ps1 -Check

    # Testleri calistir
    Write-Host "Testler calistiriliyor..." -ForegroundColor White
    python -m pytest tests/ -v
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Tum testler basarili!" -ForegroundColor Green
    } else {
        Write-Host "Bazi testler basarisiz!" -ForegroundColor Red
    }

    Write-Host "Tam kalite kontrolu tamamlandi!" -ForegroundColor Green
}

# Parametresiz calisirsa yardim goster
if (-not ($Check -or $Fix -or $All)) {
    Write-Host ""
    Write-Host "Kullanim:" -ForegroundColor Yellow
    Write-Host "  .\quality-check.ps1 -Check    # Sadece kontrol et" -ForegroundColor White
    Write-Host "  .\quality-check.ps1 -Fix      # Sorunlari duzelt" -ForegroundColor White
    Write-Host "  .\quality-check.ps1 -All      # Duzelt + kontrol + test" -ForegroundColor White
    Write-Host ""
    Write-Host "Hizli kullanim: .\quality-check.ps1 -All" -ForegroundColor Cyan
}
