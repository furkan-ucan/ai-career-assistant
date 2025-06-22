from src.embedding_service import EmbeddingService


class Dummy:
    def __init__(self):
        self.calls = 0


def test_custom_config_applied(monkeypatch):
    dummy = Dummy()

    def fake_embed_content(model, content, task_type=None):
        dummy.calls += 1
        return {"embedding": [0.0]}

    import src.embedding_service as es
    monkeypatch.setattr(es.genai, "embed_content", fake_embed_content)
    monkeypatch.setenv("GEMINI_API_KEY", "DUMMY")
    service = EmbeddingService(batch_size=5, retry_count=2, rate_limit_delay=0)
    service.create_embeddings_batch(["a", "b", "c"], batch_size=2)
    assert service.batch_size == 5
    assert service.retry_count == 2
    assert service.rate_limit_delay == 0
    assert dummy.calls == 3


def test_retry_logic(monkeypatch):
    call_count = {"n": 0}

    def fake_embed_content(model, content, task_type=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise Exception("fail")
        return {"embedding": [1.0]}

    import src.embedding_service as es
    monkeypatch.setattr(es.genai, "embed_content", fake_embed_content)
    monkeypatch.setattr(__import__("time"), "sleep", lambda x: None)
    monkeypatch.setenv("GEMINI_API_KEY", "DUMMY")
    service = EmbeddingService(retry_count=2, rate_limit_delay=0)
    emb = service.create_embedding("text")
    assert emb == [1.0]
    assert call_count["n"] == 2
