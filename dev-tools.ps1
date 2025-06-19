# PowerShell Scripts for Development - Windows Alternative to Makefile

# Kod formatlaması
function Format-Code {
    Write-Host "Kod formatlaması başlatılıyor..." -ForegroundColor Yellow
    isort main.py src/ --profile black
    black main.py src/ --line-length=120
    Write-Host "✅ Kod formatlaması tamamlandı" -ForegroundColor Green
}

# Kod kalitesi kontrolü
function Test-CodeQuality {
    Write-Host "Kod kalitesi kontrolü başlatılıyor..." -ForegroundColor Yellow
    
    Write-Host "📋 isort kontrolü..." -ForegroundColor Cyan
    $isortResult = isort main.py src/ --profile black --check-only
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ isort sorunları bulundu!" -ForegroundColor Red
        return $false
    }
    
    Write-Host "🎨 black kontrolü..." -ForegroundColor Cyan
    $blackResult = black main.py src/ --line-length=120 --check
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Black formatlaması gerekli!" -ForegroundColor Red
        return $false
    }
    
    Write-Host "🔍 flake8 kontrolü..." -ForegroundColor Cyan
    $flakeResult = flake8 main.py src/ --max-line-length=120 --ignore=E203,W503
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Flake8 sorunları bulundu!" -ForegroundColor Red
        return $false
    }
    
    Write-Host "✅ Kod kalitesi kontrolü tamamlandı - Tüm testler başarılı!" -ForegroundColor Green
    return $true
}

# Ana uygulamayı çalıştır
function Start-KariyerAsistani {
    Write-Host "🚀 Akıllı Kariyer Asistanı başlatılıyor..." -ForegroundColor Yellow
    python main.py
}

# Geliştirme bağımlılıklarını yükle
function Install-DevDependencies {
    Write-Host "Geliştirme bağımlılıkları yükleniyor..." -ForegroundColor Yellow
    pip install black flake8 pytest pytest-cov isort
    Write-Host "✅ Bağımlılıklar yüklendi" -ForegroundColor Green
}

# Hızlı geliştirme kontrolü
function Test-Development {
    Write-Host "🔄 Hızlı geliştirme kontrolü..." -ForegroundColor Yellow
    Format-Code
    $qualityResult = Test-CodeQuality
    if ($qualityResult) {
        Write-Host "🎉 Geliştirme kontrolü başarılı!" -ForegroundColor Green
    } else {
        Write-Host "❌ Geliştirme kontrolü başarısız!" -ForegroundColor Red
    }
}

# Yardım
function Show-Help {
    Write-Host ""
    Write-Host "Akıllı Kariyer Asistanı - Geliştirme Komutları" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Format-Code              : Kodu isort + black ile formatla" -ForegroundColor White
    Write-Host "Test-CodeQuality         : isort + black + flake8 kontrolü" -ForegroundColor White
    Write-Host "Start-KariyerAsistani    : Ana uygulamayı çalıştır" -ForegroundColor White
    Write-Host "Install-DevDependencies  : Geliştirme araçlarını yükle" -ForegroundColor White
    Write-Host "Test-Development         : Hızlı geliştirme kontrolü" -ForegroundColor White
    Write-Host "Show-Help                : Bu yardım mesajını göster" -ForegroundColor White
    Write-Host ""
    Write-Host "Kullanım:" -ForegroundColor Yellow
    Write-Host ". .\dev-tools.ps1        # Bu scripti yükle" -ForegroundColor Gray
    Write-Host "Format-Code              # Kodu formatla" -ForegroundColor Gray
    Write-Host "Test-CodeQuality         # Kalite kontrolü" -ForegroundColor Gray
    Write-Host ""
}

# Başlangıç mesajı
Write-Host "🔧 Kariyer Asistanı Geliştirme Araçları Yüklendi" -ForegroundColor Green
Write-Host "Yardım için: Show-Help" -ForegroundColor Yellow
