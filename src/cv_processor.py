"""
CV İşleme Modülü
Kullanıcının CV'sini okur ve embedding oluşturur.
"""

# Standard Library
import logging
from pathlib import Path
from typing import List, Optional

from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class CVProcessor:
    def __init__(self, cv_path: Optional[str] = None, embedding_settings: Optional[dict] = None):
        """CV işleyici başlat"""
        if embedding_settings:
            self.embedding_service = EmbeddingService(**embedding_settings)
        else:
            self.embedding_service = EmbeddingService()
        self.cv_path = Path(cv_path) if cv_path else Path("data") / "cv.txt"
        self.cv_text: Optional[str] = None
        self.cv_embedding: Optional[List[float]] = None

    def load_cv(self) -> bool:
        """CV dosyasını yükle"""
        try:
            if not self.cv_path.exists():
                logger.error(f"❌ CV dosyası bulunamadı: {self.cv_path}")
                return False

            with open(self.cv_path, encoding="utf-8") as file:
                self.cv_text = file.read().strip()

            if not self.cv_text:
                logger.error(f"❌ CV dosyası boş: {self.cv_path}")
                return False

            logger.info(f"✅ CV yüklendi ({len(self.cv_text)} karakter)")
            return True

        except FileNotFoundError:
            logger.error(f"❌ CV dosyası bulunamadı: {self.cv_path}")
            return False
        except OSError as e:
            logger.error(f"❌ CV dosyası okuma hatası: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"❌ CV yükleme hatası: {str(e)}", exc_info=True)
            return False

    def create_cv_embedding(self) -> bool:
        """CV için embedding oluştur"""
        if not self.cv_text and not self.load_cv():
            return False

        # None kontrolü ekle
        if self.cv_text is None:
            logger.error("❌ CV metni None - embedding oluşturulamaz")
            return False

        logger.info("🔄 CV embedding'i oluşturuluyor...")
        self.cv_embedding = self.embedding_service.create_embedding(self.cv_text)

        if self.cv_embedding:
            logger.info(f"✅ CV embedding oluşturuldu (boyut: {len(self.cv_embedding)})")
            return True
        else:
            logger.error("❌ CV embedding oluşturulamadı")
            return False

    def get_cv_embedding(self) -> Optional[List[float]]:
        """CV embedding'ini döndür"""
        if not self.cv_embedding and not self.create_cv_embedding():
            return None

        return self.cv_embedding

    def get_cv_text(self) -> Optional[str]:
        """CV metnini döndür"""
        if not self.cv_text and not self.load_cv():
            return None

        return self.cv_text

    def get_cv_summary(self) -> dict:
        """CV özeti döndür"""
        if not self.cv_text:
            self.load_cv()

        return {
            "character_count": len(self.cv_text) if self.cv_text else 0,
            "word_count": len(self.cv_text.split()) if self.cv_text else 0,
            "has_embedding": self.cv_embedding is not None,
            "embedding_dimensions": len(self.cv_embedding) if self.cv_embedding else 0,
        }


if __name__ == "__main__":  # Test çalıştırması
    processor = CVProcessor()
    if processor.load_cv():
        logger.info("CV özeti:" + str(processor.get_cv_summary()))
        if processor.create_cv_embedding():
            logger.info("CV embedding başarıyla oluşturuldu!")
