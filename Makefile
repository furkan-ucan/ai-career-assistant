.PHONY: help install install-dev format lint test run clean setup-env

# Yardım
help:
	@echo "Akıllı Kariyer Asistanı - Geliştirme Komutları"
	@echo "=============================================="
	@echo "setup-env     : Python sanal ortamını oluştur ve bağımlılıkları yükle"
	@echo "install       : Sadece ana bağımlılıkları yükle"
	@echo "install-dev   : Geliştirme bağımlılıklarını da yükle"
	@echo "format        : Kodu Black ile formatla"
	@echo "lint          : Flake8 ile kod kalitesi kontrolü"
	@echo "test          : Testleri çalıştır"
	@echo "run           : Ana uygulamayı çalıştır"
	@echo "clean         : Geçici dosyaları temizle"

# Sanal ortam kurulumu
setup-env:
	python -m venv kariyer-asistani-env
	.\kariyer-asistani-env\Scripts\activate && pip install --upgrade pip
	.\kariyer-asistani-env\Scripts\activate && pip install -e .[dev]
	@echo "Sanal ortam hazır! Aktifleştirmek için: .\kariyer-asistani-env\Scripts\activate"

# Bağımlılık kurulumları
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install black flake8 pytest pytest-cov isort

# Kod formatları
format:
	isort main.py src/ --profile black
	black main.py src/ --line-length=120
	@echo "✅ Kod formatlaması tamamlandı"

lint:
	isort main.py src/ --profile black --check-only
	black main.py src/ --line-length=120 --check
	flake8 main.py src/ --max-line-length=120 --ignore=E203,W503
	@echo "✅ Kod kalitesi kontrolü tamamlandı"

# Test çalıştırma
test:
	python -m pytest tests/ -v --cov=src
	@echo "✅ Testler tamamlandı"

# Ana uygulama
run:
	python main.py

# Temizlik
clean:
	find . -type f -name "*.pyc" -delete 2>nul || true
	find . -type d -name "__pycache__" -delete 2>nul || true
	find . -type d -name "*.egg-info" -delete 2>nul || true
	if exist build rmdir /s /q build
	if exist dist rmdir /s /q dist
	@echo "✅ Geçici dosyalar temizlendi"

# Hızlı geliştirme döngüsü
dev-check: format lint
	@echo "✅ Geliştirme kontrolleri tamamlandı"
