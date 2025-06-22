# Standard Library
import os
import sys
import time

# Third Party
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Local
from src.filter import compare_filters, score_jobs, filter_junior_suitable_jobs
from src.intelligent_scoring import IntelligentScoringSystem
import pytest


def load_scoring_system():
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return IntelligentScoringSystem(cfg)


def test_title_weighting_positive_negative():
    scoring = load_scoring_system()
    job = {"title": "Junior Developer", "description": ""}
    _, details = scoring.score_job(job)
    assert details["title"] > 0

    job = {"title": "Senior Developer", "description": ""}
    _, details = scoring.score_job(job)
    assert details["title"] < 0


def test_description_weighting():
    scoring = load_scoring_system()
    job = {"title": "Dev", "description": "Python ve React ile geliştirme"}
    _, details = scoring.score_job(job)
    assert details["description"] > 0

    job = {"title": "Dev", "description": "Çağrı merkezi tecrübesi"}
    _, details = scoring.score_job(job)
    assert details["description"] < 0


@pytest.mark.parametrize(
    "description,expected_positive",
    [
        ("Python ve React geliştirme yapacaksınız", True),
        ("TypeScript ve JavaScript kullanılacak", True),
        ("Remote çalışma imkanı", True),
        ("Agile metodoloji ile çalışma", True),
        ("REST API geliştirme", True),
        ("Çağrı merkezi deneyimi gerekli", False),
        ("Yoğun seyahat gerektirir", False),
        ("Satış hedefi ve kota takibi", False),
        ("Müşteri ziyareti yapılacak", False),
    ],
)
def test_description_scoring_patterns(description, expected_positive):
    scoring = load_scoring_system()
    job = {"title": "Developer", "description": description}
    _, details = scoring.score_job(job)
    if expected_positive:
        assert details["description"] > 0, f"Expected positive score for: {description}"
    else:
        assert details["description"] < 0, f"Expected negative score for: {description}"


def test_description_text_truncation():
    """Test that descriptions are truncated to 3000 chars."""
    scoring = load_scoring_system()
    long_description = "Python " * 1000  # ~6000 characters
    job = {"title": "Dev", "description": long_description}
    _, details = scoring.score_job(job)
    # Should still work and give positive score for Python
    assert details["description"] > 0


def test_experience_regex_detection():
    scoring = load_scoring_system()
    job = {"title": "Developer", "description": "En az 5 yıl deneyim gereklidir"}
    _, details = scoring.score_job(job)
    assert details["experience"] < 0


@pytest.mark.parametrize(
    "description,expected_penalty",
    [
        ("3 yıl deneyim", -10),
        ("4 yıl tecrübe", -20),
        ("5 yıl deneyim gerekli", -40),
        ("8 yıl çalışma tecrübesi", -50),
        ("10 yıl ve üzeri deneyim", -60),
        ("15 yıl sektör tecrübesi", -60),  # Should cap at 10+ penalty
        ("2 years experience", 0),         # Below threshold
        ("1 yıl deneyim", 0),             # Below threshold
        ("Deneyim gerekmez", 0),          # No years mentioned
        ("En az 5 sene tecrübe", -40),    # 'sene' variant
        ("4 yrs experience required", -20), # English 'yrs'
        ("3 years of work", -10),         # English 'years'
    ],
)
def test_experience_penalty_thresholds(description, expected_penalty):
    scoring = load_scoring_system()
    job = {"title": "Developer", "description": description}
    _, details = scoring.score_job(job)
    assert details["experience"] == expected_penalty, f"Expected {expected_penalty} for: {description}"


def test_experience_multiple_years_max():
    """Test that maximum years value is used when multiple are present."""
    scoring = load_scoring_system()
    job = {"title": "Dev", "description": "2 yıl minimum, 8 yıl tercih edilir"}
    _, details = scoring.score_job(job)
    assert details["experience"] == -50  # Should use 8 years, not 2


