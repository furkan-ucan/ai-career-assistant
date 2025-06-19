"""
Embedding Servisi
Google Gemini API kullanarak metin embeddings'leri oluşturur.
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

# Environment variables yükle
load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        """Gemini API'yi başlat"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("Gemini API key geçerli değil! .env dosyasını kontrol edin.")

        genai.configure(api_key=api_key)
        self.model = "models/text-embedding-004"
        logger.info("✅ Gemini API bağlantısı kuruldu")

    def create_embedding(self, text: str, retry_count: int = 3) -> Optional[List[float]]:
        """
        Tek bir metin için embedding oluştur

        Args:
            text: Embedding oluşturulacak metin
            retry_count: Hata durumunda deneme sayısı

        Returns:
            Embedding vektörü veya None
        """
        for attempt in range(retry_count):
            try:
                result = genai.embed_content(model=self.model, content=text, task_type="retrieval_document")
                return result["embedding"]

            except Exception as e:
                logger.warning(f"⚠️ Embedding hatası (deneme {attempt + 1}/{retry_count}): {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    logger.error(f"❌ Embedding oluşturulamadı: {text[:50]}...")
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
