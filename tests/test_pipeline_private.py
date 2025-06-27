from types import SimpleNamespace

import pandas as pd
import pytest
from google.api_core import exceptions as google_exceptions

from src import pipeline
from src.models.pipeline_context import PipelineContext


def _make_context():
    cfg = {
        "paths": {"chromadb_dir": "dir", "cv_file": "cv.txt"},
        "vector_store_settings": {"collection_name": "name"},
    }
    return PipelineContext(config=cfg, cli_args=SimpleNamespace())


def test_setup_cv_processor_success(mocker):
    context = _make_context()
    mock_cv = mocker.patch("src.pipeline.CVProcessor").return_value
    mock_cv.load_cv.return_value = True
    mock_cv.create_cv_embedding.return_value = True
    result = pipeline._setup_cv_processor(context)
    assert result is mock_cv


def test_setup_cv_processor_failure(mocker):
    context = _make_context()
    mock_cv = mocker.patch("src.pipeline.CVProcessor").return_value
    mock_cv.load_cv.return_value = False
    result = pipeline._setup_cv_processor(context)
    assert result is None


def test_setup_vector_store_success(mocker):
    context = _make_context()
    mock_vs = mocker.patch("src.pipeline.VectorStore").return_value
    mock_vs.create_collection.return_value = True
    result = pipeline._setup_vector_store(context)
    assert result is mock_vs


def test_setup_vector_store_failure(mocker):
    context = _make_context()
    mock_vs = mocker.patch("src.pipeline.VectorStore").return_value
    mock_vs.create_collection.return_value = False
    result = pipeline._setup_vector_store(context)
    assert result is None


def test_rerank_with_ai_analysis(mocker):
    jobs = [
        {"title": "a", "fit_score": 1, "similarity_score": 90},
        {"title": "b", "fit_score": 2, "similarity_score": 80},
    ]
    mocker.patch("src.pipeline.genai.GenerativeModel")
    mocker.patch(
        "src.pipeline._analyse_single_job",
        side_effect=lambda j, c, m, t: {**j, "is_recommended": True, "fit_score": j["fit_score"] + 1},
    )
    analysed = pipeline._rerank_with_ai_analysis(jobs, "cv")
    assert analysed[0]["fit_score"] >= analysed[1]["fit_score"]


def test_collect_and_prepare_data_success(mocker):
    context = _make_context()
    mocker.patch("src.pipeline.collect_data_for_all_personas", return_value="csv")
    mock_cv = mocker.patch("src.pipeline.CVProcessor").return_value
    mock_cv.load_cv.return_value = True
    mock_cv.create_cv_embedding.return_value = True
    mock_vs = mocker.patch("src.pipeline.VectorStore").return_value
    mock_vs.create_collection.return_value = True
    mocker.patch("src.pipeline._process_and_load_jobs")
    csv_path, cv_emb, vs = pipeline._collect_and_prepare_data(context)
    assert csv_path == "csv"
    assert vs is mock_vs
    assert cv_emb is mock_cv.cv_embedding


def test_score_and_rank_jobs_with_rerank(mocker):
    context = _make_context()
    context.scoring_system = mocker.Mock()
    context.ai_metadata = {"cv_summary": "sum"}
    pipeline.rerank_settings["enabled"] = True
    mocker.patch("src.pipeline._search_and_score_jobs", return_value=[{"fit_score": 1, "similarity_score": 80}])
    mock_rerank = mocker.patch(
        "src.pipeline._rerank_with_ai_analysis", return_value=[{"fit_score": 2, "similarity_score": 80}]
    )
    result = pipeline._score_and_rank_jobs([0.1], mocker.Mock(), context)
    assert result[0]["fit_score"] == 2
    mock_rerank.assert_called_once()


def test_configure_scoring_system_and_apply_weights():
    cfg = {
        "scoring_system": {
            "description_weights": {"positive": {}},
            "dynamic_skill_weight": 10,
            "min_importance_for_scoring": 0.5,
        }
    }
    ai_md = {"key_skills": ["python"], "skill_importance": [0.8]}
    scoring = pipeline._configure_scoring_system(cfg, ai_md)
    assert isinstance(scoring, pipeline.IntelligentScoringSystem)
    assert cfg["scoring_system"]["description_weights"]["positive"] == {}
    updated = pipeline._apply_skill_weights(cfg, "java", 0.8, 10, 0.5)
    assert updated["scoring_system"]["description_weights"]["positive"]["java"] == 8


def test_extract_json_functions():
    text = 'prefix ```json\n{"a": 1}\n``` suffix'
    assert pipeline.extract_json_from_response(text) == {"a": 1}
    text2 = 'something {"b": 2} end'
    assert pipeline.extract_json_from_response(text2) == {"b": 2}


def test_search_and_score_jobs(mocker):
    context = _make_context()
    context.scoring_system = pipeline.IntelligentScoringSystem({"scoring_system": {}})
    mock_vs = mocker.Mock()
    mock_vs.search_jobs.return_value = {"metadatas": [{"title": "t"}], "distances": [0.2]}
    mocker.patch("src.pipeline.score_jobs", side_effect=lambda jobs, sc, debug=False: jobs)
    result = pipeline._search_and_score_jobs([0.1], mock_vs, 0.0, context.scoring_system, context)
    assert abs(result[0]["similarity_score"] - 80.0) < 1e-6


def test_deduplicate_and_save_jobs(tmp_path, mocker):
    context = _make_context()
    context.config["paths"] = {"data_dir": str(tmp_path)}
    df = pd.DataFrame([{"title": "t", "company": "c"}])
    mocker.patch("src.pipeline.save_dataframe_csv", return_value=str(tmp_path / "f.csv"))
    path = pipeline._deduplicate_and_save_jobs([df], context)
    assert path is not None
    assert str(path).endswith("f.csv")


@pytest.mark.parametrize(
    "exception_to_raise, expected_log_part",
    [
        (google_exceptions.ResourceExhausted("quota exhausted"), "API rate limit or quota exhausted"),
        (google_exceptions.DeadlineExceeded("timeout"), "API call timed out"),
        (ValueError("some other error"), "Unexpected error during AI analysis"),
    ],
)
def test_analyse_single_job_exception_handling(mocker, caplog, exception_to_raise, expected_log_part):
    """Test that _analyse_single_job handles various API exceptions gracefully."""
    # Mock the Gemini API call
    mock_model = mocker.patch("src.pipeline.genai.GenerativeModel").return_value
    mock_model.generate_content.side_effect = exception_to_raise

    # Sample job data
    job = {"title": "Test Job", "description": "Test description"}
    cv_summary = "Test CV summary"

    # Call the function
    result = pipeline._analyse_single_job(job, cv_summary, mock_model, 0.1)

    # Assertions
    assert result == job  # Should return the original job on failure
    assert expected_log_part in caplog.text
    assert "Test Job" in caplog.text
    if isinstance(exception_to_raise, ValueError):
        assert "some other error" in caplog.text
