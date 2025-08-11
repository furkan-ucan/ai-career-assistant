# tests/test_pipeline_integration.py
"""
Comprehensive integration tests for the career analysis pipeline
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.pipeline import JobAnalysisPipeline


class TestPipelineIntegration:
    """Integration tests for the complete pipeline."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return {
            "job_search_settings": {
                "target_sites": ["indeed"],
                "default_hours_old": 72,
                "default_results_per_site": 5,
                "min_similarity_threshold": 60,
            },
            "paths": {
                "data_dir": "test_data",
                "cv_file": "test_cv.txt",
                "chromadb_dir": "test_chromadb",
                "logs_dir": "test_logs",
            },
            "embedding_settings": {
                "batch_size": 2,
                "retry_count": 1,
                "rate_limit_delay": 0,
            },
            "ai_reranking_settings": {
                "enabled": True,
                "rerank_pool_size": 10,
                "max_workers": 1,
                "llm_model": "gemini-1.5-flash-latest",
                "llm_temperature": 0.1,
            },
            "reranking_cache": {
                "enabled": True,
                "max_age_days": 30,
            },
            "scoring_system": {
                "threshold": 60,
                "weights": {"negative": -30, "positive": 30},
                "title_keywords": {"negative": ["senior"], "positive": ["junior"]},
            },
        }

    @pytest.fixture
    def mock_cli_args(self):
        """Create mock CLI arguments."""
        args = MagicMock()
        args.cv_path = "test_cv.txt"
        args.target_sites = ["indeed"]
        args.rerank = True
        args.threshold = 60
        return args

    @pytest.fixture
    def sample_cv_content(self):
        """Sample CV content for testing."""
        return """
        John Doe
        Software Developer

        Skills:
        - Python programming
        - Web development with Django
        - Database design with PostgreSQL
        - API development
        - Agile methodologies

        Experience:
        Junior Developer at Tech Corp (2023-present)
        - Developed web applications using Python and Django
        - Worked with PostgreSQL databases
        - Collaborated in Agile teams
        """

    @pytest.fixture
    def sample_jobs_data(self):
        """Sample job data for testing."""
        return pd.DataFrame(
            [
                {
                    "title": "Junior Python Developer",
                    "company": "Tech Solutions Inc",
                    "location": "Remote",
                    "description": "We are looking for a junior Python developer with Django experience. PostgreSQL knowledge is a plus.",
                    "url": "https://example.com/job1",
                    "source_site": "indeed",
                    "date_posted": "2025-01-20",
                },
                {
                    "title": "Senior Software Engineer",
                    "company": "Big Corp",
                    "location": "New York",
                    "description": "Senior position requiring 5+ years Python experience, microservices, and team leadership.",
                    "url": "https://example.com/job2",
                    "source_site": "indeed",
                    "date_posted": "2025-01-19",
                },
                {
                    "title": "Web Developer",
                    "company": "Startup Co",
                    "location": "San Francisco",
                    "description": "Full-stack developer needed. Python, Django, and modern frontend frameworks required.",
                    "url": "https://example.com/job3",
                    "source_site": "indeed",
                    "date_posted": "2025-01-18",
                },
            ]
        )

    def test_complete_pipeline_flow(self, mock_config, mock_cli_args, sample_cv_content, sample_jobs_data):
        """Test the complete pipeline from start to finish."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test CV file
            cv_file = temp_path / "test_cv.txt"
            cv_file.write_text(sample_cv_content)
            mock_cli_args.cv_path = str(cv_file)

            # Mock external dependencies
            with (
                patch("src.pipeline.TieredJobCollector") as mock_collector,
                patch("src.pipeline.EmbeddingService") as mock_embedding,
                patch("src.pipeline.CVAnalyzer") as mock_analyzer,
                patch("src.pipeline.VectorStore") as mock_vector_store,
                patch("src.pipeline.genai.GenerativeModel") as mock_model,
            ):
                # Setup mocks
                mock_collector_instance = mock_collector.return_value
                mock_collector_instance.collect_all_jobs.return_value = sample_jobs_data

                mock_embedding_instance = mock_embedding.return_value
                mock_embedding_instance.create_embedding.return_value = [0.1, 0.2, 0.3]
                mock_embedding_instance.create_embeddings_batch.return_value = [[0.1, 0.2, 0.3]] * len(
                    sample_jobs_data
                )

                mock_analyzer_instance = mock_analyzer.return_value
                mock_analyzer_instance.extract_metadata_from_cv.return_value = {
                    "key_skills": ["python", "django", "postgresql", "api development"],
                    "target_job_titles": ["python developer", "web developer"],
                    "skill_importance": [0.9, 0.8, 0.7, 0.8],
                    "cv_summary": "Junior developer with Python and Django experience",
                }

                mock_vector_store_instance = mock_vector_store.return_value
                mock_vector_store_instance.add_jobs.return_value = None
                mock_vector_store_instance.similarity_search.return_value = [
                    {"title": "Junior Python Developer", "score": 85.0, **sample_jobs_data.iloc[0].to_dict()},
                    {"title": "Web Developer", "score": 75.0, **sample_jobs_data.iloc[2].to_dict()},
                ]

                mock_model_instance = mock_model.return_value
                mock_model_instance.generate_content.return_value.text = """
                {
                    "fit_score": 85,
                    "is_recommended": true,
                    "reasoning": "Strong match for Python and Django skills",
                    "matching_keywords": ["python", "django", "postgresql"],
                    "missing_keywords": ["team leadership"]
                }
                """

                # Run pipeline
                pipeline = JobAnalysisPipeline(mock_config)
                results = pipeline.run(mock_cli_args)

                # Verify results
                assert results is not None
                assert len(results) > 0
                assert all("fit_score" in job for job in results)
                assert all("is_recommended" in job for job in results)

                # Verify pipeline steps were called
                mock_collector_instance.collect_all_jobs.assert_called_once()
                mock_analyzer_instance.extract_metadata_from_cv.assert_called_once()
                mock_vector_store_instance.add_jobs.assert_called()
                mock_vector_store_instance.similarity_search.assert_called()

    def test_pipeline_with_no_jobs_found(self, mock_config, mock_cli_args, sample_cv_content):
        """Test pipeline behavior when no jobs are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cv_file = temp_path / "test_cv.txt"
            cv_file.write_text(sample_cv_content)
            mock_cli_args.cv_path = str(cv_file)

            with patch("src.pipeline.TieredJobCollector") as mock_collector:
                mock_collector_instance = mock_collector.return_value
                mock_collector_instance.collect_all_jobs.return_value = pd.DataFrame()  # Empty DataFrame

                pipeline = JobAnalysisPipeline(mock_config)
                results = pipeline.run(mock_cli_args)

                assert results == []

    def test_pipeline_handles_api_failures(self, mock_config, mock_cli_args, sample_cv_content):
        """Test pipeline resilience to API failures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cv_file = temp_path / "test_cv.txt"
            cv_file.write_text(sample_cv_content)
            mock_cli_args.cv_path = str(cv_file)

            with patch("src.pipeline.CVAnalyzer") as mock_analyzer:
                mock_analyzer_instance = mock_analyzer.return_value
                mock_analyzer_instance.extract_metadata_from_cv.side_effect = Exception("API Error")

                pipeline = JobAnalysisPipeline(mock_config)
                results = pipeline.run(mock_cli_args)

                # Pipeline should handle errors gracefully
                assert results is None

    def test_scoring_system_integration(self, mock_config, sample_jobs_data):
        """Test the scoring system integration."""
        from src.scoring_system import ScoringSystem, score_and_filter_jobs

        ai_metadata = {
            "key_skills": ["python", "django"],
            "skill_importance": [0.9, 0.8],
        }

        scoring_system = ScoringSystem(mock_config["scoring_system"], ai_metadata)
        scored_jobs = score_and_filter_jobs(sample_jobs_data, scoring_system)

        # Verify scoring
        assert len(scored_jobs) > 0
        assert all("score" in job for job in scored_jobs)
        # Check that scoring system applied scores (threshold filtering happens in scoring system)
        assert all(isinstance(job.get("score"), (int, float)) for job in scored_jobs)

    def test_cache_integration(self, mock_config):
        """Test cache systems integration."""
        from src.embedding_cache import EmbeddingCache
        from src.reranking_cache import RerankingCache

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test embedding cache
            embedding_cache = EmbeddingCache(cache_dir=temp_dir + "/embedding")
            test_text = "This is a test description for caching"
            test_embedding = [0.1, 0.2, 0.3, 0.4]

            # Save and retrieve
            embedding_cache.save_embedding(test_text, test_embedding)
            cached_embedding = embedding_cache.get_cached_embedding(test_text)

            assert cached_embedding == test_embedding

            # Test reranking cache
            reranking_cache = RerankingCache(cache_dir=temp_dir + "/reranking")
            test_job = {"title": "Test Job", "company": "Test Corp", "description": "Test description"}
            test_result = {"fit_score": 85, "is_recommended": True}

            # Save and retrieve
            reranking_cache.save_reranking_result(test_job, test_result)
            cached_result = reranking_cache.get_cached_reranking(test_job)

            assert cached_result == test_result

    def test_database_maintenance_integration(self, sample_jobs_data):
        """Test database maintenance integration."""
        from src.database_maintenance import DatabaseMaintenance

        with tempfile.TemporaryDirectory() as temp_dir:
            # This is a basic test - in practice, you'd need to setup ChromaDB
            maintenance = DatabaseMaintenance(persist_directory=temp_dir)

            # Test should not raise exceptions
            stats = maintenance.get_database_stats()
            assert isinstance(stats, dict)

    def test_report_generation_integration(self):
        """Test report generation integration."""
        from src.report_generator import StrategicReportGenerator

        with tempfile.TemporaryDirectory() as temp_dir:
            generator = StrategicReportGenerator(output_dir=temp_dir)

            sample_results = [
                {
                    "title": "Python Developer",
                    "company": "Tech Corp",
                    "fit_score": 85,
                    "is_recommended": True,
                    "reasoning": "Good match",
                    "matching_keywords": ["python", "django"],
                    "missing_keywords": ["react"],
                }
            ]

            sample_metadata = {
                "key_skills": ["python", "django"],
                "cv_summary": "Experienced developer",
            }

            report_file = generator.generate_comprehensive_report(
                final_results=sample_results,
                ai_metadata=sample_metadata,
                raw_jobs_count=10,
                threshold=60,
            )

            assert report_file.exists()
            assert report_file.suffix == ".md"

            # Verify content
            content = report_file.read_text()
            assert "Stratejik Kariyer Analizi Raporu" in content
            assert "Python Developer" in content
            assert "Tech Corp" in content
