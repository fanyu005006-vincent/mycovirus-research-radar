"""Generate structured daily research reports from ranked papers."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def _paper_link(paper: dict) -> str:
    if paper.get("doi"):
        return f"https://doi.org/{paper['doi']}"
    return paper.get("open_access_url") or paper.get("url") or ""


def _normalized_paper(paper: dict, rank: int) -> dict:
    importance = paper.get("importance", {})
    scores = paper.get("_scores", {})
    return {
        "rank": rank,
        "title": paper.get("title", "Untitled"),
        "authors": paper.get("authors", []),
        "year": paper.get("year"),
        "journal": paper.get("journal") or paper.get("venue") or "",
        "doi": paper.get("doi", ""),
        "url": _paper_link(paper),
        "source": paper.get("source", "unknown"),
        "topics": paper.get("topic_tags", []),
        "priority_category": paper.get("priority_category", "其他病毒学"),
        "priority_order": paper.get("priority_order", 5),
        "importance": importance,
        "component_scores": {
            "relevance": round(float(scores.get("relevance", 0)) * 100, 1),
            "recency": round(float(scores.get("recency", 0)) * 100, 1),
            "impact": round(float(scores.get("impact", 0)) * 100, 1),
            "novelty": round(float(scores.get("novelty", 0)) * 100, 1),
        },
        "summary": paper.get("tldr") or paper.get("abstract", ""),
        "selection_reason": paper.get("review_reason", ""),
        "citation_count": paper.get("citation_count", 0) or 0,
    }


def build_daily_report(papers: list[dict], date: str, top_n: int = 10) -> dict:
    """Build a JSON-serializable report with summaries and grouped papers."""
    ranked = sorted(
        papers,
        key=lambda p: p.get("importance", {}).get("score", p.get("_scores", {}).get("total", 0) * 100),
        reverse=True,
    )[:top_n]
    items = [_normalized_paper(paper, rank) for rank, paper in enumerate(ranked, 1)]

    level_counts = Counter(item["importance"].get("level", "C") for item in items)
    source_counts = Counter(item["source"] for item in items)
    topic_groups: dict[str, list[int]] = defaultdict(list)
    for item in items:
        for topic in item["topics"] or ["uncategorized"]:
            topic_groups[topic].append(item["rank"])

    must_read = [item for item in items if item["importance"].get("level") in {"S", "A"}]
    return {
        "schema_version": "1.0",
        "date": date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "summary": {
            "paper_count": len(items),
            "must_read_count": len(must_read),
            "importance_distribution": dict(level_counts),
            "source_distribution": dict(source_counts),
            "topic_distribution": {key: len(value) for key, value in topic_groups.items()},
        },
        "must_read": must_read,
        "papers": items,
    }


def render_markdown(report: dict) -> str:
    """Render a concise Obsidian-friendly Markdown report."""
    summary = report["summary"]
    lines = [
        "---",
        f"date: {report['date']}",
        "type: virology-research-weekly",
        f"paper_count: {summary['paper_count']}",
        f"must_read_count: {summary['must_read_count']}",
        "tags: [病毒学, 科研热点, 科研周报]",
        "---",
        "",
        f"# 病毒学研究文献周报 · {report['date']}",
        "",
        "## 今日概览",
        "",
        f"共收录 **{summary['paper_count']}** 篇，其中 **{summary['must_read_count']}** 篇为重点必读/高度重要。",
        f"重要度分布：{', '.join(f'{k}: {v}' for k, v in summary['importance_distribution'].items()) or '无'}。",
        "",
        "## 重点必读",
        "",
    ]

    if not report["must_read"]:
        lines.append("今日暂无 S/A 级论文。")
    for item in report["must_read"]:
        imp = item["importance"]
        lines.extend([
            f"### {item['rank']}. [{item['title']}]({item['url']})" if item["url"] else f"### {item['rank']}. {item['title']}",
            "",
            f"- 重要度：**{imp.get('score', 0)} / 100 · {imp.get('level', 'C')}级 · {imp.get('label', '')}**",
            f"- 评分理由：{'；'.join(imp.get('reasons', []))}",
            f"- 分项：相关性 {item['component_scores']['relevance']}｜时效性 {item['component_scores']['recency']}｜影响力 {item['component_scores']['impact']}｜新颖性 {item['component_scores']['novelty']}",
        ])
        if item["summary"]:
            lines.append(f"- 摘要：{item['summary'][:500]}")
        lines.append("")

    lines.extend(["## 全部文献", ""])
    for item in report["papers"]:
        imp = item["importance"]
        title = f"[{item['title']}]({item['url']})" if item["url"] else item["title"]
        lines.append(f"{item['rank']}. **[{imp.get('level', 'C')} · {imp.get('score', 0)}]** {title}")
        if item["journal"] or item["year"]:
            lines.append(f"   - {item['journal']} {item['year'] or ''}".rstrip())
        if item["topics"]:
            lines.append(f"   - 主题：{', '.join(item['topics'])}")
        lines.append(f"   - 推送优先级：{item['priority_category']}（第 {item['priority_order']} 级）")
        lines.append("")

    lines.extend([
        "## 数据来源",
        "",
        ", ".join(f"{name}: {count}" for name, count in summary["source_distribution"].items()) or "无",
        "",
        "> 重要度是辅助筛选指标，不替代对实验设计、数据质量和原文的人工判断。",
    ])
    return "\n".join(lines)


def write_daily_report(papers: list[dict], date: str, output_dir: Path, top_n: int = 10) -> dict[str, str]:
    report = build_daily_report(papers, date, top_n=top_n)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{date}.json"
    markdown_path = output_dir / f"{date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a structured mycovirus daily report")
    parser.add_argument("--papers", required=True, help="Ranked paper JSON file")
    parser.add_argument("--date", required=True, help="Report date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default="output/daily-reports")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()
    papers = json.loads(Path(args.papers).read_text(encoding="utf-8"))
    print(json.dumps(write_daily_report(papers, args.date, Path(args.output_dir), args.top), ensure_ascii=False))


if __name__ == "__main__":
    main()
