# Akilli Kariyer Asistani - Otomatik Kod Kalitesi Scripti
# Bu script her calistirildiginda kodu kontrol eder ve duzeltir

param(
    [switch]$Check,      # Sadece kontrol et
    [switch]$Fix,        # Duzelt
    [switch]$All         # Kontrol + test + duzelt
)

Write-Host "Akilli Kariyer Asistani - Kod Kalitesi Otomasyonu" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Sanal ortam aktif mi kontrol et
if (-not (Test-Path "kariyer-asistani-env\Scripts\python.exe")) {
    Write-Host "Sanal ortam bulunamadi! Once 'make setup-env' calistirin." -ForegroundColor Red
    exit 1
}

# Sanal ortami aktiflestir
Write-Host "Sanal ortam aktiflestiiriliyor..." -ForegroundColor Yellow
& ".\kariyer-asistani-env\Scripts\Activate.ps1"

if ($Check) {
    Write-Host "🔍 Kod kalitesi kontrol ediliyor..." -ForegroundColor Cyan

    # Ruff kontrolü (linting + formatting)
    Write-Host "⚡ Ruff kod kalitesi kontrolü..." -ForegroundColor White
    ruff check main.py src/ tree_generator.py --diff
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ruff kod kalitesi sorunları bulundu!" -ForegroundColor Red
    } else {
        Write-Host "✅ Ruff kod kalitesi OK" -ForegroundColor Green
    }

    # Ruff format kontrolü
    Write-Host "🎨 Ruff format kontrolü..." -ForegroundColor White
    ruff format main.py src/ tree_generator.py --check --diff
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Format düzeltilmeli!" -ForegroundColor Red
    } else {
        Write-Host "✅ Format OK" -ForegroundColor Green
    }

    # MyPy tip kontrolü
    Write-Host "🔍 MyPy tip kontrolü..." -ForegroundColor White
    mypy main.py src/ tree_generator.py --config-file=pyproject.toml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ MyPy tip uyarıları var (kritik değil)" -ForegroundColor Yellow
    } else {
        Write-Host "✅ MyPy OK" -ForegroundColor Green
    }

    # Bandit güvenlik taraması
    Write-Host "🔒 Bandit güvenlik taraması..." -ForegroundColor White
    bandit -c pyproject.toml -r main.py src/ tree_generator.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Güvenlik uyarıları var (kontrol edin)" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Güvenlik taraması OK" -ForegroundColor Green
    }

    # Geleneksel araçlar (yedek olarak)
    Write-Host "� Geleneksel araç kontrolü..." -ForegroundColor White

    # Flake8 kontrol (cognitive complexity dahil)
    $lintResult = flake8 main.py src/ tree_generator.py --show-source 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Flake8 uyarıları var:" -ForegroundColor Yellow
        Write-Host $lintResult -ForegroundColor Gray
    } else {
        Write-Host "✅ Flake8 OK" -ForegroundColor Green
    }
}

if ($Fix) {
    Write-Host "🔧 Kod kalitesi sorunları düzeltiliyor..." -ForegroundColor Cyan

    # Ruff ile otomatik düzeltme
    Write-Host "⚡ Ruff otomatik düzeltmeler..." -ForegroundColor White
    ruff check main.py src/ tree_generator.py --fix
    Write-Host "✅ Ruff lint sorunları düzeltildi" -ForegroundColor Green

    # Ruff ile format düzeltme
    Write-Host "🎨 Ruff format düzeltiliyor..." -ForegroundColor White
    ruff format main.py src/ tree_generator.py
    Write-Host "✅ Format düzeltildi" -ForegroundColor Green

    # Geleneksel araçlarla yedek düzeltme
    Write-Host "🔧 Geleneksel araçlarla ek düzeltmeler..." -ForegroundColor White

    # Import düzelt (isort)
    isort main.py src/ tree_generator.py --profile black
    Write-Host "✅ Import'lar düzeltildi" -ForegroundColor Green

    # Black format (Ruff'a ek olarak)
    black main.py src/ tree_generator.py --line-length=119
    Write-Host "✅ Black format uygulandı" -ForegroundColor Green

    Write-Host "🎉 Tüm kod kalitesi sorunları düzeltildi!" -ForegroundColor Green
}

if ($All) {
    Write-Host "🚀 Tam kalite kontrolü başlatılıyor..." -ForegroundColor Cyan

    # Önce düzelt
    & $PSScriptRoot\quality-check.ps1 -Fix

    # Sonra kontrol et
    & $PSScriptRoot\quality-check.ps1 -Check

    # Testleri çalıştır
    Write-Host "🧪 Testler çalıştırılıyor..." -ForegroundColor White
    python -m pytest tests/ -v
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Tüm testler başarılı!" -ForegroundColor Green
    } else {
        Write-Host "❌ Bazı testler başarısız!" -ForegroundColor Red
    }

    Write-Host "🏆 Tam kalite kontrolü tamamlandı!" -ForegroundColor Green
}

# Parametresiz çalışırsa yardım göster
if (-not ($Check -or $Fix -or $All)) {
    Write-Host ""
    Write-Host "💡 Kullanım:" -ForegroundColor Yellow
    Write-Host "  .\quality-check.ps1 -Check    # Sadece kontrol et" -ForegroundColor White
    Write-Host "  .\quality-check.ps1 -Fix      # Sorunları düzelt" -ForegroundColor White
    Write-Host "  .\quality-check.ps1 -All      # Düzelt + kontrol + test" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 Hızlı kullanım: .\quality-check.ps1 -All" -ForegroundColor Cyan
}
