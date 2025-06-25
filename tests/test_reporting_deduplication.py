"""Test the URL-based deduplication functionality in reporting module."""

from src.reporting import _deduplicate_jobs_by_url


def test_deduplicate_jobs_by_url_empty_list():
    """Test deduplication with empty job list."""
    result = _deduplicate_jobs_by_url([])
    assert result == []


def test_deduplicate_jobs_by_url_single_job():
    """Test deduplication with single job."""
    jobs = [{"title": "Software Engineer", "job_url": "https://example.com/job1", "fit_score": 85.0}]
    result = _deduplicate_jobs_by_url(jobs)
    assert len(result) == 1
    assert result[0] == jobs[0]


def test_deduplicate_jobs_by_url_no_duplicates():
    """Test deduplication with no duplicate URLs."""
    jobs = [
        {"title": "Software Engineer", "job_url": "https://example.com/job1", "fit_score": 85.0},
        {"title": "Data Analyst", "job_url": "https://example.com/job2", "fit_score": 90.0},
    ]
    result = _deduplicate_jobs_by_url(jobs)
    assert len(result) == 2
    # Should be sorted by score descending
    assert result[0]["fit_score"] == 90.0
    assert result[1]["fit_score"] == 85.0


def test_deduplicate_jobs_by_url_with_duplicates():
    """Test deduplication with duplicate URLs keeping highest score."""
    jobs = [
        {
            "title": "Software Engineer",
            "job_url": "https://example.com/job1",
            "fit_score": 85.0,
            "company": "Company A",
        },
        {
            "title": "Senior Software Engineer",
            "job_url": "https://example.com/job1",  # Same URL
            "fit_score": 92.0,
            "company": "Company A",
        },
        {"title": "Data Analyst", "job_url": "https://example.com/job2", "fit_score": 88.0},
    ]
    result = _deduplicate_jobs_by_url(jobs)
    assert len(result) == 2  # One duplicate removed

    # Should keep the higher scored job for duplicate URL
    job1_result = next(job for job in result if job["job_url"] == "https://example.com/job1")
    assert job1_result["fit_score"] == 92.0
    assert job1_result["title"] == "Senior Software Engineer"

    # Results should be sorted by score descending
    assert result[0]["fit_score"] == 92.0
    assert result[1]["fit_score"] == 88.0


def test_deduplicate_jobs_by_url_different_score_fields():
    """Test deduplication with different score field names."""
    jobs = [
        {
            "title": "Job 1",
            "job_url": "https://example.com/job1",
            "match_score": 85.0,  # Different score field
        },
        {
            "title": "Job 2",
            "job_url": "https://example.com/job1",  # Same URL
            "similarity_score": 90.0,  # Yet another score field
        },
    ]
    result = _deduplicate_jobs_by_url(jobs)
    assert len(result) == 1
    # Should keep the job with higher score (90.0)
    assert result[0]["similarity_score"] == 90.0
    assert result[0]["title"] == "Job 2"


def test_deduplicate_jobs_by_url_missing_urls():
    """Test deduplication with missing URLs."""
    jobs = [
        {
            "title": "Job 1",
            "job_url": "",  # Empty URL
            "fit_score": 85.0,
        },
        {
            "title": "Job 2",
            # Missing job_url field
            "fit_score": 90.0,
        },
        {"title": "Job 3", "job_url": "https://example.com/job3", "fit_score": 88.0},
    ]
    result = _deduplicate_jobs_by_url(jobs)
    # All should be kept as they have different/missing URLs
    assert len(result) == 3
    # Should be sorted by score
    assert result[0]["fit_score"] == 90.0
    assert result[1]["fit_score"] == 88.0
    assert result[2]["fit_score"] == 85.0


def test_deduplicate_jobs_by_url_multiple_duplicates():
    """Test deduplication with multiple sets of duplicate URLs."""
    jobs = [
        {"title": "Job A1", "job_url": "https://example.com/jobA", "fit_score": 85.0},
        {"title": "Job A2", "job_url": "https://example.com/jobA", "fit_score": 95.0},  # Higher
        {"title": "Job B1", "job_url": "https://example.com/jobB", "fit_score": 80.0},
        {"title": "Job B2", "job_url": "https://example.com/jobB", "fit_score": 75.0},  # Lower
        {"title": "Job C", "job_url": "https://example.com/jobC", "fit_score": 90.0},  # Unique
    ]
    result = _deduplicate_jobs_by_url(jobs)
    assert len(result) == 3  # 2 duplicates removed

    # Check correct jobs kept
    urls_and_scores = {job["job_url"]: job["fit_score"] for job in result}
    assert urls_and_scores["https://example.com/jobA"] == 95.0  # Higher score kept
    assert urls_and_scores["https://example.com/jobB"] == 80.0  # Higher score kept
    assert urls_and_scores["https://example.com/jobC"] == 90.0  # Unique

    # Check sorted by score descending
    assert result[0]["fit_score"] == 95.0
    assert result[1]["fit_score"] == 90.0
    assert result[2]["fit_score"] == 80.0


def test_deduplicate_jobs_by_url_edge_case_zero_scores():
    """Test deduplication with zero or missing scores."""
    jobs = [
        {"title": "Job 1", "job_url": "https://example.com/job1", "fit_score": 0.0},
        {"title": "Job 2", "job_url": "https://example.com/job1"},  # No score field
        {"title": "Job 3", "job_url": "https://example.com/job2", "fit_score": 85.0},
    ]
    result = _deduplicate_jobs_by_url(jobs)
    assert len(result) == 2

    # Job 1 should be kept over Job 2 (0.0 > missing score which defaults to 0)
    job1_result = next(job for job in result if job["job_url"] == "https://example.com/job1")
    assert job1_result["title"] == "Job 1"
    assert job1_result["fit_score"] == 0.0
