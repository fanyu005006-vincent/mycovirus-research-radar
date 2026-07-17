from curate.ranker import describe_importance, rank_papers
from generate.daily_report import build_daily_report, render_markdown
from scripts.daily_radar import assign_priority_category, is_recent_paper, is_virology_paper


def _papers():
    return [
        {
            "title": "A novel mycovirus causes hypovirulence in a plant pathogenic fungus",
            "abstract": "mycovirus hypovirulence biological control plant disease",
            "doi": "10.1000/myco.1",
            "year": 2026,
            "published_date": "2026-07-01",
            "citation_count": 20,
            "source": "pubmed",
            "topic_tags": ["hypovirulence-biocontrol"],
        },
        {
            "title": "An unrelated clinical report",
            "abstract": "clinical observations",
            "doi": "10.1000/other.1",
            "year": 2020,
            "published_date": "2020-01-01",
            "citation_count": 1,
            "source": "crossref",
            "topic_tags": ["other"],
        },
    ]


def test_describe_importance_levels():
    result = describe_importance({"total": 0.8, "relevance": 0.9, "recency": 1, "impact": 0.6, "novelty": 1})
    assert result["score"] == 80
    assert result["level"] == "S"
    assert result["reasons"]


def test_report_contains_ranked_sections():
    prefs = {
        "topics": {
            "hypovirulence-biocontrol": {
                "keywords": ["mycovirus hypovirulence biological control plant disease"],
                "weight": 1.0,
            }
        }
    }
    ranked = rank_papers(_papers(), prefs, [])
    report = build_daily_report(ranked, "2026-07-17")
    markdown = render_markdown(report)
    assert report["papers"][0]["title"].startswith("A novel mycovirus")
    assert report["papers"][0]["importance"]["score"] > report["papers"][1]["importance"]["score"]
    assert "# 病毒学研究文献周报" in markdown
    assert "## 重点必读" in markdown
    assert "## 全部文献" in markdown


def test_virology_gate_rejects_unrelated_broad_feed_records():
    assert is_virology_paper({"title": "A novel mycovirus in Fusarium"})
    assert is_virology_paper({"title": "Phage therapy against bacterial infection"})
    assert not is_virology_paper({"title": "Mitochondrial copper homeostasis in liver disease"})
    assert not is_virology_paper({"title": "Unrelated study", "abstract": None, "tldr": None})
    assert is_recent_paper({"year": 2026}, 2026, 2)
    assert is_recent_paper({"year": 2025}, 2026, 2)
    assert not is_recent_paper({"year": 2024}, 2026, 2)


def test_subject_priority_order():
    myco = assign_priority_category({"topic_tags": ["human-viruses", "mycoviruses"]})
    plant = assign_priority_category({"topic_tags": ["plant-viruses"]})
    animal = assign_priority_category({"topic_tags": ["animal-viruses"]})
    human = assign_priority_category({"topic_tags": ["human-viruses"]})
    assert [myco["priority_order"], plant["priority_order"], animal["priority_order"], human["priority_order"]] == [1, 2, 3, 4]
