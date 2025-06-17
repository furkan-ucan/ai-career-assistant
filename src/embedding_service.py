"""
Embedding Servisi
Google Gemini API kullanarak metin embeddings'leri oluşturur.
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
from typing import List, Optional

# Environment variables yükle
load_dotenv()

class EmbeddingService:
    def __init__(self):
        """Gemini API'yi başlat"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("Gemini API key geçerli değil! .env dosyasını kontrol edin.")

        genai.configure(api_key=api_key)
        self.model = 'models/text-embedding-004'
        print("✅ Gemini API bağlantısı kuruldu")

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
                result = genai.embed_content(
                    model=self.model,
                    content=text,
                    task_type="retrieval_document"
                )
                return result['embedding']

            except Exception as e:
                print(f"⚠️ Embedding hatası (deneme {attempt + 1}/{retry_count}): {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"❌ Embedding oluşturulamadı: {text[:50]}...")
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

        print(f"🔄 {total} metin için embedding oluşturuluyor...")

        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []

            for text in batch:
                embedding = self.create_embedding(text)
                batch_embeddings.append(embedding)

                # Rate limiting için kısa bekleme
                time.sleep(0.1)

            embeddings.extend(batch_embeddings)
            print(f"📊 İlerleme: {min(i + batch_size, total)}/{total}")

        successful_count = sum(1 for e in embeddings if e is not None)
        print(f"✅ {successful_count}/{total} embedding başarıyla oluşturuldu")

        return embeddings

if __name__ == "__main__":
    # Test çalıştırması
    service = EmbeddingService()
    test_embedding = service.create_embedding("Bu bir test metnidir.")
    print(f"Test embedding boyutu: {len(test_embedding) if test_embedding else 'Başarısız'}")
