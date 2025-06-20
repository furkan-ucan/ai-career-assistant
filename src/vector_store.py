"""
Vektör Depolama Modülü - Temizlenmiş Versiyon
ChromaDB kullanarak iş ilanı vektörlerini saklar ve arama yapar.
"""

# Standard Library
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third Party
import chromadb
import pandas as pd

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, persist_directory: str = None):
        """ChromaDB istemcisini başlat"""
        try:
            if persist_directory:
                persist_path = Path(persist_directory)
                persist_path.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(path=str(persist_path))
                logger.info(f"✅ ChromaDB kalıcı client başlatıldı: {persist_path}")
            else:
                self.client = chromadb.Client()
                logger.info("✅ ChromaDB geçici client başlatıldı")

            self.collection_name = "job_listings"
            self.collection = None
            logger.info("VectorStore başarıyla başlatıldı")

        except Exception as e:
            logger.error(f"❌ VectorStore başlatma hatası: {str(e)}", exc_info=True)
            raise

    def create_collection(self) -> bool:
        """Koleksiyon oluştur veya mevcut olanı getir"""
        try:
            # get_or_create_collection kullanarak hem yeni oluşturma hem de mevcut getirme
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}  # Cosine similarity kullan
            )

            # Mevcut öğe sayısını kontrol et
            existing_count = self.collection.count()
            if existing_count > 0:
                logger.info(f"✅ Mevcut koleksiyon yüklendi ({existing_count} öğe)")
            else:
                logger.info("✅ Yeni koleksiyon oluşturuldu")

            return True
        except Exception as e:
            logger.error(f"❌ Koleksiyon oluşturma/yükleme hatası: {str(e)}", exc_info=True)
            return False

    def get_collection(self):
        """Mevcut koleksiyonu getir"""
        if not self.collection:
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info("✅ Mevcut koleksiyon yüklendi")
            except Exception as e:
                logger.info("⚠️ Koleksiyon bulunamadı, yeni oluşturuluyor...")
                logger.debug(f"Hata detayı: {e}")
                self.create_collection()

        return self.collection

    def add_jobs(self, jobs_df: pd.DataFrame, embeddings: List[Optional[List[float]]]) -> bool:
        """İş ilanlarını ve embeddings'lerini koleksiyona ekle - Tekrar eklemeyi önler"""
        if not self.get_collection():
            return False

        if self.collection is None:
            logger.error("❌ Koleksiyon başlatılmamış. Önce `create_collection` çağırılmalı.")
            return False

        # Eklenecek geçerli işleri, embedding'leri ve ID'leri topla
        valid_embeddings = []
        documents = []
        metadatas = []
        ids = []
        seen_ids = set()  # Bu işlemdeki ID'lerin tekrarını önlemek için

        for index, job in jobs_df.iterrows():
            # Sadece geçerli embedding'i olan işleri ekle
            if embeddings[index] is not None:
                # ID oluşturmadan önce alanları normalleştir (küçük harf, boşlukları temizle)
                title_norm = str(job.get("title", "")).lower().strip()
                company_norm = str(job.get("company", "")).lower().strip()
                location_norm = str(job.get("location", "")).lower().strip()

                # Benzersiz ve tutarlı bir ID oluştur (normalleştirilmiş içeriğe dayalı)
                job_id_str = f"{title_norm}-{company_norm}-{location_norm}"
                job_id = hashlib.md5(job_id_str.encode("utf-8")).hexdigest()

                # Bu ID'yi bu pakette daha önce görmediğimizden emin ol
                if job_id not in seen_ids:
                    seen_ids.add(job_id)  # Görüldü olarak işaretle

                    # Metadatayı hazırla (sadece serileştirilebilir tipler)
                    metadata = {
                        "title": str(job.get("title", "N/A")),
                        "company": str(job.get("company", "N/A")),
                        "location": str(job.get("location", "N/A")),
                        "description": str(job.get("description", ""))[:500],  # İlk 500 karakter
                        "job_url": str(job.get("job_url", job.get("url", "N/A"))),
                        "source_site": str(job.get("source", "N/A")),
                        "persona_source": str(job.get("persona_source", "N/A")),
                    }  # Sadece string, int, float veya bool olanları al
                    metadata = {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}

                    metadatas.append(metadata)
                    valid_embeddings.append(embeddings[index])
                    documents.append(f"{job.get('title', '')} at {job.get('company', '')}")
                    ids.append(job_id)
                else:
                    logger.warning(f"⚠️ Yinelenen ID ({job_id}) atlanıyor. İlan: '{title_norm}'")

        if not ids:
            logger.info("ℹ️ Vector store'a eklenecek yeni iş ilanı bulunamadı.")
            return True

        try:
            # ChromaDB'ye toplu ekleme (upsert mantığıyla çalışır)
            self.collection.upsert(embeddings=valid_embeddings, documents=documents, metadatas=metadatas, ids=ids)
            logger.info(f"✅ {len(ids)} adet iş ilanı vector store'a başarıyla eklendi/güncellendi.")
            return True
        except Exception as e:
            logger.error(f"❌ Vector store'a ekleme sırasında hata: {e}", exc_info=True)
            return False

    def search_jobs(self, query_embedding: list, n_results: int = 50) -> dict:
        """
        Verilen bir embedding'e en benzer işleri vector store'dan arar.
        """
        if self.collection is None:
            logger.error("❌ Koleksiyon başlatılmamış.")
            return {}
        if not query_embedding:
            logger.error("❌ Sorgu embedding'i boş olamaz.")
            return {}

        try:
            search_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )
            logger.info(f"✅ Vector store'da {len(search_results.get('ids', [[]])[0])} sonuç bulundu.")
            return search_results
        except Exception as e:
            logger.error(f"❌ Vector store'da arama hatası: {e}", exc_info=True)
            return {}

    def get_stats(self) -> Dict[str, Any]:
        """Koleksiyon istatistiklerini getir"""
        if not self.get_collection():
            return {"total_jobs": 0, "error": "Koleksiyon erişim hatası"}

        try:
            total_count = self.collection.count()
            return {
                "total_jobs": total_count,
                "collection_name": self.collection_name,
                "last_updated": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"❌ İstatistik alma hatası: {str(e)}", exc_info=True)
            return {"total_jobs": 0, "error": str(e)}

    def clear_collection(self) -> bool:
        """Koleksiyonu temizle (dikkatli kullan!)"""
        try:
            if self.collection:
                # Tüm öğeleri sil
                all_items = self.collection.get()
                if all_items.get("ids"):
                    self.collection.delete(ids=all_items["ids"])
                logger.info("🗑️ Koleksiyon başarıyla temizlendi")
                return True
            else:
                logger.warning("⚠️ Temizlenecek koleksiyon bulunamadı")
                return False
        except Exception as e:
            logger.error(f"❌ Koleksiyon temizleme hatası: {str(e)}", exc_info=True)
            return False


# Yardımcı fonksiyonlar
def create_vector_store(persist_directory: str = None) -> Optional[VectorStore]:
    """VectorStore örneği oluştur"""
    try:
        return VectorStore(persist_directory=persist_directory)
    except Exception as e:
        logger.error(f"VectorStore oluşturma hatası: {str(e)}")
        return None
