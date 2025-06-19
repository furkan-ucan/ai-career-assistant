"""
Embedding Servisi
Google Gemini API kullanarak metin embeddings'leri oluşturur.
Metin kısaltma ve gelişmiş rate-limit yönetimi ile optimize edilmiş.
"""

# Standard Library
import logging
import os
import time
from typing import List, Optional

# Third Party
import google.generativeai as genai
import numpy as np
from dotenv import load_dotenv
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

# Environment variables yükle
load_dotenv()

logger = logging.getLogger(__name__)

# Konfigürasyon sabitleri
MAX_TEXT_LENGTH = 15000  # Gemini API için güvenli karakter limiti
DEFAULT_DELAY_BETWEEN_REQUESTS = 2.0  # Saniye cinsinden varsayılan bekleme süresi


class EmbeddingService:
    def __init__(self, delay_between_requests: float = DEFAULT_DELAY_BETWEEN_REQUESTS):
        """
        Gemini API'yi başlat

        Args:
            delay_between_requests: API istekleri arasındaki bekleme süresi (saniye)
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("Gemini API key geçerli değil! .env dosyasını kontrol edin.")

        genai.configure(api_key=api_key)
        self.model = "models/text-embedding-004"
        self.delay_between_requests = delay_between_requests

        logger.info("✅ Gemini API bağlantısı kuruldu")
        logger.info(f"📋 Metin limiti: {MAX_TEXT_LENGTH} karakter")
        logger.info(f"⏱️ İstekler arası bekleme: {delay_between_requests} saniye")

    def _truncate_text_if_needed(self, text: str) -> str:
        """
        Metni gerekirse güvenli limit içinde kısalt

        Args:
            text: Kontrol edilecek metin

        Returns:
            Kısaltılmış veya orijinal metin
        """
        if len(text) > MAX_TEXT_LENGTH:
            original_len = len(text)
            truncated_text = text[:MAX_TEXT_LENGTH]
            logger.warning(
                f"📏 Metin {MAX_TEXT_LENGTH} karaktere kısaltıldı. "
                f"Orijinal: {original_len} → Kısaltılmış: {len(truncated_text)}"
            )
            return truncated_text
        return text

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        before_sleep=lambda retry_state: logger.info(
            f"🔄 Rate limit/hata nedeniyle {retry_state.attempt_number}. deneme için bekleniyor..."
        ),
    )
    def _perform_embedding_request(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Tenacity ile korumalı API çağrısı

        Args:
            text: Embedding oluşturulacak metin (önceden kısaltılmış olmalı)
            task_type: Gemini API task tipi

        Returns:
            Embedding vektörü

        Raises:
            Exception: API çağrısı başarısız olursa
        """
        # Her API çağrısından önce genel bekleme (rate limit koruması)
        time.sleep(self.delay_between_requests)

        result = genai.embed_content(model=self.model, content=text, task_type=task_type)

        return result["embedding"]

    def create_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> Optional[List[float]]:
        """
        Tek bir metin için embedding oluştur (metin kısaltma ve tenacity koruması ile)

        Args:
            text: Embedding oluşturulacak metin
            task_type: Gemini API task tipi

        Returns:
            Embedding vektörü veya None (hata durumunda)
        """
        # 1. Metin kısaltma kontrolü
        text_to_embed = self._truncate_text_if_needed(text)

        # 2. Tenacity korumalı API çağrısı
        try:
            embedding = self._perform_embedding_request(text_to_embed, task_type)
            return embedding

        except RetryError as e:
            logger.error(
                f"❌ Embedding {e.last_attempt.attempt_number} deneme sonunda oluşturulamadı: "
                f"{text_to_embed[:50]}... Hata: {e.last_attempt.exception()}"
            )
            return None
        except Exception as e:
            logger.error(f"❌ Beklenmeyen embedding hatası: {e}")
            return None

    def create_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[Optional[List[float]]]:
        """
        Birden fazla metin için batch embedding oluştur

        Args:
            texts: Embedding oluşturulacak metinler
            batch_size: Batch boyutu

        Returns:
            Embedding vektörlerinin listesi
        """
        embeddings = []
        total = len(texts)

        logger.info(f"🔄 {total} metin için embedding oluşturuluyor...")

        for i in range(0, total, batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = []

            for text in batch:
                embedding = self.create_embedding(text)
                batch_embeddings.append(embedding)

                # Rate limiting için kısa bekleme
                time.sleep(0.1)

            embeddings.extend(batch_embeddings)
            logger.info(f"📊 İlerleme: {min(i + batch_size, total)}/{total}")

        successful_count = sum(1 for e in embeddings if e is not None)
        logger.info(f"✅ {successful_count}/{total} embedding başarıyla oluşturuldu")

        return embeddings

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        İki metin arasındaki anlamsal benzerliği hesaplar (cosine similarity)

        Args:
            text1: İlk metin
            text2: İkinci metin

        Returns:
            Benzerlik puanı (0-100 arası)
        """
        logger.info("🔄 Embedding'ler oluşturuluyor...")

        # Her iki metin için embedding oluştur
        embedding1 = self.create_embedding(text1)
        embedding2 = self.create_embedding(text2)

        if embedding1 is None or embedding2 is None:
            logger.error("❌ Embedding oluşturulamadı!")
            return 0.0

        # NumPy array'lere çevir
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity hesapla
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        cosine_sim = dot_product / (norm1 * norm2)

        # 0-100 arasına ölçekle
        similarity_percentage = (cosine_sim + 1) / 2 * 100

        logger.info(f"✅ Cosine similarity: {cosine_sim:.4f}")
        logger.info(f"✅ Benzerlik puanı: {similarity_percentage:.2f}%")

        return similarity_percentage


if __name__ == "__main__":
    # Test çalıştırması
    service = EmbeddingService()
    test_embedding = service.create_embedding("Bu bir test metnidir.")
    logger.info(f"Test embedding boyutu: {len(test_embedding) if test_embedding else 'Başarısız'}")
