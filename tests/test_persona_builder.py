from src.persona_builder import build_dynamic_personas


def test_build_dynamic_personas_simple():
    titles = ["Business Analyst", "Data Analyst"]
    personas = build_dynamic_personas(titles)
    assert "Business_Analyst" in personas
    term = personas["Business_Analyst"]["term"]
    assert "Business Analyst" in term
    assert personas["Data_Analyst"]["hours_old"] == 72