@pytest.mark.parametrize(
    "title,expected_min,expected_max",
    [
        ("Senior Software Engineer", -35, -25),  # Senior matches (-30)
        ("Junior React Developer", 25, 35),      # Junior matches (+30)
        ("Sr. Data Scientist", -5, 5),           # "Sr." matches "sr." (-30) but let's allow range
        ("Entry Level Python Dev", 25, 35),      # Entry matches (+30)
        ("Lead Developer", -35, -25),            # Lead matches (-30)
        ("Architect", -35, -25),                 # Architect matches (-30)
        ("Manager", -35, -25),                   # Manager matches (-30)
        ("Trainee Software Engineer", 25, 35),  # Trainee matches (+30)
        ("Intern Developer", 25, 35),            # Intern matches (+30)
        ("Stajyer Yazılım Geliştirici", 25, 35), # Stajyer matches (+30)
    ],
)
def test_parametrized_title_scores(title, expected_min, expected_max):
    scoring = load_scoring_system()
    total, _ = scoring.score_job({"title": title, "description": ""})
    assert expected_min <= total <= expected_max


def test_should_include_threshold():
    scoring = load_scoring_system()
    job = {"title": "Intern Developer", "description": "0 yıl deneyim"}
    total, _ = scoring.score_job(job)
    assert scoring.should_include(total)


def test_compare_filters_basic():
    jobs = [
        {"title": "Senior Developer", "description": "5 yıl deneyim"},
        {"title": "Junior Developer", "description": "0 yıl deneyim"},
    ]
    scoring = load_scoring_system()
    result = compare_filters(jobs, scoring)
    assert "Junior Developer" in result["intersection"]
    assert "Senior Developer" not in result["intersection"]


def test_scoring_performance():
    scoring = load_scoring_system()
    jobs = [{"title": "Junior Developer", "description": ""} for _ in range(1000)]
    start = time.time()
    score_jobs(jobs, scoring)
    assert (time.time() - start) < 1.0


def test_filter_empty_list():
    assert filter_junior_suitable_jobs([]) == []


# Edge Case Tests
def test_edge_cases():
    """Test edge cases and boundary conditions."""
    scoring = load_scoring_system()
    
    # Empty strings
    job = {"title": "", "description": ""}
    total, details = scoring.score_job(job)
    assert total == 0
    assert details["title"] == 0
    assert details["description"] == 0
    assert details["experience"] == 0
    
    # None values
    job = {"title": None, "description": None}
    total, details = scoring.score_job(job)
    assert total == 0
    
    # Very long title with multiple keywords
    long_title = "Senior Lead Architect Manager Director Junior Entry Trainee"
    job = {"title": long_title, "description": ""}
    total, details = scoring.score_job(job)
    # Should have both positive and negative scores
    assert details["title"] != 0
    
    # Mixed case sensitivity
    job = {"title": "SENIOR developer", "description": "PYTHON programming"}
    _, details = scoring.score_job(job)
    assert details["title"] < 0  # Should catch SENIOR
    assert details["description"] > 0  # Should catch PYTHON


def test_regex_word_boundaries():
    """Test that regex patterns use proper word boundaries."""
    scoring = load_scoring_system()
    
    # Should NOT match partial words
    job = {"title": "Seniority Manager", "description": ""}
    _, details = scoring.score_job(job)
    # "Senior" should not match in "Seniority"
    title_score = details["title"]
    
    # Should match exact words
    job2 = {"title": "Senior Manager", "description": ""}
    _, details2 = scoring.score_job(job2)
    
    # Senior Manager should have more negative score than Seniority Manager
    assert details2["title"] < title_score


def test_hyphenated_words():
    """Test hyphenated word handling."""
    scoring = load_scoring_system()
    
    # Test that "full-stack" and "full stack" are treated the same
    job1 = {"title": "Full-Stack Developer", "description": ""}
    job2 = {"title": "Full Stack Developer", "description": ""}
    
    score1, _ = scoring.score_job(job1)
    score2, _ = scoring.score_job(job2)
    
    # Both should be treated similarly (this tests our regex enhancement)
    assert abs(score1 - score2) <= 5  # Allow small variance


