"""Tests for the extracted _scrape_single_site function."""

from unittest.mock import patch

import pandas as pd
import pytest

from src.data_collector import _scrape_single_site


@pytest.fixture
def mock_job_data():
    """Sample job data for testing."""
    return pd.DataFrame(
        {
            "title": ["Python Developer", "Data Analyst"],
            "company": ["TechCorp", "DataCorp"],
            "location": ["Istanbul", "Ankara"],
        }
    )


@patch("src.data_collector.scrape_jobs")
@patch("src.data_collector.logger")
def test_scrape_single_site_success(mock_logger, mock_scrape_jobs, mock_job_data):
    """Test successful scraping from a single site."""
    mock_scrape_jobs.return_value = mock_job_data

    result = _scrape_single_site("indeed", "Python Developer", "Turkey", 50, 72)

    # Check that scrape_jobs was called with correct parameters
    mock_scrape_jobs.assert_called_once_with(
        site_name="indeed",
        search_term="Python Developer",
        location="Turkey",
        results_wanted=50,
        hours_old=72,
        country_indeed="Turkey",
    )

    # Check result
    assert result is not None
    assert len(result) == 2
    assert "source_site" in result.columns
    assert all(result["source_site"] == "indeed")

    # Check logging
    mock_logger.info.assert_any_call("\n--- Site 'indeed' için arama yapılıyor ---")
    mock_logger.info.assert_any_call("✅ 'indeed' sitesinden 2 ilan toplandı.")


@patch("src.data_collector.scrape_jobs")
@patch("src.data_collector.logger")
def test_scrape_single_site_linkedin_params(mock_logger, mock_scrape_jobs, mock_job_data):
    """Test LinkedIn-specific parameters."""
    mock_scrape_jobs.return_value = mock_job_data

    result = _scrape_single_site("linkedin", "Data Scientist", "Turkey", 30, 48)

    # Check LinkedIn-specific parameters
    mock_scrape_jobs.assert_called_once_with(
        site_name="linkedin",
        search_term="Data Scientist",
        location="Turkey",
        results_wanted=30,
        hours_old=48,
        linkedin_fetch_description=True,
    )

    assert result is not None
    assert all(result["source_site"] == "linkedin")


@patch("src.data_collector.scrape_jobs")
@patch("src.data_collector.logger")
def test_scrape_single_site_empty_result(mock_logger, mock_scrape_jobs):
    """Test handling of empty results."""
    mock_scrape_jobs.return_value = pd.DataFrame()  # Empty DataFrame

    result = _scrape_single_site("indeed", "Rare Job", "Turkey", 50, 72)

    assert result is None
    mock_logger.info.assert_any_call("ℹ️ 'indeed' sitesinden bu arama terimi için ilan bulunamadı.")


@patch("src.data_collector.scrape_jobs")
@patch("src.data_collector.logger")
def test_scrape_single_site_none_result(mock_logger, mock_scrape_jobs):
    """Test handling of None results."""
    mock_scrape_jobs.return_value = None

    result = _scrape_single_site("indeed", "Nonexistent Job", "Turkey", 50, 72)

    assert result is None
    mock_logger.info.assert_any_call("ℹ️ 'indeed' sitesinden bu arama terimi için ilan bulunamadı.")


@patch("src.data_collector.scrape_jobs")
@patch("src.data_collector.logger")
def test_scrape_single_site_exception(mock_logger, mock_scrape_jobs):
    """Test exception handling."""
    mock_scrape_jobs.side_effect = Exception("Connection error")

    result = _scrape_single_site("indeed", "Python Developer", "Turkey", 50, 72)

    assert result is None
    mock_logger.error.assert_called_once()
    error_call = mock_logger.error.call_args
    assert "Connection error" in str(error_call)
    assert "'indeed' sitesinden veri toplarken hata" in str(error_call)


@pytest.mark.parametrize(
    "site,expected_params",
    [
        ("indeed", {"country_indeed": "Turkey"}),
        ("linkedin", {"linkedin_fetch_description": True}),
        ("other_site", {}),
    ],
)
@patch("src.data_collector.scrape_jobs")
def test_scrape_single_site_params_by_site(mock_scrape_jobs, mock_job_data, site, expected_params):
    """Test that correct parameters are used for different sites."""
    mock_scrape_jobs.return_value = mock_job_data

    _scrape_single_site(site, "Test Job", "Turkey", 25, 24)

    expected_call_params = {
        "site_name": site,
        "search_term": "Test Job",
        "location": "Turkey",
        "results_wanted": 25,
        "hours_old": 24,
        **expected_params,
    }

    mock_scrape_jobs.assert_called_once_with(**expected_call_params)
