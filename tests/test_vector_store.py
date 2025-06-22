# Standard Library
import os
import sys
import tempfile

# Third Party
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Local
from src.vector_store import VectorStore


def test_stable_job_id_consistency():
    job = {"title": "Dev", "description": "desc"}
    vs = VectorStore()
    first = vs._stable_job_id(job)
    second = vs._stable_job_id(job)
    assert first == second


def test_stable_job_id_uses_url():
    job1 = {"title": "Dev", "description": "desc", "url": "http://example.com/1"}
    job2 = {"title": "Dev", "description": "desc", "url": "http://example.com/1", "persona_source": "A"}
    vs = VectorStore()
    assert vs._stable_job_id(job1) == vs._stable_job_id(job2)


def test_duplicate_detection_across_runs():
    job = {"title": "Dev", "description": "desc"}
    df = pd.DataFrame([job])
    embeddings = [[0.0, 0.0, 0.0]]

    with tempfile.TemporaryDirectory() as tmpdir:
        # First run
        vs1 = VectorStore(persist_directory=tmpdir)
        vs1.add_jobs(df, embeddings)
        count1 = vs1.get_stats()["total_jobs"]
        assert count1 == 1

        # Simulate new run with same storage
        vs2 = VectorStore(persist_directory=tmpdir)
        vs2.add_jobs(df, embeddings)
        count2 = vs2.get_stats()["total_jobs"]
        assert count2 == 1
