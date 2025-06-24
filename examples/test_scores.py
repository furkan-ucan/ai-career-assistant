# Third Party
import yaml

# Local
from src.intelligent_scoring import IntelligentScoringSystem

with open("config.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
scoring = IntelligentScoringSystem(cfg)

# Test actual scores
test_titles = [
    "Senior Software Engineer",
    "Junior React Developer",
    "Sr. Data Scientist",
    "Entry Level Python Dev",
    "Architect",
]

for title in test_titles:
    total, details = scoring.score_job({"title": title, "description": ""})
    print(f'{title}: total={total}, title={details["title"]}')
