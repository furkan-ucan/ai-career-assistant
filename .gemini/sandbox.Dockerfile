# ==========================================================
# UCAN-DOS v2.2 için Özel Güvenlik Kasası Mimarisi
# Mimar: Dr. Alistair Finch
# Amaç: Standart sandbox'a Node.js yeteneği eklemek.
# ==========================================================

# Adım 1: Google'ın standart, yüksek güvenlikli kasasını temel al.
FROM us-docker.pkg.dev/gemini-code-dev/gemini-cli/sandbox:0.1.13

# Adım 2: Gerekli araçları kurmak için yönetici (root) yetkilerini al.
USER root

# Adım 3: Temel araçları yükle.
RUN apt-get update && apt-get install -y curl bash

# Adım 4: Node Version Manager (nvm) kur.
# ---> İYİLEŞTİRME: ENV formatı güncellendi.
ENV NVM_DIR="/usr/local/nvm"
ENV NODE_VERSION="20.11.1"
RUN mkdir -p ${NVM_DIR} && \
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Adım 5: nvm'i kullanarak Node.js'i kur ve varsayılan olarak ayarla.
# ---> HATA DÜZELTMESİ: nvm'in çalışmasını engelleyen NPM_CONFIG_PREFIX değişkenini kaldır.
# ---> İYİLEŞTİRME: Her RUN komutu kendi kabuğunda (shell) çalıştığı için,
# nvm'i etkinleştirmek ve kullanmak aynı RUN komutu içinde yapılmalı.
# Komutları birleştirmek için `bash -c "..."` yapısını kullanmak daha sağlam bir yöntemdir.
SHELL ["/bin/bash", "-c"]
RUN unset NPM_CONFIG_PREFIX && \
    . "${NVM_DIR}/nvm.sh" && \
    nvm install "${NODE_VERSION}" && \
    nvm alias default "${NODE_VERSION}" && \
    nvm use default

# Adım 6: PATH'i güncelle.
# ---> İYİLEŞTİRME: ENV formatı güncellendi ve PATH daha doğru bir şekilde ayarlandı.
ENV PATH="${NVM_DIR}/versions/node/v${NODE_VERSION}/bin:${PATH}"

# Adım 7: Güvenlik için, kısıtlı 'gemini' kullanıcısına geri dön.
USER gemini
