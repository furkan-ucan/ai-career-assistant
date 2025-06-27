from unittest.mock import MagicMock, patch

from src.exceptions import CVNotFoundError
from src.pipeline import analyze_and_find_best_jobs

# A minimal mock for CVAnalyzer result
MOCK_AI_METADATA = {
    "key_skills": ["python", "data analysis"],
    "target_job_titles": ["Data Analyst"],
    "skill_importance": [0.9, 0.8],
    "cv_summary": "A skilled data analyst with python experience.",
}

# A minimal mock for VectorStore result
MOCK_SIMILAR_JOBS = [{"title": "Data Analyst", "description": "python job", "similarity_score": 0.9}]


@patch("pathlib.Path.read_text", return_value="cv")
@patch("src.pipeline.CVProcessor")
@patch("src.pipeline.CVAnalyzer")
@patch("src.pipeline.collect_data_for_all_personas")
@patch("src.pipeline.display_results")
@patch("src.pipeline.log_summary_statistics")
def test_pipeline_no_rerank(
    mock_log_summary,
    mock_display,
    mock_collect_data,
    mock_cv_analyzer,
    mock_cv_processor,
    mock_read_text,
):
    """Test the main pipeline with the rerank feature disabled."""
    # Setup mocks
    mock_cv_analyzer.return_value.extract_metadata_from_cv.return_value = MOCK_AI_METADATA
    mock_collect_data.return_value = MagicMock()  # Return a mock dataframe

    # Execute the pipeline with rerank=False
    analyze_and_find_best_jobs(
        selected_personas=[],
        results_per_site=50,
        similarity_threshold=0.7,
        rerank=False,
    )

    # Assertions
    mock_cv_analyzer.assert_called_once()
    mock_collect_data.assert_called_once()
    mock_display.assert_called_once()
    mock_log_summary.assert_called_once()


@patch("pathlib.Path.read_text", return_value="cv")
@patch("src.pipeline.CVProcessor")
@patch("src.pipeline.CVAnalyzer")
@patch("src.pipeline.logger")
def test_pipeline_cv_processing_error(mock_logger, mock_cv_analyzer, mock_cv_processor, mock_read_text):
    """Test that the pipeline handles CV processing errors gracefully."""
    # Setup mock to raise an error
    mock_cv_analyzer.return_value.extract_metadata_from_cv.side_effect = CVNotFoundError("CV Error")

    # Execute and expect the function to exit gracefully (return None)
    result = analyze_and_find_best_jobs(
        selected_personas=[],
        results_per_site=50,
        similarity_threshold=0.7,
        rerank=True,
    )

    assert result is None
    mock_logger.error.assert_called()


@patch("pathlib.Path.read_text", return_value="cv")
@patch("src.pipeline.CVProcessor")
@patch("src.pipeline.CVAnalyzer")
@patch("src.pipeline.collect_data_for_all_personas")
@patch("src.pipeline.logger")
def test_pipeline_no_similar_jobs_found(
    mock_logger, mock_collect_data, mock_cv_analyzer, mock_cv_processor, mock_read_text
):
    """Test the pipeline's behavior when no data is collected."""
    # Setup mocks
    mock_cv_analyzer.return_value.extract_metadata_from_cv.return_value = MOCK_AI_METADATA
    mock_collect_data.return_value = None  # No jobs found

    # Execute
    analyze_and_find_best_jobs(
        selected_personas=[],
        results_per_site=50,
        similarity_threshold=0.7,
        rerank=True,
    )

    # Assert that collection was attempted
    mock_collect_data.assert_called_once()
