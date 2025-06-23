from src.persona_builder import build_dynamic_personas


def test_build_dynamic_personas_basic():
    titles = ["Python Developer", "Data Analyst"]
    personas = build_dynamic_personas(titles)
    assert "Python_Developer" in personas
    cfg = personas["Python_Developer"]
    assert "Python Developer" in cfg["term"]
    assert "-Senior" in cfg["term"]
    assert cfg["hours_old"] == 72
    assert cfg["results"] == 25
