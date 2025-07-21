# ==========================================================
# UCAN-DOS v2.1 CUSTOM SANDBOX BLUEPRINT
# Mimar: Furkan Uçan
# Amaç: Standart Gemini sandbox'ına Node.js yeteneği kazandırmak.
# ==========================================================

# Adım 1: Google'ın resmi ve güvenli imajını temel alarak başla.
# Mimaride asla tekerleği yeniden icat etmeyiz; devlerin omuzlarında yükseliriz.
FROM us-docker.pkg.dev/gemini-code-dev/gemini-cli/sandbox:0.1.11

# Adım 2: Kurulum yapmak için geçici olarak yönetici (root) yetkilerine geç.
# Bu, inşaat alanına girerken baret takmak gibidir. Gerekli ve geçici.
USER root

# Adım 3: Node.js ve NPM'i kur.
# 'apt-get update' -> Malzeme listesini güncelle.
# 'apt-get install -y ...' -> Gerekli malzemeleri (nodejs, npm) şantiyeye getir ve kur.
# '-y' bayrağı, tüm onay sorularına otomatik evet der.
RUN apt-get update && apt-get install -y \
    nodejs \
    npm

# Adım 4: Güvenliği yeniden sağla.
# İnşaat bitti. Baretimizi çıkarıp, normal kullanıcı yetkilerine geri dönüyoruz.
# Bu, "Minimum Ayrıcalık Prensibi"nin kusursuz bir uygulamasıdır.
USER gemini
