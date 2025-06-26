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
from typing import Any

# Third Party
import chromadb
import pandas as pd
import yaml

from .constants import COSINE_METRIC, DEFAULT_COLLECTION_NAME

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str | None = None,
    ):
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
                    with open("config.yaml", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f)
                    collection_name = cfg.get("vector_store_settings", {}).get("collection_name")
                except Exception as cfg_err:
                    logger.warning(f"Config load failed: {cfg_err}; using default collection name")
            self.collection_name = collection_name or DEFAULT_COLLECTION_NAME
            self.collection: Any | None = None
            logger.info("VectorStore başarıyla başlatıldı")

        except Exception as e:
            logger.error(f"❌ VectorStore başlatma hatası: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _stable_job_id(job_dict: dict[str, Any]) -> str:
        """Create a deterministic job ID using URL if available."""
        url = job_dict.get("url") or job_dict.get("job_url")
        if url:
            digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        else:
            canonical = json.dumps(job_dict, sort_keys=True, ensure_ascii=False)
            digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"job_{digest}"

    def create_collection(self) -> bool:
        """Koleksiyon oluştur veya mevcut olanı getir"""
        try:
            # get_or_create_collection kullanarak hem yeni oluşturma hem de mevcut getirme
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": COSINE_METRIC},  # Cosine similarity kullan
            )

            # Mevcut öğe sayısını kontrol et
            if self.collection is not None:
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

    def job_exists(self, job_dict: dict[str, Any]) -> bool:
        """İş ilanının zaten mevcut olup olmadığını kontrol eder."""
        collection = self.get_collection()
        if not collection:
            return False

        job_id = self._stable_job_id(job_dict)
        try:
            existing = collection.get(ids=[job_id])
            return len(existing.get("ids", [])) > 0
        except Exception:
            return False

    def add_jobs(self, jobs_df: pd.DataFrame, embeddings: list[list[float] | None]) -> bool:
        """
        İş ilanlarını ve embeddings'lerini koleksiyona ekle - Tekrar eklemeyi önler
        """
        collection = self.get_collection()
        if not collection:
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
            collection.add(
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
        self,
        query_embedding: list[float],
        n_results: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> dict[str, list]:
        """Vektör benzerliği ile iş ilanı ara"""
        collection = self.get_collection()
        if not collection:
            return {"matches": [], "distances": [], "metadatas": []}

        try:
            where_clause = filter_metadata if filter_metadata else {}

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
            )

            return self._extract_search_results(results)

        except Exception as e:
            logger.error(f"❌ Vektör arama hatası: {str(e)}", exc_info=True)
            return {"matches": [], "distances": [], "metadatas": []}

    def _extract_search_results(self, results: dict | None) -> dict[str, list]:
        """Search sonuçlarını güvenli şekilde çıkar"""
        if not results:
            return {"matches": [], "distances": [], "metadatas": []}

        metadatas = results.get("metadatas")
        documents = results.get("documents")
        distances = results.get("distances")

        if metadatas and isinstance(metadatas, list) and len(metadatas) > 0 and metadatas[0] is not None:
            metadatas_list = metadatas[0] if metadatas[0] else []
            documents_list = documents[0] if documents and documents[0] else []
            distances_list = distances[0] if distances and distances[0] else []

            logger.info(f"🔍 {len(metadatas_list)} iş ilanı bulundu")
            return {
                "matches": documents_list,
                "distances": distances_list,
                "metadatas": metadatas_list,
            }
        else:
            logger.info("ℹ️ Arama kriterlerine uygun iş ilanı bulunamadı")
            return {"matches": [], "distances": [], "metadatas": []}

    def get_stats(self) -> dict[str, Any]:
        """Koleksiyon istatistiklerini getir"""
        collection = self.get_collection()
        if not collection:
            return {"total_jobs": 0, "error": "Koleksiyon erişim hatası"}

        try:
            total_count = collection.count()
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
def create_vector_store(
    persist_directory: str | None = None, collection_name: str | None = None
) -> VectorStore | None:
    """VectorStore örneği oluştur"""
    try:
        return VectorStore(persist_directory=persist_directory, collection_name=collection_name)
    except Exception as e:
        logger.error(f"VectorStore oluşturma hatası: {str(e)}")
        return None
