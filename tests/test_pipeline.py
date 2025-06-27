import pandas as pd
import pytest

from src.pipeline import run_end_to_end_pipeline


@pytest.fixture
def mock_scoring_system():
    class Dummy:
        def score_job(self, job):
            return 100, {}

        def should_include(self, score):
            return True

    return Dummy()


@pytest.fixture
def basic_vector_store(mocker):
    mock_vs = mocker.MagicMock()
    mock_vs.create_collection.return_value = True
    mock_vs.add_jobs.return_value = True
    mock_vs.search_jobs.return_value = {
        "metadatas": [[{"title": "Dev", "company": "Corp"}]],
        "distances": [[0.1]],
    }
    mock_vs.job_exists.return_value = False
    return mock_vs


@pytest.fixture
def basic_cv_processor(mocker):
    mock_cv = mocker.MagicMock()
    mock_cv.load_cv.return_value = True
    mock_cv.create_cv_embedding.return_value = True
    mock_cv.cv_embedding = [0.1, 0.2]
    return mock_cv


@pytest.fixture
def basic_embeddings(mocker):
    mock_emb = mocker.MagicMock()
    mock_emb.create_embedding.return_value = [0.1, 0.2]
    return mock_emb


def test_pipeline_setup_phase(mocker, mock_scoring_system):
    """Tests the initial setup of CV analysis, persona building, and scoring system."""
    # Mocks for setup phase
    mocker.patch("src.pipeline.Path.read_text", return_value="cv text")
    mock_analyzer_cls = mocker.patch("src.pipeline.CVAnalyzer")
    mock_analyzer = mock_analyzer_cls.return_value
    mock_analyzer.extract_metadata_from_cv.return_value = {"target_job_titles": ["Dev"]}

    mock_build_personas = mocker.patch("src.pipeline.build_dynamic_personas")
    mock_configure_scoring = mocker.patch("src.pipeline._configure_scoring_system", return_value=mock_scoring_system)

    # Mock the rest of the pipeline to isolate the setup phase
    mocker.patch("src.pipeline._execute_full_pipeline")

    # Run the pipeline orchestrator
    run_end_to_end_pipeline()

    # Assertions for setup phase
    mock_analyzer_cls.assert_called_once()
    mock_analyzer.extract_metadata_from_cv.assert_called_once_with("cv text")
    mock_build_personas.assert_called_once_with(["Dev"])
    mock_configure_scoring.assert_called_once()


def test_pipeline_execution_flow(mocker):
    """Tests the main execution flow after a successful setup."""
    # Mock the entire setup phase to focus on execution
    mocker.patch("src.pipeline._setup_ai_metadata_and_personas")
    mocker.patch("src.pipeline._configure_scoring_system", return_value=mocker.MagicMock())

    # Mock the core execution functions to verify they are called
    mock_collect_prepare = mocker.patch(
        "src.pipeline._collect_and_prepare_data", return_value=("fake.csv", [0.1], mocker.MagicMock())
    )
    mock_score_rank = mocker.patch("src.pipeline._score_and_rank_jobs", return_value=[{"title": "Dev"}])
    mock_display = mocker.patch("src.pipeline.display_results")
    mock_log_summary = mocker.patch("src.pipeline.log_summary_statistics")
    mocker.patch("pandas.read_csv", return_value=pd.DataFrame())

    # Run the pipeline
    run_end_to_end_pipeline()

    # Assert that the main execution steps were called
    mock_collect_prepare.assert_called_once()
    mock_score_rank.assert_called_once()
    mock_display.assert_called_once()
    mock_log_summary.assert_called_once()


def test_pipeline_reranking_logic(
    mocker, basic_cv_processor, basic_vector_store, mock_scoring_system, basic_embeddings
):
    """Tests that the AI reranking is called when enabled and conditions are met."""
    # Mock setup phase
    mocker.patch("src.pipeline.Path.read_text", return_value="cv")
    mock_analyzer_cls = mocker.patch("src.pipeline.CVAnalyzer")
    mock_analyzer = mock_analyzer_cls.return_value
    # This metadata is crucial for reranking to be triggered
    mock_analyzer.extract_metadata_from_cv.return_value = {"cv_summary": "summary"}

    # Mock data collection and processing
    mocker.patch("src.pipeline.collect_data_for_all_personas", return_value="fake.csv")
    mocker.patch("src.pipeline._load_and_validate_csv", return_value=pd.DataFrame([{"title": "Dev"}]))
    mocker.patch("src.pipeline.CVProcessor", return_value=basic_cv_processor)
    mocker.patch("src.pipeline.VectorStore", return_value=basic_vector_store)
    mocker.patch("src.pipeline.EmbeddingService", return_value=basic_embeddings)
    mocker.patch("src.pipeline.IntelligentScoringSystem", return_value=mock_scoring_system)
    mocker.patch("src.pipeline.score_jobs", side_effect=lambda j, s, debug: j)
    mocker.patch("src.pipeline.display_results")
    mocker.patch("src.pipeline.log_summary_statistics")

    # Mock the reranking function itself to see if it's called
    mock_rerank_func = mocker.patch("src.pipeline._rerank_with_ai_analysis", return_value=[])

    # Enable reranking in config
    mocker.patch.dict("src.pipeline.rerank_settings", {"enabled": True})

    # Run with reranking enabled (default)
    run_end_to_end_pipeline()

    # Assert reranking was called
    mock_rerank_func.assert_called_once()


def test_pipeline_fails_if_data_collection_fails(mocker, mock_scoring_system):
    """Ensures pipeline stops if data collection returns nothing."""
    # Mock setup
    mocker.patch("src.pipeline.Path.read_text", return_value="cv")
    mocker.patch("src.pipeline.CVAnalyzer")
    mocker.patch("src.pipeline.IntelligentScoringSystem", return_value=mock_scoring_system)

    # Mock data collection to fail (return None)
    mock_collect = mocker.patch("src.pipeline.collect_data_for_all_personas", return_value=None)

    # Mock subsequent steps to ensure they are not called
    mock_vector_cls = mocker.patch("src.pipeline.VectorStore")
    mock_cv_processor_cls = mocker.patch("src.pipeline.CVProcessor")
    mock_display = mocker.patch("src.pipeline.display_results")

    # Run pipeline
    run_end_to_end_pipeline(["Dev"], 1, 80)

    # Assertions
    mock_collect.assert_called_once()
    mock_vector_cls.assert_not_called()
    mock_cv_processor_cls.assert_not_called()
    mock_display.assert_not_called()
