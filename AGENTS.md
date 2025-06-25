# AGENTS.md — Akıllı Kariyer Asistanı · Codex Çalışma Kılavuzu

<!-- AgentsMD-Spec: v0.3  |  Docs: https://agentsmd.net/#what-is-agentsmd -->

## 1 • Görev Tanımı

OpenAI Codex, bu depoda **Python CLI** aracı geliştirir:
CV → `JobSpy` (LinkedIn / Indeed) → ChromaDB (cosine) → Gemini AI puanlama → filtrelenmiş ilan listesi.
Aşağıdaki dizinler dışında hiçbir dosya yaratma / silme:

| Bileşen    | Dizin                           | Açıklama                     |
| ---------- | ------------------------------- | ---------------------------- |
| Kaynak-kod | `src/`                          | Embedding, scraping, scoring |
| CLI giriş  | `main.py`                       | Uygulama başlangıcı          |
| Konfig     | `config.yaml`, `pyproject.toml` | Runtime + tooling            |
| Veri       | `data/`                         | CV, ChromaDB, CSV            |
| Test       | `tests/`                        | Pytest senaryoları           |
| Araç       | `quality-check.ps1`, `setup.sh` | Kod kalitesi, hızlı kurulum  |
| Belgeler   | `docs/`, `memory-bank/`         | Sistem mimarisi              |

## 2 • Çalıştırma Talimatları (Runbook)

```bash
# Ortam
bash setup.sh && source kariyer-asistani-env/bin/activate
# Tam kalite kontrolü
ruff check --fix . && ruff format . && mypy . && bandit -c pyproject.toml -r .
pytest -q
3 • Kodlama Standartları
Biçim + Lint + Import: ruff v0.4+

Satır uzunluğu: 119

Adlandırma: EN; yorum/log mesajı TR

Logging: logging (INFO) — print() yasak

Yollar: pathlib.Path

Tip kontrolü: mypy (uyarı yok)

Güvenlik: bandit (0 issue)

Do / Don’t
Yap	Yapma
logging.info() kullan	print() kullanma
ruff check --fix	black / isort / flake8 çalıştırma
get_or_create_collection	Chroma koleksiyonunu silme

4 • Fonksiyon Manifesti (Codex Function-Calling)
yaml
Kopyala
Düzenle
functions:
  run_tests:
    description: "Pytest senaryolarını çalıştır."
    parameters: {}
  format_code:
    description: "Ruff ile kodu biçimlendir."
    parameters: {}
5 • Pull-Request-Checklist
Açıklama net, ilgili issue etiketli

ruff, mypy, bandit, pytest yeşil

Yalnızca tek odaklı değişiklik

README / docs güncel

6 • Yasaklı Dosyalar
.env, data/chromadb/, *.pyc, __pycache__/, .ruff_cache/, logs/
```
