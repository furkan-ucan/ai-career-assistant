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

    # Import sıralaması kontrol
    Write-Host "📋 Import sıralaması kontrol ediliyor..." -ForegroundColor White
    isort main.py src/ tree_generator.py --profile black --check-only --diff
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Import sıralaması düzeltilmeli!" -ForegroundColor Red
    } else {
        Write-Host "✅ Import sıralaması OK" -ForegroundColor Green
    }

    # Format kontrol
    Write-Host "🎨 Format kontrol ediliyor..." -ForegroundColor White
    black main.py src/ tree_generator.py --line-length=88 --check --diff
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Format düzeltilmeli!" -ForegroundColor Red
    } else {
        Write-Host "✅ Format OK" -ForegroundColor Green
    }

    # Lint kontrol (cognitive complexity dahil)
    Write-Host "Lint kontrol ediliyor..." -ForegroundColor White
    $lintResult = flake8 main.py src/ tree_generator.py --show-source 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Lint hatalari var!" -ForegroundColor Red
        Write-Host $lintResult -ForegroundColor Yellow
    } else {
        Write-Host "Lint OK" -ForegroundColor Green
    }

    # MyPy tip kontrolu
    Write-Host "Tip kontrolu ediliyor..." -ForegroundColor White
    mypy main.py src/ --config-file=pyproject.toml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Tip hatalari var!" -ForegroundColor Red
    } else {
        Write-Host "Tip kontrol OK" -ForegroundColor Green
    }

    # MyPy tip kontrolü
    Write-Host "🔍 MyPy tip kontrolü..." -ForegroundColor White
    mypy main.py src/cv_processor.py src/data_collector.py src/embedding_service.py --config-file=pyproject.toml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ MyPy tip uyarıları var (kritik değil)" -ForegroundColor Yellow
    } else {
        Write-Host "✅ MyPy OK" -ForegroundColor Green
    }
}

if ($Fix) {
    Write-Host "🔧 Kod kalitesi sorunları düzeltiliyor..." -ForegroundColor Cyan

    # Import düzelt
    Write-Host "📋 Import'lar düzeltiliyor..." -ForegroundColor White
    isort main.py src/ tree_generator.py --profile black
    Write-Host "✅ Import'lar düzeltildi" -ForegroundColor Green

    # Format düzelt
    Write-Host "🎨 Format düzeltiliyor..." -ForegroundColor White
    black main.py src/ tree_generator.py --line-length=88
    Write-Host "✅ Format düzeltildi" -ForegroundColor Green

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
