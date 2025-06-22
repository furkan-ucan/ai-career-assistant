from src.filter import filter_junior_suitable_jobs


def test_senior_jobs_filtered_junior_jobs_kept():
    jobs = [
        {"title": "Senior Developer", "description": "5+ yıl deneyim, takım yönetimi"},
        {"title": "Junior Developer", "description": "0 yıl deneyim"},
    ]
    filtered = filter_junior_suitable_jobs(jobs)
    titles = [j["title"] for j in filtered]
    assert "Junior Developer" in titles
    assert "Senior Developer" not in titles
