#!/usr/bin/env python3
"""OpenMOSS Unified Search — Grok deep search + OpenCLI detail enrichment.

Usage:
  python3 moss-search.py "关键词" [--mode auto|academic|social|news|all] [--detail] [--output path]
"""
import argparse
import json
import os
import subprocess
import sys

XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
GROK_MODEL = "grok-4.20-0309-reasoning"

ENRICHMENT_SOURCES = {
    "academic": [
        ("opencli arxiv search '{q}' -f json", "arXiv"),
        ("opencli google search 'site:scholar.google.com {q}' -f json", "Google Scholar"),
    ],
    "social": [
        ("opencli xiaohongshu search '{q}' -f json", "小红书"),
        ("opencli zhihu search '{q}' -f json", "知乎"),
        ("opencli reddit search '{q}' -f json", "Reddit"),
    ],
    "news": [
        ("opencli google news --query '{q}' -f json", "Google News"),
        ("opencli hackernews top --limit 10 -f json", "HackerNews"),
    ],
    "general": [
        ("opencli google search '{q}' -f json", "Google"),
        ("opencli youtube search '{q}' -f json", "YouTube"),
    ],
}


def grok_search(query: str, mode: str) -> str:
    """Use Grok Responses API with web_search tool."""
    import httpx

    system_prompts = {
        "auto": "You are a research assistant. Search the web and provide comprehensive, well-sourced answers with citations.",
        "academic": "You are an academic research assistant. Focus on peer-reviewed papers, preprints, and scholarly sources. Cite DOIs and paper titles.",
        "social": "You are a social media analyst. Search for user experiences, reviews, and community discussions.",
        "news": "You are a news analyst. Focus on recent news, industry developments, and trending topics.",
        "all": "You are a comprehensive research assistant. Search all available sources and synthesize findings.",
    }

    payload = {
        "model": GROK_MODEL,
        "input": [
            {"role": "system", "content": system_prompts.get(mode, system_prompts["auto"])},
            {"role": "user", "content": query},
        ],
        "tools": [{"type": "web_search"}],
    }

    client = httpx.Client(timeout=120)
    resp = client.post(
        "https://api.x.ai/v1/responses",
        headers={"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"},
        json=payload,
    )

    if resp.status_code != 200:
        return f"[Grok search failed: HTTP {resp.status_code}] {resp.text[:300]}"

    data = resp.json()

    content = ""
    citations = []

    output_items = data.get("output", [])
    for item in output_items:
        if item.get("type") == "message":
            for block in item.get("content", []):
                if block.get("type") == "output_text":
                    content += block.get("text", "")
                    for ann in block.get("annotations", []):
                        if ann.get("type") == "url_citation":
                            citations.append({"title": ann.get("title", ""), "url": ann.get("url", "")})

    if citations:
        content += "\n\n## Sources\n"
        seen = set()
        for c in citations:
            if c["url"] not in seen:
                seen.add(c["url"])
                content += f"- [{c['title']}]({c['url']})\n"

    return content


def opencli_enrich(query: str, sources: list) -> dict:
    results = {}
    for cmd_template, name in sources:
        cmd = cmd_template.replace("{q}", query.replace("'", "'\\''"))
        try:
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30,
                env={**os.environ, "DISPLAY": ":10"}
            )
            if proc.returncode == 0 and proc.stdout.strip():
                try:
                    data = json.loads(proc.stdout)
                    if data:
                        results[name] = data if isinstance(data, list) else [data]
                except json.JSONDecodeError:
                    if len(proc.stdout.strip()) > 20:
                        results[name] = proc.stdout.strip()[:2000]
        except (subprocess.TimeoutExpired, Exception):
            pass
    return results


def format_enrichment(enrichments: dict) -> str:
    if not enrichments:
        return ""
    parts = ["\n\n---\n## Enrichment Details\n"]
    for source, data in enrichments.items():
        parts.append(f"\n### {source}\n")
        if isinstance(data, str):
            parts.append(data[:1000])
        elif isinstance(data, list):
            for i, item in enumerate(data[:5]):
                if isinstance(item, dict):
                    title = item.get("title", item.get("name", f"Item {i+1}"))
                    desc = item.get("description", item.get("desc", item.get("content", "")))[:200]
                    url = item.get("url", item.get("link", ""))
                    parts.append(f"- **{title}**")
                    if desc:
                        parts.append(f"  {desc}")
                    if url:
                        parts.append(f"  [{url}]({url})")
                    parts.append("")
                else:
                    parts.append(f"- {str(item)[:200]}")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="OpenMOSS Unified Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--mode", default="auto", choices=["auto", "academic", "social", "news", "all"])
    parser.add_argument("--detail", action="store_true", help="Enrich with OpenCLI sources")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    if not XAI_API_KEY:
        print("ERROR: XAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print(f"[moss-search] Grok searching: {args.query} (mode={args.mode})", file=sys.stderr)
    result = grok_search(args.query, args.mode)

    if args.detail:
        print(f"[moss-search] Enriching with OpenCLI sources...", file=sys.stderr)
        if args.mode == "all":
            sources = []
            for v in ENRICHMENT_SOURCES.values():
                sources.extend(v)
        elif args.mode in ENRICHMENT_SOURCES:
            sources = ENRICHMENT_SOURCES[args.mode]
        else:
            sources = ENRICHMENT_SOURCES["general"]
        enrichments = opencli_enrich(args.query, sources)
        result += format_enrichment(enrichments)

    output = f"# Search: {args.query}\n\n**Mode:** {args.mode} | **Detail:** {'yes' if args.detail else 'no'}\n\n---\n\n{result}\n"

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[moss-search] Results written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
