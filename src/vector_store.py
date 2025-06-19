"""
Vektör Depolama Modülü
ChromaDB kullanarak iş ilanı vektörlerini saklar ve arama yapar.
"""

import chromadb
from chromadb.config import Settings
import pandas as pd
from typing import List, Dict, Optional, Any
import os
import json
from datetime import datetime

class VectorStore:
    def __init__(self, persist_directory: str = "data/chromadb"):
        """ChromaDB istemcisini başlat"""
        self.persist_directory = persist_directory

        # Persist directory oluştur
        os.makedirs(persist_directory, exist_ok=True)

        # ChromaDB istemcisi
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = "job_listings"
        self.collection = None

        print(f"✅ ChromaDB başlatıldı: {persist_directory}")

    def create_collection(self) -> bool:
        """İş ilanları koleksiyonu oluştur"""
        try:
            # Mevcut koleksiyonu sil (eğer varsa)
            try:
                self.client.delete_collection(self.collection_name)
                print("🗑️ Mevcut koleksiyon silindi")
            except:
                pass            # Yeni koleksiyon oluştur (COSINE SIMILARITY ile)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "İş ilanları vektör koleksiyonu", "hnsw:space": "cosine"}
            )

            print("✅ Yeni koleksiyon oluşturuldu")
            return True

        except Exception as e:
            print(f"❌ Koleksiyon oluşturma hatası: {str(e)}")
            return False

    def get_collection(self):
        """Mevcut koleksiyonu getir"""
        if not self.collection:
            try:
                self.collection = self.client.get_collection(self.collection_name)
                print("✅ Mevcut koleksiyon yüklendi")
            except:
                print("⚠️ Koleksiyon bulunamadı, yeni oluşturuluyor...")
                self.create_collection()

        return self.collection

    def add_jobs(self, jobs_df: pd.DataFrame, embeddings: List[Optional[List[float]]]) -> bool:
        """İş ilanlarını ve embeddings'lerini koleksiyona ekle"""
        if not self.get_collection():
            return False

        valid_jobs = []
        valid_embeddings = []
        valid_ids = []
        valid_metadatas = []

        # Geçerli embeddings'leri filtrele
        for i, (_, job) in enumerate(jobs_df.iterrows()):
            if embeddings[i] is not None:
                valid_jobs.append(job['description'] if 'description' in job else str(job))
                valid_embeddings.append(embeddings[i])
                valid_ids.append(f"job_{i}_{int(datetime.now().timestamp())}")

                # Metadata hazırla
                metadata = {
                    "title": str(job.get('title', 'N/A')),
                    "company": str(job.get('company', 'N/A')),
                    "location": str(job.get('location', 'N/A')),
                    "url": str(job.get('job_url', 'N/A')),
                    "date_posted": str(job.get('date_posted', 'N/A')),
                    "added_at": datetime.now().isoformat()
                }
                valid_metadatas.append(metadata)

        if not valid_embeddings:
            print("❌ Eklenecek geçerli embedding bulunamadı")
            return False

        try:
            # Batch olarak ekle
            self.collection.add(
                embeddings=valid_embeddings,
                documents=valid_jobs,
                metadatas=valid_metadatas,
                ids=valid_ids
            )

            print(f"✅ {len(valid_embeddings)} iş ilanı ChromaDB'ye eklendi")
            return True

        except Exception as e:
            print(f"❌ ChromaDB ekleme hatası: {str(e)}")
            return False

    def search_similar_jobs(self, cv_embedding: List[float], top_k: int = 15) -> List[Dict[str, Any]]:
        """CV'ye benzer işleri ara"""
        if not self.get_collection():
            return []

        try:
            results = self.collection.query(
                query_embeddings=[cv_embedding],
                n_results=top_k,
                include=['metadatas', 'distances', 'documents']
            )            # Sonuçları işle
            similar_jobs = []
            if results['metadatas'] and results['metadatas'][0]:
                for i, metadata in enumerate(results['metadatas'][0]):
                    distance = results['distances'][0][i]
                    # Cosine distance'ı cosine similarity'ye çevir
                    similarity_score = round((1 - distance) * 100, 2)

                    job_info = {
                        'title': metadata.get('title', 'N/A'),
                        'company': metadata.get('company', 'N/A'),
                        'location': metadata.get('location', 'N/A'),
                        'url': metadata.get('url', 'N/A'),
                        'date_posted': metadata.get('date_posted', 'N/A'),
                        'similarity_score': similarity_score,
                        'distance': round(distance, 4),
                        'description': results['documents'][0][i] if results['documents'][0] else 'N/A'
                    }
                    similar_jobs.append(job_info)

            print(f"✅ {len(similar_jobs)} benzer iş bulundu")
            return similar_jobs

        except Exception as e:
            print(f"❌ Arama hatası: {str(e)}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Koleksiyon istatistiklerini getir"""
        if not self.get_collection():
            return {}

        try:
            count = self.collection.count()
            return {
                "total_jobs": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            print(f"❌ İstatistik alma hatası: {str(e)}")
            return {}

if __name__ == "__main__":
    # Test çalıştırması
    store = VectorStore()
    stats = store.get_collection_stats()
    print("ChromaDB istatistikleri:", stats)
