"""
Vektör Depolama Modülü - Temizlenmiş Versiyon
ChromaDB kullanarak iş ilanı vektörlerini saklar ve arama yapar.
"""

# Standard Library
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third Party
import chromadb
import pandas as pd
import yaml

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, persist_directory: str = None, collection_name: str = None):
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
            if collection_name is None:
                try:
                    with open("config.yaml", "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f)
                    collection_name = cfg.get("vector_store_settings", {}).get("collection_name")
                except Exception as cfg_err:
                    logger.warning(f"Config load failed: {cfg_err}; using default collection name")
            self.collection_name = collection_name or "job_embeddings"
            self.collection = None
            logger.info("VectorStore başarıyla başlatıldı")

        except Exception as e:
            logger.error(f"❌ VectorStore başlatma hatası: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _stable_job_id(job_dict: Dict[str, Any]) -> str:
        """Create a deterministic job ID using URL if available."""
        url = job_dict.get("url") or job_dict.get("job_url")
        if url:
            digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        else:
            canonical = json.dumps(job_dict, sort_keys=True, ensure_ascii=False)
            digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
        return f"job_{digest}"

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

    def job_exists(self, job_dict: Dict[str, Any]) -> bool:
        """Check whether a job with the given ID already exists."""
        if not self.get_collection():
            return False

        job_id = self._stable_job_id(job_dict)
        try:
            existing = self.collection.get(ids=[job_id])
            return len(existing.get("ids", [])) > 0
        except Exception:
            return False

    def add_jobs(self, jobs_df: pd.DataFrame, embeddings: List[Optional[List[float]]]) -> bool:
        """İş ilanlarını ve embeddings'lerini koleksiyona ekle - Tekrar eklemeyi önler"""
        if not self.get_collection():
            return False

        try:
            valid_jobs = []
            valid_embeddings = []
            valid_ids = []

            # Geçerli veri ve embedding'leri filtrele
            for i, (_, job_row) in enumerate(jobs_df.iterrows()):
                if i < len(embeddings) and embeddings[i] is not None:
                    job_dict = job_row.to_dict()
                    if self.job_exists(job_dict):
                        continue

                    job_id = self._stable_job_id(job_dict)
                    valid_jobs.append(job_dict)
                    valid_embeddings.append(embeddings[i])
                    valid_ids.append(job_id)

            if not valid_jobs:
                logger.info("ℹ️ Eklenecek yeni iş ilanı bulunamadı (tümü zaten mevcut)")
                return True

            # Batch olarak ekle
            self.collection.add(
                embeddings=valid_embeddings,
                documents=[f"{job.get('title', '')} {job.get('description', '')}" for job in valid_jobs],
                metadatas=valid_jobs,
                ids=valid_ids,
            )

            logger.info(f"✅ {len(valid_jobs)} yeni iş ilanı başarıyla eklendi")
            return True

        except Exception as e:
            logger.error(f"❌ İş ilanları ekleme hatası: {str(e)}", exc_info=True)
            return False

    def search_jobs(
        self, query_embedding: List[float], n_results: int = 10, filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List]:
        """Vektör benzerliği ile iş ilanı ara"""
        if not self.get_collection():
            return {"matches": [], "distances": [], "metadatas": []}

        try:
            where_clause = filter_metadata if filter_metadata else {}

            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=n_results, where=where_clause if where_clause else None
            )

            if results and results.get("metadatas") and len(results["metadatas"]) > 0:
                logger.info(f"🔍 {len(results['metadatas'][0])} iş ilanı bulundu")
                return {
                    "matches": results["documents"][0] if results.get("documents") else [],
                    "distances": results["distances"][0] if results.get("distances") else [],
                    "metadatas": results["metadatas"][0] if results.get("metadatas") else [],
                }
            else:
                logger.info("ℹ️ Arama kriterlerine uygun iş ilanı bulunamadı")
                return {"matches": [], "distances": [], "metadatas": []}

        except Exception as e:
            logger.error(f"❌ Vektör arama hatası: {str(e)}", exc_info=True)
            return {"matches": [], "distances": [], "metadatas": []}

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
def create_vector_store(persist_directory: str = None, collection_name: str = None) -> Optional[VectorStore]:
    """VectorStore örneği oluştur"""
    try:
        return VectorStore(persist_directory=persist_directory, collection_name=collection_name)
    except Exception as e:
        logger.error(f"VectorStore oluşturma hatası: {str(e)}")
        return None