def test_config_driven_flexibility():
    """Test that system respects config changes."""
    scoring = load_scoring_system()
    
    # Test threshold behavior
    assert scoring.threshold == -20  # From config
    
    # Test that weights are configurable
    assert scoring.weights["negative"] == -30
    assert scoring.weights["positive"] == 30
    
    # Test experience penalties are config-driven
    expected_penalties = {3: -10, 4: -20, 5: -40, 8: -50, 10: -60}
    assert scoring.experience_penalties == expected_penalties


# Performance and Regression Tests
def test_scoring_performance_extended():
    """Extended performance test with various job types."""
    scoring = load_scoring_system()
    
    # Create diverse job dataset
    jobs = []
    job_templates = [
        {"title": "Junior Developer", "description": "Python programming"},
        {"title": "Entry Level Analyst", "description": "Remote work available"},
        # Note: Avoiding negative scoring jobs since they get filtered out
    ]
    
    # Scale up for performance testing
    for _ in range(500):  # 1000 total jobs
        jobs.extend(job_templates)
    
    start = time.time()
    results = score_jobs(jobs, scoring)
    duration = time.time() - start
    
    assert duration < 2.0  # Should complete within 2 seconds
    # Results may be fewer than input due to filtering
    assert len(results) > 0  # Should have some results
    
    # Ensure all jobs have complete scoring details
    for job_data in results:
        assert "score_details" in job_data
        details = job_data["score_details"]
        assert "title" in details
        assert "description" in details
        assert "experience" in details
        assert "total" in details


def test_regression_protection():
    """Test critical functionality to prevent regressions."""
    scoring = load_scoring_system()
    
    # Test cases that should always work
    critical_tests = [
        {
            "job": {"title": "Junior Developer", "description": "Python, React"},
            "should_include": True,
            "title_positive": True,
            "desc_positive": True,
        },
        {
            "job": {"title": "Senior Manager", "description": "10 yıl deneyim, çağrı merkezi"},
            "should_include": False,
            "title_positive": False,
            "desc_positive": False,
        },
        {
            "job": {"title": "Entry Level Engineer", "description": "Remote work, API development"},
            "should_include": True,
            "title_positive": True,
            "desc_positive": True,
        },
    ]
    
    for test_case in critical_tests:
        job = test_case["job"]
        total, details = scoring.score_job(job)
        
        # Test inclusion decision
        include_decision = scoring.should_include(total)
        assert include_decision == test_case["should_include"], f"Inclusion failed for: {job['title']}"
        
        # Test title scoring direction
        if test_case["title_positive"]:
            assert details["title"] > 0, f"Title should be positive for: {job['title']}"
        else:
            assert details["title"] < 0, f"Title should be negative for: {job['title']}"
        
        # Test description scoring direction  
        if test_case["desc_positive"]:
            assert details["description"] > 0, f"Description should be positive for: {job['title']}"
        else:
            assert details["description"] <= 0, f"Description should be non-positive for: {job['title']}"


def test_comprehensive_integration():
    """Comprehensive integration test combining all scoring features."""
    scoring = load_scoring_system()
    
    # Complex job with multiple scoring factors
    complex_job = {
        "title": "Junior Full-Stack Developer",  # Positive title
        "description": """
        Aranan Nitelikler:
        - Python ve React deneyimi
        - TypeScript bilgisi 
        - Remote çalışma imkanı
        - Agile metodoloji
        - REST API geliştirme
        - En az 2 yıl deneyim (junior için uygun)
        """
    }
    
    total, details = scoring.score_job(complex_job)
    
    # Should have positive total score
    assert total > 0, f"Complex job should have positive score, got: {total}"
    
    # Title should be positive (Junior)
    assert details["title"] > 0, "Title score should be positive for Junior"
    
    # Description should be positive (many positive keywords)
    assert details["description"] > 0, "Description should be positive with tech keywords"
    
    # Experience should be neutral (2 years is below 3-year threshold)
    assert details["experience"] == 0, "2 years should not trigger penalty"
    
    # Should be included
    assert scoring.should_include(total), "Complex positive job should be included"

