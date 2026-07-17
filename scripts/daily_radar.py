"""Run the keyless daily search -> score -> report pipeline."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot.notifier import format_daily_push, send_push
from curate.ranker import rank_papers
from generate.daily_report import write_daily_report
from search.query_all import search_all


def _identity(paper: dict) -> str:
    doi = (paper.get("doi") or "").strip().lower()
    if doi:
        return f"doi:{doi}"
    title = " ".join((paper.get("title") or "").lower().split()).rstrip(".")
    return f"title:{title}"


def _load_history(data_dir: Path) -> list[dict]:
    path = data_dir / "papers.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


async def collect(profile: dict, per_topic: int) -> list[dict]:
    merged: dict[str, dict] = {}
    for key, topic in profile.get("topics", {}).items():
        if topic.get("blocked"):
            continue
        query = " ".join(topic.get("keywords", []))
        if not query:
            continue
        for paper in await search_all(query, top=per_topic):
            identity = _identity(paper)
            if identity in merged:
                tags = set(merged[identity].get("topic_tags", []))
                tags.add(key)
                merged[identity]["topic_tags"] = sorted(tags)
            else:
                item = dict(paper)
                item["topic_tags"] = [key]
                merged[identity] = item
    return list(merged.values())


async def run(args: argparse.Namespace) -> dict:
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    papers = await collect(profile, args.per_topic)
    weights = profile.get("ranking_weights", {})
    ranked = rank_papers(
        papers,
        {"topics": profile.get("topics", {})},
        _load_history(args.data_dir),
        w_relevance=weights.get("relevance", 0.55),
        w_recency=weights.get("recency", 0.20),
        w_impact=weights.get("impact", 0.15),
        w_novelty=weights.get("novelty", 0.10),
    )[: args.top]
    paths = write_daily_report(ranked, args.date, args.output_dir, top_n=args.top)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    pushed = False
    if token and chat_id and ranked:
        await send_push(token, chat_id, format_daily_push(args.date, ranked, os.getenv("SITE_URL", "")))
        pushed = True

    return {"collected": len(papers), "reported": len(ranked), "telegram_pushed": pushed, **paths}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build today's mycovirus research report")
    parser.add_argument("--profile", type=Path, default=ROOT / "profiles" / "mycovirus.json")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output" / "daily-reports")
    parser.add_argument("--date", default=datetime.now().astimezone().date().isoformat())
    parser.add_argument("--per-topic", type=int, default=20)
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
