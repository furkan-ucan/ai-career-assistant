.PHONY: help install format lint test run clean check-quality fix-quality

# Yardım
help:
	@echo "Akıllı Kariyer Asistanı - Modern Geliştirme Komutları"
	@echo "==================================================="
	@echo "format         : Kodu Ruff ile formatla"
	@echo "lint           : Ruff ile kod kalitesi kontrolü"
	@echo "test           : Testleri çalıştır"
	@echo "run            : Ana uygulamayı çalıştır"
	@echo "clean          : Geçici dosyaları temizle"
	@echo "check-quality  : Kod kalitesi kontrol et"
	@echo "fix-quality    : Kod kalitesi sorunlarını düzelt"

# Kod formatları
format:
	ruff check main.py src/ tree_generator.py --fix
	ruff format main.py src/ tree_generator.py
	@echo "✅ Ruff kod formatlaması tamamlandı"

lint:
	ruff check main.py src/ tree_generator.py
	@echo "✅ Ruff kod kalitesi kontrolü tamamlandı"

# Kod kalitesi (Windows için PowerShell script kullan)
check-quality:
	@echo "🔍 Windows için: .\quality-check.ps1 -Check kullanın"

fix-quality:
	@echo "🔧 Windows için: .\quality-check.ps1 -Fix kullanın"

# Test çalıştırma
test:
	python -m pytest tests/ -v --cov=src
	@echo "✅ Testler tamamlandı"

# Ana uygulama
run:
	python main.py

# Temizlik (Windows uyumlu)
clean:
	@echo "🧹 Geçici dosyaları temizleniyor..."
	@for /r %%i in (*.pyc) do @del "%%i" 2>nul || echo.
	@for /d /r %%i in (__pycache__) do @rmdir /s /q "%%i" 2>nul || echo.
	@if exist build rmdir /s /q build 2>nul || echo.
	@if exist dist rmdir /s /q dist 2>nul || echo.
	@echo "✅ Geçici dosyalar temizlendi"