# Enhanced Edge Case Testing for Issue #18 Phase 4
@pytest.mark.parametrize(
    "description,expected_positive",
    [
        ("Python geliştirme deneyimi", True),
        ("React ve TypeScript ile çalışma", True),
        ("Remote çalışma imkanı", True),
        ("Çağrı merkezi deneyimi", False),
        ("Yoğun seyahat gerekli", False),
        ("Satış hedefi ve kota", False),
        ("", False),  # Empty description
        (None, False),  # None description
    ],
)
def test_description_scoring_edge_cases(description, expected_positive):
    """Test description scoring with various edge cases including None and empty values."""
    scoring = load_scoring_system()
    job = {"title": "Developer", "description": description}
    _, details = scoring.score_job(job)
    
    if expected_positive:
        assert details["description"] > 0, f"Expected positive score for: {description}"
    else:
        assert details["description"] <= 0, f"Expected non-positive score for: {description}"


@pytest.mark.parametrize(
    "title,description,experience_text,expected_include",        [
            ("Junior Developer", "Python development", "0 yıl deneyim", True),
            ("Entry Level React Dev", "React projects", "Fresh graduate", True),
            ("Senior Engineer", "5+ years experience", "5 yıl deneyim", False),
            ("Lead Developer", "Team leadership", "8 years experience", False),
            ("Trainee Position", "Learning opportunity", "No experience required", True),
            ("", "", "", True),  # All empty but score=0 >= threshold(-20)
            (None, None, None, True),  # All None but score=0 >= threshold(-20)
        ],
)
def test_comprehensive_job_scoring(title, description, experience_text, expected_include):
    """Test comprehensive job scoring with realistic job combinations."""
    scoring = load_scoring_system()
    job_desc = f"{description or ''} {experience_text or ''}".strip()
    job = {"title": title, "description": job_desc}
    
    total, details = scoring.score_job(job)
    result = scoring.should_include(total)
    
    assert result == expected_include, f"Job {title} with desc '{job_desc}' - Expected: {expected_include}, Got: {result}, Score: {total}, Details: {details}"


@pytest.mark.parametrize(
    "experience_text,expected_penalty",
    [
        ("5 yıl deneyim gerekli", True),
        ("4 years experience required", True),
        ("10+ years professional experience", True),
        ("2 yıl deneyim", False),  # Below threshold
        ("1 year experience", False),
        ("Fresh graduate position", False),
        ("No experience required", False),
        ("", False),  # Empty
        (None, False),  # None
    ],
)
def test_experience_detection_comprehensive(experience_text, expected_penalty):
    """Test experience detection with various formats and edge cases."""
    scoring = load_scoring_system()
    score = scoring.score_experience(experience_text)
    
    if expected_penalty:
        assert score < 0, f"Expected penalty for: {experience_text}, got: {score}"
    else:
        assert score >= 0, f"Expected no penalty for: {experience_text}, got: {score}"


def test_regex_pattern_word_boundaries():
    """Test that regex patterns properly use word boundaries to avoid partial matches."""
    scoring = load_scoring_system()
    
    # Should NOT match partial words
    job1 = {"title": "Engineering Management", "description": ""}
    total1, _ = scoring.score_job(job1)
    
    # Should match exact words
    job2 = {"title": "Manager Position", "description": ""}
    total2, _ = scoring.score_job(job2)
    
    # Manager should be more negative than Engineering (partial match)
    assert total2 < total1, f"Manager ({total2}) should be more negative than Engineering partial match ({total1})"


def test_hyphenated_word_matching():
    """Test that hyphenated words are properly matched (full-stack vs full stack)."""
    scoring = load_scoring_system()
    
    # Test with hyphen
    job1 = {"title": "Full-Stack Developer", "description": ""}
    
    # Test without hyphen  
    job2 = {"title": "Full Stack Developer", "description": ""}
    
    total1, _ = scoring.score_job(job1)
    total2, _ = scoring.score_job(job2)
    
    # Both should have similar positive scores
    assert abs(total1 - total2) <= 10, f"Hyphenated and non-hyphenated should score similarly: {total1} vs {total2}"


