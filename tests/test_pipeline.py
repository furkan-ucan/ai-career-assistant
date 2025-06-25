from pathlib import Path

import pandas as pd
import pytest

from src.pipeline import run_end_to_end_pipeline


def _mock_scoring_system():
    class Dummy:
        def score_job(self, job):
            return 100, {}

        def should_include(self, score):
            return True

    return Dummy()


def _basic_vector_store(mocker):
    mock_vs = mocker.MagicMock()
    mock_vs.create_collection.return_value = True
    mock_vs.add_jobs.return_value = True
    mock_vs.search_jobs.return_value = {
        "metadatas": [{"title": "Dev", "company": "Corp"}],
        "distances": [0.1],
    }
    mock_vs.job_exists.return_value = False
    return mock_vs


def _basic_cv_processor(mocker):
    mock_cv = mocker.MagicMock()
    mock_cv.load_cv.return_value = True
    mock_cv.create_cv_embedding.return_value = True
    mock_cv.cv_embedding = [0.1, 0.2]
    return mock_cv


def _basic_embeddings(mocker):
    mock_emb = mocker.MagicMock()
    mock_emb.create_embedding.return_value = [0.1, 0.2]
    return mock_emb


@pytest.mark.usefixtures("tmp_path")
def test_pipeline_happy_path(mocker, tmp_path):
    mocker.patch("src.pipeline.Path.read_text", return_value="cv")
    mocker.patch("src.pipeline.save_dataframe_csv", return_value=Path("fake.csv"))
    mocker.patch(
        "src.pipeline._load_and_validate_csv",
        return_value=pd.DataFrame({"title": ["Dev"], "company": ["Corp"], "description": ["d"]}),
    )
    mocker.patch(
        "src.pipeline.build_dynamic_personas", return_value={"Dev": {"term": "dev", "hours_old": 24, "results": 1}}
    )

    mock_collect = mocker.patch("src.pipeline.collect_data_for_all_personas", return_value="fake.csv")
    mock_analyzer_cls = mocker.patch("src.pipeline.CVAnalyzer")
    mock_analyzer = mock_analyzer_cls.return_value
    mock_analyzer.extract_metadata_from_cv.return_value = {}

    mock_scoring_cls = mocker.patch("src.pipeline.IntelligentScoringSystem", return_value=_mock_scoring_system())
    mocker.patch("src.pipeline.CVProcessor", return_value=_basic_cv_processor(mocker))
    mock_vector_cls = mocker.patch("src.pipeline.VectorStore", return_value=_basic_vector_store(mocker))
    mocker.patch("src.pipeline.EmbeddingService", return_value=_basic_embeddings(mocker))
    mock_display = mocker.patch("src.pipeline.display_results")
    mocker.patch("src.pipeline.score_jobs", side_effect=lambda jobs, scoring_system, debug=False: jobs)

    run_end_to_end_pipeline(["Dev"], 1, 80)

    mock_collect.assert_called_once()
    mock_analyzer_cls.assert_called_once()
    mock_scoring_cls.assert_called_once()
    mock_vector_cls.assert_called_once()
    mock_display.assert_called_once()


def test_pipeline_fails_if_data_collection_fails(mocker):
    mock_collect = mocker.patch("src.pipeline.collect_data_for_all_personas", return_value=None)
    mock_vector_cls = mocker.patch("src.pipeline.VectorStore")
    mock_cv_processor_cls = mocker.patch("src.pipeline.CVProcessor")
    mock_display = mocker.patch("src.pipeline.display_results")
    mocker.patch("src.pipeline.Path.read_text", return_value="cv")
    mocker.patch("src.pipeline.CVAnalyzer")
    mocker.patch("src.pipeline.IntelligentScoringSystem", return_value=_mock_scoring_system())

    run_end_to_end_pipeline(["Dev"], 1, 80)

    mock_collect.assert_called_once()
    mock_vector_cls.assert_not_called()
    mock_cv_processor_cls.assert_not_called()
    mock_display.assert_not_called()
