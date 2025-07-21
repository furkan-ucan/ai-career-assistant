# src/embedding_service.py
"""
Embedding Servisi
Google Gemini API kullanarak metin embeddings'leri oluşturur.
"""

# Standard Library
import logging
import time

# Third Party
import google.generativeai as genai
import numpy as np

from .config import get_config

# Environment variables yükle
logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, batch_size: int = 10, retry_count: int = 3, rate_limit_delay: float = 0.1):
        """Gemini API'yi başlat ve konfigürasyon ayarlarını sakla"""
        config = get_config()
        api_key = config.get("GEMINI_API_KEY") if config else None
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("Gemini API key geçerli değil! .env dosyasını kontrol edin.")
        genai.configure(api_key=api_key)
        self.model = "models/text-embedding-004"
        self.batch_size = batch_size
        self.retry_count = retry_count
        self.rate_limit_delay = rate_limit_delay
        logger.info("✅ Gemini API bağlantısı kuruldu")

    def create_embedding(self, text: str, retry_count: int | None = None, max_chars: int = 8000) -> list[float] | None:
        """
        Tek bir metin için embedding oluştur - Token limit kontrolü ile
        Args:
            text: Embedding oluşturulacak metin
            retry_count: Hata durumunda deneme sayısı (None ise varsayılan kullanılır)
                max_chars: Maksimum karakter sayısı
                (Gemini token limiti için, ~8000 char ≈ 2000 token)
        Returns:
            Embedding vektörü veya None
        """
        if not text:
            return None
        # Token limit için güvenli kısaltma (Gemini text-embedding-004 için optimize)
        original_length = len(text)
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.debug(f"Metin {original_length} karakterden {max_chars} karaktere kısaltıldı")
        retry_count = retry_count if retry_count is not None else self.retry_count
        for attempt in range(retry_count):
            try:
                result = genai.embed_content(model=self.model, content=text, task_type="retrieval_document")
                return result["embedding"]  # type: ignore
            except Exception as e:
                logger.warning(f"⚠️ Embedding hatası (deneme {attempt + 1}/{retry_count}): {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    logger.error(f"❌ Embedding oluşturulamadı: {text[:50]}...")
        return None

    def create_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int | None = None,
        retry_count: int | None = None,
        rate_limit_delay: float | None = None,
        max_chars: int = 8000,
    ) -> list[list[float] | None]:
        """
        Birden fazla metin için batch embedding oluştur - Token limit kontrolü ile
        Args:
            texts: Embedding oluşturulacak metinler
            batch_size: Batch boyutu (None ise varsayılan kullanılır)
            retry_count: Hata durumunda deneme sayısı
            rate_limit_delay: Her istek sonrası bekleme süresi
            max_chars: Maksimum karakter sayısı (her metin için)
        Returns:
            Embedding vektörlerinin listesi
        """
        batch_size = batch_size if batch_size is not None else self.batch_size
        retry_count = retry_count if retry_count is not None else self.retry_count
        delay = rate_limit_delay if rate_limit_delay is not None else self.rate_limit_delay
        embeddings = []
        total = len(texts)
        logger.info(f"🔄 {total} metin için embedding oluşturuluyor...")
        for i in range(0, total, batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = []
            for text in batch:
                embedding = self.create_embedding(text, retry_count=retry_count, max_chars=max_chars)
                batch_embeddings.append(embedding)
                # Rate limiting için kısa bekleme
                time.sleep(delay)
            embeddings.extend(batch_embeddings)
            logger.info(f"📊 İlerleme: {min(i + batch_size, total)}/{total}")
        successful_count = sum(1 for e in embeddings if e is not None)
        logger.info(f"✅ {successful_count}/{total} embedding başarıyla oluşturuldu")
        return embeddings

    def calculate_similarity(self, text1: str, text2: str, max_chars: int = 8000) -> float:
        """
        İki metin arasındaki anlamsal benzerliği hesaplar (cosine similarity)
        Args:
            text1: İlk metin
            text2: İkinci metin
            max_chars: Maksimum karakter sayısı (her metin için)
        Returns:
            Benzerlik puanı (0-100 arası)
        """
        logger.info("🔄 Embedding'ler oluşturuluyor...")
        # Her iki metin için embedding oluştur
        embedding1 = self.create_embedding(text1, max_chars=max_chars)
        embedding2 = self.create_embedding(text2, max_chars=max_chars)
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
        return float(similarity_percentage)


if __name__ == "__main__":
    # Test çalıştırması
    service = EmbeddingService()
    test_embedding = service.create_embedding("Bu bir test metnidir.")
    logger.info(f"Test embedding boyutu: {len(test_embedding) if test_embedding else 'Başarısız'}")
