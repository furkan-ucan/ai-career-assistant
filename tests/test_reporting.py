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
            "match_score": 90.0,
            "source_site": "SiteA",
            "persona_source": "dev",
            "url": "http://job1",
        },
        {
            "title": "Data Scientist",
            "company": "DataCorp",
            "location": "Istanbul",
            "match_score": 85.0,
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
            "match_score": 85.5,
        },
        {
            "title": "Business Analyst",
            "company": "BizCorp",
            "persona_source": "analyst",
            "match_score": 78.2,
        },
        {
            "title": "Full Stack Developer",
            "company": "DevCorp",
            "persona_source": "developer",
            "match_score": 82.1,
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
    logging.raiseExceptions = False
    with caplog.at_level(logging.INFO, logger="src.reporting"):
        display_results(sample_jobs, 80)
    output = caplog.text
    assert "Software Engineer" in output
    assert "DataCorp" in output
    assert "%80" in output
    assert "Persona Dağılımı" in output


def test_display_results_with_no_jobs(caplog):
    logging.raiseExceptions = False
    with caplog.at_level(logging.INFO, logger="src.reporting"):
        display_results([], 70)
    output = caplog.text
    assert "0 ilan bulundu" in output
    assert "Eşiği düşürmeyi" in output


def test_log_summary_statistics_with_full_data(
    caplog, sample_jobs_df, sample_high_quality_jobs, sample_ai_metadata
):
    """Test log_summary_statistics with complete data."""
    with caplog.at_level(logging.INFO):
        log_summary_statistics(sample_jobs_df, sample_high_quality_jobs, sample_ai_metadata)

    # Check header
    assert "📊 Özet İstatistikler:" in caplog.text

    # Check site distribution
    assert "🔹 Site Dağılımı:" in caplog.text
    assert "kariyer.net: 2 ilan" in caplog.text
    assert "yenibiris.com: 1 ilan" in caplog.text
    assert "linkedin: 1 ilan" in caplog.text

    # Check skill mentions (python, react, sql, typescript should be found)
    assert "🔹 Ana Yeteneklerin İlanlardaki Toplam Görünme Sayısı:" in caplog.text

    # Check persona success
    assert "🔹 En Başarılı Personalar:" in caplog.text
    assert "developer: 2 ilan" in caplog.text
    assert "analyst: 1 ilan" in caplog.text


def test_log_summary_statistics_empty_dataframe(caplog, sample_high_quality_jobs, sample_ai_metadata):
    """Test log_summary_statistics with empty DataFrame."""
    empty_df = pd.DataFrame()

    with caplog.at_level(logging.INFO):
        log_summary_statistics(empty_df, sample_high_quality_jobs, sample_ai_metadata)

    # Should still show header and persona info
    assert "📊 Özet İstatistikler:" in caplog.text
    assert "🔹 En Başarılı Personalar:" in caplog.text
    # But no site distribution
    assert "🔹 Site Dağılımı:" not in caplog.text


def test_log_summary_statistics_no_ai_metadata(caplog, sample_jobs_df, sample_high_quality_jobs):
    """Test log_summary_statistics without AI metadata."""
    with caplog.at_level(logging.INFO):
        log_summary_statistics(sample_jobs_df, sample_high_quality_jobs, None)

    assert "📊 Özet İstatistikler:" in caplog.text
    assert "🔹 Site Dağılımı:" in caplog.text
    assert "🔹 En Başarılı Personalar:" in caplog.text
    # No skill mentions without AI metadata
    assert "Ana Yeteneklerin İlanlardaki Toplam Görünme Sayısı:" not in caplog.text


def test_log_summary_statistics_empty_high_quality_jobs(caplog, sample_jobs_df, sample_ai_metadata):
    """Test log_summary_statistics with empty high-quality jobs."""
    with caplog.at_level(logging.INFO):
        log_summary_statistics(sample_jobs_df, [], sample_ai_metadata)

    assert "📊 Özet İstatistikler:" in caplog.text
    assert "🔹 Site Dağılımı:" in caplog.text
    assert "🔹 Ana Yeteneklerin İlanlardaki Toplam Görünme Sayısı:" in caplog.text
    # No persona success section
    assert "🔹 En Başarılı Personalar:" not in caplog.text


def test_log_summary_statistics_jobs_without_persona_source(caplog, sample_jobs_df, sample_ai_metadata):
    """Test log_summary_statistics with jobs that have no persona_source."""
    jobs_without_persona = [
        {"title": "Developer", "company": "Corp"},
        {"title": "Analyst", "company": "Biz"},
    ]

    with caplog.at_level(logging.INFO):
        log_summary_statistics(sample_jobs_df, jobs_without_persona, sample_ai_metadata)

    assert "📊 Özet İstatistikler:" in caplog.text
    assert "🔹 Site Dağılımı:" in caplog.text
    # No persona section since jobs don't have persona_source
    assert "🔹 En Başarılı Personalar:" not in caplog.text


def test_log_summary_statistics_missing_description_column(
    caplog, sample_high_quality_jobs, sample_ai_metadata
):
    """Test log_summary_statistics with DataFrame missing description column."""
    df_no_desc = pd.DataFrame({"source_site": ["kariyer.net", "yenibiris.com"], "title": ["Developer", "Analyst"]})

    with caplog.at_level(logging.INFO):
        log_summary_statistics(df_no_desc, sample_high_quality_jobs, sample_ai_metadata)

    assert "📊 Özet İstatistikler:" in caplog.text
    assert "🔹 Site Dağılımı:" in caplog.text
    assert "🔹 En Başarılı Personalar:" in caplog.text
    # No skill mentions without description column
    assert "Ana Yeteneklerin İlanlardaki Toplam Görünme Sayısı:" not in caplog.text


def test_log_summary_statistics_skill_counting(caplog, sample_ai_metadata):
    """Test that skill counting works correctly."""
    # Create DataFrame with known skill occurrences
    df_with_skills = pd.DataFrame(
        {
            "source_site": ["site1", "site2"],
            "description": [
                "Looking for Python developer with React skills",  # python: 1, react: 1
                "Python and SQL experience required",  # python: 1, sql: 1
            ],
        }
    )

    with caplog.at_level(logging.INFO):
        log_summary_statistics(df_with_skills, [], sample_ai_metadata)

    # Should find: python (2), react (1), sql (1), typescript (0) = 4 total
    assert "Ana Yeteneklerin İlanlardaki Toplam Görünme Sayısı: 4" in caplog.text


def test_log_summary_statistics_completely_empty_inputs(caplog):
    """Test log_summary_statistics with all empty inputs."""
    empty_df = pd.DataFrame()

    with caplog.at_level(logging.INFO):
        log_summary_statistics(empty_df, [], None)

    # Should only show header
    assert "📊 Özet İstatistikler:" in caplog.text
    # No other sections should appear
    assert "🔹 Site Dağılımı:" not in caplog.text
    assert "🔹 Ana Yeteneklerin İlanlardaki Toplam Görünme Sayısı:" not in caplog.text
    assert "🔹 En Başarılı Personalar:" not in caplog.text
