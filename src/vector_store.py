# src/vector_store.py
"""Vector Store module, hardened against data duplication errors."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, cast

import chromadb
import numpy as np
import pandas as pd

from .core.constants import COSINE_METRIC, DEFAULT_COLLECTION_NAME
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

ChromaMetadata = dict[str, str | int | float | bool]


class VectorStore:
    """Manages the vector database for job embeddings."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        persist_directory: str | Path | None = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ):
        self.embedding_service = embedding_service
        try:
            if persist_directory:
                persist_path = Path(persist_directory) if isinstance(persist_directory, str) else persist_directory
                self.client = chromadb.PersistentClient(path=str(persist_path))
            else:
                self.client = chromadb.Client()

            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": COSINE_METRIC},
            )
            logger.info(f"✅ Vector store collection '{collection_name}' is ready.")
        except Exception as e:
            logger.exception(f"❌ Failed to initialize VectorStore: {e}")
            raise

    def _clean_metadata_for_chromadb(self, metadata: dict[str, Any]) -> ChromaMetadata:
        clean_meta: ChromaMetadata = {}
        for key, value in metadata.items():
            str_key = str(key)
            if isinstance(value, (str, int, float, bool)):
                clean_meta[str_key] = value
        return clean_meta

    def add_jobs(self, jobs_df: pd.DataFrame):
        """Add new jobs to the vector store with proper error handling."""
        if jobs_df.empty:
            return

        try:
            # Filter out existing jobs
            new_jobs_df = self._filter_existing_jobs(jobs_df)
            if new_jobs_df.empty:
                logger.info("ℹ️ No new jobs to add to the vector store (all found jobs already exist).")
                return

            # Prepare job data with embeddings
            prepared_data = self._prepare_job_data_with_embeddings(new_jobs_df)
            if not prepared_data["valid_jobs"]:
                logger.warning("⚠️ No valid jobs with embeddings to store.")
                return

            # Store jobs in vector database
            self._store_jobs_in_vector_db(prepared_data)
            logger.info(f"✅ Successfully added {len(prepared_data['valid_ids'])} new jobs to the vector store.")

        except Exception as e:
            logger.error(f"❌ Failed to add jobs to vector store: {e}", exc_info=True)
            raise

    def _filter_existing_jobs(self, jobs_df: pd.DataFrame) -> pd.DataFrame:
        """Filter out jobs that already exist in the vector store."""
        records = jobs_df.to_dict("records")
        # CRITICAL FIX: Ensure IDs sent to ChromaDB for checking are unique.
        ids_to_check = {self._stable_job_id(job) for job in records}
        ids_list = list(ids_to_check)

        if not ids_list:
            return pd.DataFrame()

        try:
            existing_ids = set(self.collection.get(ids=ids_list)["ids"])
            return jobs_df[~jobs_df.apply(lambda row: self._stable_job_id(row.to_dict()) in existing_ids, axis=1)]
        except Exception as e:
            logger.error(f"❌ Failed to check existing jobs: {e}")
            raise

    def _prepare_job_data_with_embeddings(self, jobs_df: pd.DataFrame) -> dict[str, list]:
        """Prepare job data with embeddings for storage."""
        new_records = jobs_df.to_dict("records")
        descriptions = [str(job.get("description", "")) for job in new_records]
        embeddings_list = self.embedding_service.create_embeddings_batch(texts=descriptions)

        valid_jobs, valid_embeddings, valid_ids = [], [], []
        for job, embedding in zip(new_records, embeddings_list, strict=True):
            if embedding is not None:
                valid_jobs.append(job)
                valid_embeddings.append(embedding)
                valid_ids.append(self._stable_job_id(job))

        return {"valid_jobs": valid_jobs, "valid_embeddings": valid_embeddings, "valid_ids": valid_ids}

    def _store_jobs_in_vector_db(self, prepared_data: dict[str, list]) -> None:
        """Store prepared job data in the vector database."""
        valid_jobs = prepared_data["valid_jobs"]
        valid_embeddings = prepared_data["valid_embeddings"]
        valid_ids = prepared_data["valid_ids"]

        clean_metadatas = [self._clean_metadata_for_chromadb(cast(dict[str, Any], job)) for job in valid_jobs]

        try:
            self.collection.add(
                embeddings=np.array(valid_embeddings),
                documents=[str(job.get("description", "")) for job in valid_jobs],
                metadatas=cast(Any, clean_metadatas),
                ids=valid_ids,
            )
        except Exception as e:
            logger.error(f"❌ Failed to store jobs in ChromaDB: {e}")
            raise

    def search_jobs(self, query_embedding: list[float], n_results: int = 10) -> list[dict[str, Any]]:
        if not query_embedding:
            return []

        try:
            results = self.collection.query(
                query_embeddings=np.array([query_embedding]),
                n_results=n_results,
            )
        except Exception as e:
            logger.exception(f"❌ Failed to query ChromaDB: {e}")
            return []

        if not results or not results.get("metadatas"):
            return []

        metadatas = results.get("metadatas")
        if not metadatas or not metadatas[0]:
            return []

        metadatas_list = metadatas[0]
        distances = results.get("distances", [[]])
        distances_list = distances[0] if distances else []

        similar_jobs = []
        for metadata, dist in zip(metadatas_list, distances_list, strict=False):
            if metadata is None or dist is None:
                continue
            job = dict(cast(dict[str, Any], metadata))
            job["similarity_score"] = (1 - float(dist)) * 100
            similar_jobs.append(job)

        return similar_jobs

    def _stable_job_id(self, job_dict: dict[Any, Any]) -> str:
        safe_job_dict = cast(dict[str, Any], job_dict)
        url = safe_job_dict.get("url") or safe_job_dict.get("job_url")
        if url:
            return hashlib.sha256(str(url).encode("utf-8")).hexdigest()
        canonical = json.dumps(safe_job_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
