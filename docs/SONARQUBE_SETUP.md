# 🔎 SonarQu## 🔧 2. Standalone Mode (Önerilen Başlangıç)

Eklenti varsayılan olarak **standalone mode** (yerel analiz) modunda çalışır ve **host URL/token gerektirmez**:

- ✅ **Avantajlar**: Hiçbir sunucu kurulumu gerektirmez, hemen çalışır
- ✅ **Özellikler**: Kapsamlı kod kalitesi, güvenlik sorunları, code smells, cognitive complexity
- ✅ **Yeterlilik**: Bireysel geliştirme için tamamen yeterli
- ⚠️ **Sınırlamalar**: Enterprise kuralları ve merkezi kalite kapıları eksik (çoğu proje için gerekli değil)

**💡 Önemli**: Bireysel geliştirme yapıyorsanız standalone mode yeterlidir. Host URL ve token girmenize gerek yoktur!IDE Kurulum Rehberi

Bu dosya, **SonarQube for IDE** (SonarLint) eklentisini VS Code'da nasıl tam kapasiteyle kullanacağınızı açıklar.

## 📥 1. VS Code Eklentisi Kurulumu

```bash
# Eklenti zaten extension listesinde mevcut
# VS Code Extensions panelinden "SonarQube for IDE" arayıp yükleyin
# ID: sonarsource.sonarlint-vscode
```

## 🔧 2. Yerel (Standalone) Kullanım

Eklenti varsayılan olarak **yerel analiz** modunda çalışır:

- ✅ **Avantajlar**: Kurulum gerektirmez, hemen çalışır
- ✅ **Özellikler**: Temel kod kalitesi, güvenlik sorunları, code smells
- ⚠️ **Sınırlamalar**: İleri düzey kurallar ve security hotspots eksik

### Standalone Mode İçin Ayarlar

VS Code `settings.json` dosyanıza eklenmiş (hiçbir ek konfigürasyon gerekmez):

```json
{
  "sonarlint.rules": {
    "python:S1481": "off", // Unused variables (Ruff handle eder)
    "python:S1066": "off", // Collapsible if statements (stil tercihi)
    "python:S1192": "warn" // String literal duplicates
  },
  "sonarlint.disableTelemetry": true
}
```

**🚀 Hemen Çalışır**: Eklenti kurulduktan sonra kod yazarken Problems panelinde anında SonarQube analizi görürsünüz!

## 🌐 3. Connected Mode (İleri Düzey - Opsiyonel)

**Connected Mode** yalnızca şu durumlarda gereklidir:

- Takım çalışması ile merkezi kalite kuralları
- Enterprise güvenlik kuralları
- Kalite kapıları (quality gates) gereksinimleri

| Kullanım Türü       | Host URL & Token Gerekli? | Kullanım Durumu                                       |
| ------------------- | ------------------------- | ----------------------------------------------------- |
| **Standalone Mode** | ❌ Hayır                  | Bireysel geliştirme, yerel kalite kontrolü            |
| **Connected Mode**  | ✅ Evet                   | Takım çalışması, merkezi kalite kuralları, enterprise |

### 3A. SonarCloud (Ücretsiz, Public Projeler)

**Sadece takım çalışması için gerekli:**

1. **SonarCloud'a kaydolun**: https://sonarcloud.io
2. **GitHub ile giriş yapın**
3. **Organization oluşturun**: `your-username` (otomatik)
4. **Proje ekleyin**: `akilli-kariyer-asistani`
5. **Token üretin**: Account > Security > Generate Token

### 3B. VS Code'da Bağlantı Kurma (Opsiyonel)

**Yalnızca Connected Mode istiyorsanız:**

```bash
# Command Palette (Ctrl+Shift+P)
> SonarLint: Add SonarQube Connection
```

**SonarCloud için:**

- Connection Type: SonarCloud
- Organization Key: `your-username`
- Token: `your_generated_token`

**SonarQube Server için:**

- Connection Type: SonarQube Server
- Server URL: `https://your-sonar-server.com`
- Token: `your_server_token`

### 3C. Proje Binding

```bash
# Command Palette
> SonarLint: Bind to SonarQube or SonarCloud project
```

- Connection: Az önce eklediğiniz connection
- Project Key: `akilli-kariyer-asistani`

## 📊 4. Raporlama ve Entegrasyon

### Coverage Raporu Üretimi

```powershell
# Windows PowerShell
.\quality-check.ps1 -All

# Manual pytest ile
python -m pytest --cov=src --cov=main --cov-report=xml --junitxml=test-results.xml
```

Bu komut şu dosyaları üretir:

- `coverage.xml` → Kod kapsama raporu
- `test-results.xml` → Test sonuçları

### SonarQube Proje Ayarları

`sonar-project.properties` dosyası hazır:

```properties
# Connected Mode için bu satırları uncomment edin:
# sonar.host.url=https://sonarcloud.io
# sonar.organization=your-organization-key
# sonar.login=your_token
```

## 🎯 5. Kullanım ve İpuçları

### VS Code'da Görüntüleme

- **Problems Panel** (Ctrl+Shift+M): Tüm sorunlar listesi
- **Editor**: Sorunlu satırlar altı çizili
- **File Explorer**: Sorunlu dosyalar işaretli
- **Status Bar**: Sorun sayısı gösterimi

### Yararlı Komutlar

```bash
# Command Palette'te şunları arayın:
> SonarLint: Show all locations
> SonarLint: Show SonarLint output
> SonarLint: Clear SonarLint issues cache
> SonarLint: Update all bindings
```

### Kural Yönetimi

```json
// .vscode/settings.json
{
  "sonarlint.rules": {
    "python:S1134": "off", // FIXME comments
    "python:S125": "warn", // Commented code
    "python:S2068": "error" // Hard-coded credentials
  }
}
```

## 🔄 6. CI/CD Entegrasyonu

GitHub Actions workflow hazır: `.github/workflows/quality.yml`

Secrets eklemeyi unutmayın:

- `SONAR_TOKEN`: SonarCloud/Server token'ı
- `SONAR_HOST_URL`: Server URL'si (SonarCloud için gereksiz)

## 🆘 7. Sorun Giderme

### Eklenti Çalışmıyor

```bash
# VS Code Command Palette
> Developer: Reload Window
> SonarLint: Show SonarLint output
```

### Connection Sorunları

```bash
# Token'ları kontrol edin
# Firewall/proxy ayarlarını gözden geçirin
# Organization key'i doğru mu?
```

### Performance Sorunları

```json
{
  "sonarlint.analyzeOpenFilesOnly": true,
  "sonarlint.excludedFiles": ["**/.git/**", "**/__pycache__/**", "**/logs/**"]
}
```

## 📚 8. Referanslar

- [SonarLint for VS Code Dokumentasyonu](https://docs.sonarcloud.io/advanced-setup/sonarlint-smart-notifications/)
- [SonarCloud Setup Rehberi](https://docs.sonarcloud.io/getting-started/github/)
- [Python Kuralları Listesi](https://rules.sonarsource.com/python/)

---

**💡 Önerilen Yaklaşım**:

1. **Başlangıç**: Standalone mode ile başlayın (host/token gerekmez)
2. **Değerlendirme**: Birkaç hafta kullanın, ihtiyaçlarınızı değerlendirin
3. **Yükseltme**: Takım çalışması gerekiyorsa Connected Mode'a geçin

**🎯 Çoğu Geliştirici İçin**: Standalone mode tamamen yeterlidir!
