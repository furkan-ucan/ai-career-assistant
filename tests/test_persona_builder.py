import pytest

from src.persona_builder import _generate_unique_key, build_dynamic_personas


def test_build_dynamic_personas_simple():
    titles = ["Business Analyst", "Data Analyst"]
    personas = build_dynamic_personas(titles)
    assert "business_analyst" in personas
    term = personas["business_analyst"]["term"]
    assert isinstance(term, str)
    assert "Business Analyst" in term
    assert personas["data_analyst"]["hours_old"] == 72


@pytest.mark.parametrize(
    "titles,expected",
    [
        (["Junior GIS Specialist"], 20),
        (["React Developer"], 30),
        (["Chief Executive Officer"], 20),
    ],
)
def test_dynamic_result_counts(titles, expected):
    personas = build_dynamic_personas(titles)
    # Use the production normalization logic
    key = _generate_unique_key(titles[0], set())
    assert personas[key]["results"] == expected
