# AGENTS.md – Akıllı Kariyer Asistanı Kuralları

## 1. Proje Özeti
Python tabanlı CLI: CV → embed → ilan toplama (`JobSpy` ile LinkedIn/Indeed) → ChromaDB (`cosine`) → Gemini AI ile puanlama → filtrelenmiş iş listesi.
Yapılandırma: `config.yaml`. API Anahtarı: `.env` (`GEMINI_API_KEY`).

## 2. Temel Komutlar
- **Uygulamayı Çalıştır:** `python main.py` (Sanal ortam (`kariyer-asistani-env`) aktif olmalı)
- **Bağımlılıkları Yükle:** `pip install -r requirements.txt`
- **Kod Kalitesi (Format + Lint + Test):** `make quality-check` (veya Windows için `.\dev-tools.ps1 -Action Test-CodeQuality`)
- **Sadece Testleri Çalıştır:** `pytest -q tests/`

## 3. Kod Standartları ve En İyi Pratikler
- **Formatlama:** `black .` (Yapılandırma `pyproject.toml` içinde)
- **Import Sıralama:** `isort .` (Yapılandırma `pyproject.toml` içinde)
- **Linting:** `flake8 .` (Yapılandırma `.flake8` içinde)
- **Loglama:** Python `logging` modülü kullanılacak (varsayılan seviye: INFO). `print()` kullanmaktan kaçın.
- **Dosya Yolları:** `pathlib.Path` kullan.
- **Yapılandırma:** Tüm ayarlar `config.yaml`'dan, hassas bilgiler `.env`'den okunur.
- **Hata Yönetimi:** Spesifik exception'lar yakalanmalı, `tenacity` ile API retry.

## 4. Önemli Klasörler ve Dosyalar
| Klasör/Dosya        | Açıklama                                      |
| ------------------- | --------------------------------------------- |
| `main.py`           | Ana uygulama giriş noktası                     |
| `config.yaml`       | Tüm proje ve puanlama ayarları                |
| `src/`              | Tüm Python modülleri (business logic)         |
| `src/intelligent_scoring.py` | Anahtar puanlama mantığı                  |
| `data/cv.txt`       | Kullanıcı CV metni (config'den yolu override edilebilir) |
| `data/chromadb/`    | Vektör veritabanı (Git'e ekleme!)             |
| `tests/`            | Pytest birim testleri                         |

## 5. Kesinlikle Yasaklı Eylemler
- **Commit ETME:** `.env` dosyası, `data/chromadb/` klasörü, `*.pyc` dosyaları, `__pycache__/` klasörü.
- **Komutlar (Sandbox Dışı):** `git reset --hard`, `rm -rf` (özellikle proje dışı yollarda).
- **ChromaDB:** `VectorStore.create_collection()` içindeki koleksiyon silme mantığı sadece debug/test amaçlıdır; üretimde `get_or_create_collection` kullanılmalı.

## 6. Puanlama Sistemi İpuçları (Scoring Hints)
- Ağırlıklı puanlama `config.yaml`'daki `scoring_system` bölümünden yönetilir.
- **Bileşenler:** Başlık (`title_weights`), Açıklama (`description_weights`), Deneyim Yılı (`experience_penalties`).
- **CV Beceri Bonusu:** Eğer bir ilanın AI tarafından hesaplanan ham kosinüs benzerlik skoru `cv_skill_boost_threshold`'un üzerindeyse, toplam skora `cv_skill_bonus_points` eklenir. (Bu özellik `calculate_total_score` içinde kontrol edilir).
- Regex pattern'leri `_create_regex_pattern` ile kelime sınırı (`\b`) gözetilerek ve case-insensitive olarak oluşturulur.

## 7. Dil ve Yorumlar
- Kod içi yorumlar ve log mesajları **Türkçe** olabilir.
- Değişken, fonksiyon, sınıf ve dosya isimleri **İngilizce** olmalıdır (PEP 8).
