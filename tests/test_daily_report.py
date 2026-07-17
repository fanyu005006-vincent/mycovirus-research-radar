from curate.ranker import describe_importance, rank_papers
from generate.daily_report import build_daily_report, render_markdown


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
    assert "# 真菌病毒科研日报" in markdown
    assert "## 重点必读" in markdown
    assert "## 全部文献" in markdown
