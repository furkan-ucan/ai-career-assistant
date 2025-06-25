import logging

import pytest

from src.reporting import display_results


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
