# Standard Library
import time

# Third Party
import pandas as pd

# Local
from src.data_collector import collect_job_data


def test_concurrent_scraping(monkeypatch):
    call_times = []

    def fake_scrape_jobs(**kwargs):
        call_times.append(time.time())
        time.sleep(0.2)
        return pd.DataFrame(
            [
                {
                    "title": f"t-{kwargs['site_name']}",
                    "company": "c",
                    "location": "l",
                }
            ]
        )

    monkeypatch.setattr("src.data_collector.scrape_jobs", fake_scrape_jobs)
    start = time.time()
    df = collect_job_data("x", site_names=["a", "b"], max_results_per_site=1, hours_old=1)
    duration = time.time() - start
    assert len(df) == 2
    assert duration < 0.4
    assert max(call_times) - min(call_times) < 0.3
