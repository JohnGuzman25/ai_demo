#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys, json, random
from datetime import datetime
from pathlib import Path

OUT_DIR = Path("outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def build_augmented_query(query: str, site: str | None, recency: int | None) -> str:
    hints = []
    if site:
        hints.append(f"Prioritize sources from {site} when relevant.")
    if recency:
        hints.append(f"Prefer sources published within the last {recency} days.")
    if hints:
        return f"{query}\n\nResearch hints: " + " ".join(hints)
    return query

def run_repo_cli(augmented_query: str, demo: bool = False) -> str:
    """If demo=True, use fake data instead of calling the API."""
    if demo:
        fake_sources = [
            "https://nasa.gov/ai-mars-rover",
            "https://nytimes.com/tech/ai-safety",
            "https://openai.com/research/updates"
        ]
        sample = random.choice(fake_sources)
        fake_output = (
            "### Simulated AI Web Search Result\n"
            f"Query: {augmented_query}\n\n"
            f"- Source: {sample}\n"
            "- Summary: AI systems are being applied to scientific and business problems, improving automation and data analysis.\n"
            f"- Date: {datetime.now().strftime('%Y-%m-%d')}\n"
        )
        return fake_output
    else:
        # real mode (if you ever add an API key)
        cmd = ["python", "-m", "src.main", augmented_query]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return proc.stdout

def export_report(query: str, augmented_query: str, output: str, fmt: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    if fmt == "json":
        path = OUT_DIR / f"report-{ts}.json"
        data = {"query": query, "augmented_query": augmented_query, "output": output}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(path)
    path = OUT_DIR / f"report-{ts}.md"
    md = []
    md.append(f"# Search Report\n")
    md.append(f"**Query:** {query}\n")
    if augmented_query != query:
        md.append("**Augmented Query Hints:**\n")
        md.append("```\n" + augmented_query + "\n```\n")
    md.append("## Output\n")
    md.append("```\n" + output.strip() + "\n```\n")
    path.write_text("\n".join(md), encoding="utf-8")
    return str(path)

def append_to_log(query: str, site: str | None, recency: int | None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] Query: {query}"
    if site:
        line += f" | site={site}"
    if recency:
        line += f" | recency={recency}d"
    (OUT_DIR / "query_log.txt").open("a", encoding="utf-8").write(line + "\n")

def summarize_output(output: str, style: str) -> str:
    lines = output.strip().splitlines()
    if style == "short":
        return "\n".join(lines[:10])
    elif style == "detailed":
        return output
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Demo CLI (works offline in --demo mode)")
    parser.add_argument("query", type=str, help="Your research question")
    parser.add_argument("--site", type=str, help="Domain hint, e.g. nytimes.com or nasa.gov")
    parser.add_argument("--recency", type=int, help="Prefer sources within N days")
    parser.add_argument("--export", choices=["md","json"], help="Export results to outputs/")
    parser.add_argument("--summary", choices=["short","detailed"], help="Choose summary length")
    parser.add_argument("--log", action="store_true", help="Save query to outputs/query_log.txt")
    parser.add_argument("--demo", action="store_true", help="Run without OpenAI API (offline mode)")
    args = parser.parse_args()

    augmented = build_augmented_query(args.query, args.site, args.recency)
    output = run_repo_cli(augmented, demo=args.demo)

    if args.summary:
        output = summarize_output(output, args.summary)

    print(output)

    if args.export:
        path = export_report(args.query, augmented, output, args.export)
        print(f"\nSaved report → {path}")

    if args.log:
        append_to_log(args.query, args.site, args.recency)
        print("Logged query to outputs/query_log.txt")
