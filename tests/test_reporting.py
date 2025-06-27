import logging

import pandas as pd
import pytest

from src.reporting import display_results


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
    with caplog.at_level(logging.INFO, logger="src.reporting"):
        display_results(sample_jobs, 80)
    output = caplog.text
    assert "Software Engineer" in output
    assert "Great fit" in output  # Check for reasoning
    assert "Eşleşen: python" in output  # Check for matching keywords
    assert "DataCorp" in output
    assert "Uygunluk eşiği: %80 ve üzeri" in output
    assert "Persona Dağılımı" in output


def test_display_results_with_no_jobs(caplog):
    logging.raiseExceptions = False
    with caplog.at_level(logging.INFO, logger="src.reporting"):
        display_results([], 70)
    output = caplog.text
    assert "0 ilan bulundu" in output