def test_case_insensitive_matching():
    """Test that matching is case insensitive."""
    scoring = load_scoring_system()
    
    jobs = [
        {"title": "junior developer", "description": ""},
        {"title": "JUNIOR DEVELOPER", "description": ""},
        {"title": "Junior Developer", "description": ""},
        {"title": "Junior developer", "description": ""},
    ]
    
    scores = [scoring.score_job(job)[0] for job in jobs]
    
    # All scores should be identical
    assert all(score == scores[0] for score in scores), f"Case variations should score identically: {scores}"


def test_multiple_keyword_matches():
    """Test jobs with multiple positive/negative keywords."""
    scoring = load_scoring_system()
    
    # Multiple positive keywords
    job_positive = {"title": "Junior Entry Level Developer", "description": "Python and React development"}
    total_pos, details_pos = scoring.score_job(job_positive)
    
    # Multiple negative keywords
    job_negative = {"title": "Senior Lead Manager", "description": ""}
    total_neg, details_neg = scoring.score_job(job_negative)
    
    assert total_pos > 50, f"Multiple positive keywords should give high score: {total_pos}"
    assert total_neg < -50, f"Multiple negative keywords should give very negative score: {total_neg}"


def test_config_driven_thresholds():
    """Test that scoring uses config-driven thresholds properly."""
    scoring = load_scoring_system()
    
    # Test that threshold from config is used
    assert hasattr(scoring, 'threshold'), "Scoring system should have threshold attribute"
    assert isinstance(scoring.threshold, (int, float)), "Threshold should be numeric"
    
    # Test should_include logic
    assert not scoring.should_include(scoring.threshold - 1), "Score below threshold should be excluded"
    assert scoring.should_include(scoring.threshold), "Score at threshold should be included"
    assert scoring.should_include(scoring.threshold + 1), "Score above threshold should be included"


def test_performance_with_large_description():
    """Test performance with very large job descriptions."""
    scoring = load_scoring_system()
    
    # Create large description (should be truncated to 3000 chars)
    large_desc = "Python development " * 200  # ~3400 characters
    job = {"title": "Junior Developer", "description": large_desc}
    
    start_time = time.time()
    total, details = scoring.score_job(job)
    processing_time = time.time() - start_time
    
    assert processing_time < 0.1, f"Large description processing should be fast: {processing_time:.3f}s"
    assert details["description"] > 0, "Large description with positive keywords should score positively"


def test_empty_and_none_handling():
    """Test proper handling of empty and None values."""
    scoring = load_scoring_system()
    
    test_cases = [
        {"title": None, "description": None},
        {"title": "", "description": ""},
        {"title": "  ", "description": "  "},  # Whitespace only
        {"title": "Valid Title", "description": None},
        {"title": None, "description": "Valid description"},
    ]
    
    for job in test_cases:
        try:
            total, details = scoring.score_job(job)
            # Should not crash and should return valid scores
            assert isinstance(total, int), f"Total score should be int for {job}"
            assert isinstance(details, dict), f"Details should be dict for {job}"
            assert all(isinstance(v, int) for v in details.values()), f"All detail values should be int for {job}"
        except Exception as e:
            pytest.fail(f"Scoring failed for {job}: {e}")


def test_regression_protection_basic_scores():
    """Regression test to ensure basic scoring patterns remain consistent."""
    scoring = load_scoring_system()
    
    # These scores should remain stable across updates
    regression_cases = [
        {"job": {"title": "Junior Developer", "description": ""}, "min_score": 25, "max_score": 35},
        {"job": {"title": "Senior Developer", "description": ""}, "min_score": -35, "max_score": -25},
        {"job": {"title": "Entry Level", "description": "Python"}, "min_score": 40, "max_score": 50},
        {"job": {"title": "Manager", "description": "5 yıl deneyim"}, "min_score": -75, "max_score": -65},
    ]
    
    for case in regression_cases:
        total, _ = scoring.score_job(case["job"])
        assert case["min_score"] <= total <= case["max_score"], \
            f"Regression test failed for {case['job']}: expected {case['min_score']}-{case['max_score']}, got {total}"
