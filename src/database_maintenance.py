# src/database_maintenance.py
"""
Database Maintenance System - Cleans old and irrelevant data
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import chromadb

logger = logging.getLogger(__name__)


class DatabaseMaintenance:
    """Maintains vector database by cleaning old and irrelevant jobs."""

    def __init__(self, persist_directory: str | Path = "data/chromadb", collection_name: str = "job_embeddings"):
        """Initialize database maintenance."""
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name

        if self.persist_directory.exists():
            self.client = chromadb.PersistentClient(path=str(self.persist_directory))
            try:
                self.collection = self.client.get_collection(name=collection_name)
                logger.info(f"✅ Connected to collection '{collection_name}' for maintenance")
            except ValueError:
                logger.warning(f"Collection '{collection_name}' not found. Creating new one.")
                self.collection = self.client.create_collection(name=collection_name)
        else:
            logger.warning(f"Database directory {self.persist_directory} does not exist")
            self.collection = None

    def cleanup_old_jobs(self, max_age_days: int = 30) -> int:
        """Remove jobs older than specified days."""
        if not self.collection:
            return 0

        try:
            # Get all job data
            all_data = self.collection.get(include=["metadatas", "documents"])

            if not all_data["ids"]:
                logger.info("No jobs found in database")
                return 0

            # Calculate cutoff date
            cutoff_date = datetime.now(UTC) - timedelta(days=max_age_days)

            old_job_ids = []
            metadatas = all_data["metadatas"]
            if metadatas is not None:
                for i, metadata in enumerate(metadatas):
                    if metadata and "date_posted" in metadata:
                        try:
                            date_posted = metadata["date_posted"]
                            if isinstance(date_posted, str):
                                job_date = datetime.fromisoformat(date_posted)
                                if job_date < cutoff_date:
                                    old_job_ids.append(all_data["ids"][i])
                        except (ValueError, TypeError):
                            # If date parsing fails, consider it old
                            old_job_ids.append(all_data["ids"][i])

            # Remove old jobs
            if old_job_ids:
                self.collection.delete(ids=old_job_ids)
                logger.info(f"🗑️ Removed {len(old_job_ids)} old jobs (older than {max_age_days} days)")
                return len(old_job_ids)
            else:
                logger.info(f"No jobs older than {max_age_days} days found")
                return 0

        except Exception as e:
            logger.error(f"❌ Error during old job cleanup: {e}")
            return 0

    def remove_duplicate_jobs(self) -> int:
        """Remove duplicate jobs based on URL or content similarity."""
        if not self.collection:
            return 0

        try:
            # Get all job data
            all_data = self.collection.get(include=["metadatas", "documents"])

            if not all_data["ids"]:
                return 0

            # Track URLs and duplicates
            url_to_id = {}
            duplicate_ids = []

            metadatas = all_data["metadatas"]
            if metadatas is not None:
                for i, metadata in enumerate(metadatas):
                    job_id = all_data["ids"][i]

                    if metadata and "url" in metadata:
                        url = metadata["url"]
                        if url in url_to_id:
                            # Duplicate found
                            duplicate_ids.append(job_id)
                            logger.debug(f"Found duplicate job: {url}")
                        else:
                            url_to_id[url] = job_id

            # Remove duplicates
            if duplicate_ids:
                self.collection.delete(ids=duplicate_ids)
                logger.info(f"🗑️ Removed {len(duplicate_ids)} duplicate jobs")
                return len(duplicate_ids)
            else:
                logger.info("No duplicate jobs found")
                return 0

        except Exception as e:
            logger.error(f"❌ Error during duplicate removal: {e}")
            return 0

    def cleanup_invalid_jobs(self) -> int:
        """Remove jobs with missing or invalid data."""
        if not self.collection:
            return 0

        try:
            # Get all job data
            all_data = self.collection.get(include=["metadatas", "documents"])

            if not all_data["ids"]:
                return 0

            invalid_ids = []

            metadatas = all_data["metadatas"]
            documents = all_data["documents"]

            if metadatas is not None:
                for i, metadata in enumerate(metadatas):
                    job_id = all_data["ids"][i]
                    document = documents[i] if documents and i < len(documents) else None

                    # Check for invalid conditions
                    is_invalid = False

                    # No metadata
                    if not metadata:
                        is_invalid = True
                        logger.debug(f"Job {job_id} has no metadata")

                    # No document/description
                    elif not document or len(document.strip()) < 10:
                        is_invalid = True
                        logger.debug(f"Job {job_id} has no valid description")

                    # Missing essential fields
                    elif not metadata.get("title") or not metadata.get("company"):
                        is_invalid = True
                        logger.debug(f"Job {job_id} missing title or company")

                    if is_invalid:
                        invalid_ids.append(job_id)

            # Remove invalid jobs
            if invalid_ids:
                self.collection.delete(ids=invalid_ids)
                logger.info(f"🗑️ Removed {len(invalid_ids)} invalid jobs")
                return len(invalid_ids)
            else:
                logger.info("No invalid jobs found")
                return 0

        except Exception as e:
            logger.error(f"❌ Error during invalid job cleanup: {e}")
            return 0

    def get_database_stats(self) -> dict[str, Any]:
        """Get comprehensive database statistics."""
        if not self.collection:
            return {"error": "No collection available"}

        try:
            # Get all data for analysis
            all_data = self.collection.get(include=["metadatas"])
            total_jobs = len(all_data["ids"])

            if total_jobs == 0:
                return {"total_jobs": 0, "by_site": {}, "by_age": {}, "storage_mb": 0}

            # Analyze by site
            by_site: dict[str, int] = {}
            by_age = {"this_week": 0, "this_month": 0, "older": 0}

            now = datetime.now(UTC)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            metadatas = all_data["metadatas"]
            if metadatas is not None:
                for metadata in metadatas:
                    if metadata:
                        # Count by site
                        site_value = metadata.get("source_site", "unknown")
                        site = str(site_value) if site_value is not None else "unknown"
                        by_site[site] = by_site.get(site, 0) + 1

                        # Count by age
                        if "date_posted" in metadata:
                            try:
                                date_posted = metadata["date_posted"]
                                if isinstance(date_posted, str):
                                    job_date = datetime.fromisoformat(date_posted)
                                    if job_date >= week_ago:
                                        by_age["this_week"] += 1
                                    elif job_date >= month_ago:
                                        by_age["this_month"] += 1
                                    else:
                                        by_age["older"] += 1
                            except (ValueError, TypeError):
                                by_age["older"] += 1
                        else:
                            by_age["older"] += 1

            # Estimate storage size
            storage_mb = 0.0
            if self.persist_directory.exists():
                total_size = sum(f.stat().st_size for f in self.persist_directory.rglob("*") if f.is_file())
                storage_mb = total_size / (1024 * 1024)

            return {
                "total_jobs": total_jobs,
                "by_site": by_site,
                "by_age": by_age,
                "storage_mb": round(storage_mb, 2),
                "collection_name": self.collection_name,
            }

        except Exception as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {"error": str(e)}

    def perform_full_maintenance(self, max_age_days: int = 30) -> dict[str, Any]:
        """Perform comprehensive database maintenance."""
        if not self.collection:
            return {"error": "No collection available"}

        logger.info("🔧 Starting comprehensive database maintenance...")

        results = {}

        # Get initial stats
        initial_stats = self.get_database_stats()
        initial_count = initial_stats.get("total_jobs", 0)

        # Cleanup operations
        results["removed_old"] = self.cleanup_old_jobs(max_age_days)
        results["removed_duplicates"] = self.remove_duplicate_jobs()
        results["removed_invalid"] = self.cleanup_invalid_jobs()

        # Get final stats
        final_stats = self.get_database_stats()
        final_count = final_stats.get("total_jobs", 0)

        results["initial_count"] = initial_count
        results["final_count"] = final_count
        results["total_removed"] = initial_count - final_count

        logger.info("✅ Database maintenance completed:")
        logger.info(f"   Initial jobs: {initial_count}")
        logger.info(f"   Final jobs: {final_count}")
        logger.info(f"   Total removed: {results['total_removed']}")
        logger.info(f"   Storage: {final_stats.get('storage_mb', 0):.2f} MB")

        return results
