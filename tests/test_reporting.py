import logging

import pandas as pd
import pytest

from src.reporting import display_results, log_summary_statistics


@pytest.fixture()
def sample_jobs():
    return [
        {
            "title": "Software Engineer",
            "company": "TechCorp",
            "location": "Remote",
            "fit_score": 90.0,
            "reasoning": "Great fit",
            "matching_keywords": ["python"],
            "missing_keywords": ["sap"],
            "source_site": "SiteA",
            "persona_source": "dev",
            "url": "http://job1",
        },
        {
            "title": "Data Scientist",
            "company": "DataCorp",
            "location": "Istanbul",
            "fit_score": 85.0,
            "reasoning": "Good",
            "matching_keywords": ["sql"],
            "missing_keywords": [],
            "source_site": "SiteB",
            "persona_source": "data",
            "url": "http://job2",
        },
    ]


@pytest.fixture
def sample_jobs_df():
    """Create sample all_jobs DataFrame for testing."""
    return pd.DataFrame(
        {
            "source_site": ["kariyer.net", "yenibiris.com", "kariyer.net", "linkedin"],
            "description": [
                "Python developer with React experience",
                "Business analyst with SQL knowledge",
                "Full-stack developer React TypeScript",
                "Data analyst Python pandas experience",
            ],
            "title": ["Python Developer", "Business Analyst", "Full Stack Developer", "Data Analyst"],
            "company": ["TechCorp", "BizCorp", "DevCorp", "DataCorp"],
        }
    )


@pytest.fixture
def sample_high_quality_jobs():
    """Create sample high-quality jobs list for testing."""
    return [
        {
            "title": "Python Developer",
            "company": "TechCorp",
            "persona_source": "developer",
            "fit_score": 85.5,
            "matching_keywords": ["python"],
        },
        {
            "title": "Business Analyst",
            "company": "BizCorp",
            "persona_source": "analyst",
            "fit_score": 78.2,
            "matching_keywords": ["sql"],
        },
        {
            "title": "Full Stack Developer",
            "company": "DevCorp",
            "persona_source": "developer",
            "fit_score": 82.1,
            "matching_keywords": ["react"],
        },
    ]


@pytest.fixture
def sample_ai_metadata():
    """Create sample AI metadata for testing."""
    return {
        "key_skills": ["python", "react", "sql", "typescript"],
        "target_job_titles": ["Business Analyst", "Python Developer"],
        "skill_importance": [0.95, 0.85, 0.80, 0.75],
    }


def test_display_results_with_valid_jobs(sample_jobs, caplog):
    original_raise_exceptions = logging.raiseExceptions
    try:
        logging.raiseExceptions = False
        with caplog.at_level(logging.INFO, logger="src.reporting"):
            display_results(sample_jobs, 80)
        output = caplog.text
        assert "Software Engineer" in output
        assert "Great fit" in output  # Check for reasoning
        assert "Eşleşen: python" in output  # Check for matching keywords
        assert "DataCorp" in output
        assert "Uygunluk eşiği: %80 ve üzeri" in output
        assert "Persona Dağılımı" in output
    finally:
        logging.raiseExceptions = original_raise_exceptions


def test_display_results_with_no_jobs(caplog):
    logging.raiseExceptions = False
    with caplog.at_level(logging.INFO, logger="src.reporting"):
        display_results([], 70)
    output = caplog.text
    assert "0 ilan bulundu" in output
    assert "Eşiği düşürmeyi" in output


@pytest.mark.parametrize(
    "jobs_df_fixture,high_quality_jobs_fixture,ai_metadata_fixture,expected_sections,missing_sections",
    [
        # Case 1: Full data, all sections should be present
        (
            "sample_jobs_df",
            "sample_high_quality_jobs",
            "sample_ai_metadata",
            ["Bulunan İlanların Site Dağılımı", "En Önemli Yetenekleriniz", "En Başarılı Personalar"],
            [],
        ),
        # Case 2: Empty jobs DataFrame, site distribution should be missing
        (
            "empty_df",
            "sample_high_quality_jobs",
            "sample_ai_metadata",
            ["En Önemli Yetenekleriniz", "En Başarılı Personalar"],
            ["Bulunan İlanların Site Dağılımı"],
        ),
        # Case 3: Empty high-quality jobs, persona and skill sections should be missing
        (
            "sample_jobs_df",
            "empty_high_quality_jobs",  # No matching keywords to aggregate
            "sample_ai_metadata",
            ["Bulunan İlanların Site Dağılımı", "En Önemli Yetenekleriniz"],  # Skills from CV are still shown
            ["En Başarılı Personalar", "En Popüler 5 Skill"],  # Persona and aggregated skills are missing
        ),
        # Case 4: No AI metadata, should fall back to skill aggregation from jobs
        (
            "sample_jobs_df",
            "sample_high_quality_jobs",
            "no_ai_metadata",
            ["Bulunan İlanların Site Dağılımı", "En Popüler 5 Skill", "En Başarılı Personalar"],
            ["En Önemli Yetenekleriniz"],
        ),
        # Case 5: All inputs are empty
        (
            "empty_df",
            "empty_high_quality_jobs",
            "no_ai_metadata",
            [],
            [
                "Bulunan İlanların Site Dağılımı",
                "En Popüler 5 Skill",
                "En Başarılı Personalar",
                "En Önemli Yetenekleriniz",
            ],
        ),
    ],
)
def test_log_summary_statistics_combinations(
    request,
    caplog,
    jobs_df_fixture,
    high_quality_jobs_fixture,
    ai_metadata_fixture,
    expected_sections,
    missing_sections,
):
    """Parametrized test for log_summary_statistics with different input combinations."""
    # Helper fixtures for parametrize
    fixtures = {
        "sample_jobs_df": request.getfixturevalue("sample_jobs_df"),
        "empty_df": pd.DataFrame(),
        "sample_high_quality_jobs": request.getfixturevalue("sample_high_quality_jobs"),
        "empty_high_quality_jobs": [],
        "sample_ai_metadata": request.getfixturevalue("sample_ai_metadata"),
        "no_ai_metadata": None,
    }

    jobs_df = fixtures[jobs_df_fixture]
    high_quality_jobs = fixtures[high_quality_jobs_fixture]
    ai_metadata = fixtures[ai_metadata_fixture]

    with caplog.at_level(logging.INFO):
        log_summary_statistics(jobs_df, high_quality_jobs, ai_metadata)

    # Check that expected sections are present
    for section in expected_sections:
        assert section in caplog.text, f"Expected section '{section}' not found"

    # Check that missing sections are not present
    for section in missing_sections:
        assert section not in caplog.text, f"Unexpected section '{section}' found"

    # Header should always be present
    assert "📊 Özet İstatistikler:" in caplog.text
