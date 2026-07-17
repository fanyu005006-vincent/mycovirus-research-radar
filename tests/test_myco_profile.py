import json
from pathlib import Path


def test_mycovirus_profile_is_valid_and_weights_sum_to_one():
    root = Path(__file__).resolve().parents[1]
    profile = json.loads((root / "profiles" / "mycovirus.json").read_text(encoding="utf-8"))

    assert len(profile["topics"]) >= 5
    assert all(topic["keywords"] for topic in profile["topics"].values())
    assert any(
        "mycovirus" in keyword.lower()
        for topic in profile["topics"].values()
        for keyword in topic["keywords"]
    )
    assert abs(sum(profile["ranking_weights"].values()) - 1.0) < 1e-9
    assert profile["paper_count"]["value"] > 0
