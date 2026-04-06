"""
Generates Markdown and JSON reports from scan results.
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from detectors.base import Detection

CATEGORY_ORDER = ["LLM API", "Framework", "Vector DB", "Dev Tool", "Observability", "No-code"]

SIGNAL_EMOJI = {
    "dependency": "📦",
    "import": "📥",
    "env_var": "🔑",
    "config_file": "⚙️",
    "api_call": "🌐",
}


def build_summary(detections: list[Detection]) -> dict:
    """Deduplicate by tool and collect evidence."""
    tools: dict[str, dict] = {}
    for d in detections:
        if d.tool_id not in tools:
            tools[d.tool_id] = {
                "tool_id": d.tool_id,
                "label": d.label,
                "category": d.category,
                "signals": [],
            }
        tools[d.tool_id]["signals"].append({
            "type": d.signal_type,
            "detail": d.signal,
            "file": d.file,
            "line": d.line,
        })
    return tools


def to_json(detections: list[Detection], scan_root: str) -> str:
    summary = build_summary(detections)
    payload = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "scanned_path": scan_root,
        "tool_count": len(summary),
        "tools": list(summary.values()),
    }
    return json.dumps(payload, indent=2)


def to_markdown(detections: list[Detection], scan_root: str) -> str:
    summary = build_summary(detections)

    if not summary:
        return (
            f"# AI Connector Hub — Scan Report\n\n"
            f"**Scanned:** `{scan_root}`  \n"
            f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"> No AI tools detected.\n"
        )

    # Group by category
    by_category: dict[str, list] = defaultdict(list)
    for tool in summary.values():
        by_category[tool["category"]].append(tool)

    lines = [
        "# AI Connector Hub — Scan Report\n",
        f"**Scanned:** `{scan_root}`  ",
        f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Tools found:** {len(summary)}\n",
    ]

    # Summary table
    lines.append("## Summary\n")
    lines.append("| Tool | Category | Signals |")
    lines.append("|------|----------|---------|")
    for cat in CATEGORY_ORDER:
        for tool in sorted(by_category.get(cat, []), key=lambda t: t["label"]):
            types = sorted({s["type"] for s in tool["signals"]})
            badge = " ".join(f"{SIGNAL_EMOJI.get(t, '')} {t}" for t in types)
            lines.append(f"| **{tool['label']}** | {cat} | {badge} |")
    # Any categories not in our order
    for cat, tools in by_category.items():
        if cat not in CATEGORY_ORDER:
            for tool in sorted(tools, key=lambda t: t["label"]):
                types = sorted({s["type"] for s in tool["signals"]})
                badge = " ".join(f"{SIGNAL_EMOJI.get(t, '')} {t}" for t in types)
                lines.append(f"| **{tool['label']}** | {cat} | {badge} |")

    # Detail sections by category
    lines.append("\n## Details\n")
    for cat in CATEGORY_ORDER:
        tools_in_cat = sorted(by_category.get(cat, []), key=lambda t: t["label"])
        if not tools_in_cat:
            continue
        lines.append(f"### {cat}\n")
        for tool in tools_in_cat:
            lines.append(f"#### {tool['label']}\n")
            # Dedupe signals: show each (type+detail+file) once
            seen_sigs = set()
            for s in tool["signals"]:
                sig_key = (s["type"], s["detail"], s["file"])
                if sig_key in seen_sigs:
                    continue
                seen_sigs.add(sig_key)
                emoji = SIGNAL_EMOJI.get(s["type"], "•")
                loc = f"`{s['file']}`" + (f" line {s['line']}" if s["line"] else "")
                lines.append(f"- {emoji} **{s['type']}** — `{s['detail']}` in {loc}")
            lines.append("")

    return "\n".join(lines)


def print_terminal(detections: list[Detection]) -> None:
    summary = build_summary(detections)
    if not summary:
        print("  No AI tools detected.")
        return

    by_category: dict[str, list] = defaultdict(list)
    for tool in summary.values():
        by_category[tool["category"]].append(tool)

    for cat in CATEGORY_ORDER:
        tools_in_cat = by_category.get(cat, [])
        if not tools_in_cat:
            continue
        print(f"\n  [{cat}]")
        for tool in sorted(tools_in_cat, key=lambda t: t["label"]):
            types = sorted({s["type"] for s in tool["signals"]})
            badges = "  ".join(f"{SIGNAL_EMOJI.get(t, '')} {t}" for t in types)
            print(f"    ✓ {tool['label']:<30} {badges}")
