#!/usr/bin/env python3
"""
AI Connector Hub — scanner
Detects every AI tool, model, and connector a team is using.

Usage:
  python scanner.py [PATH] [--format markdown|json|terminal] [--output FILE]
  python scanner.py --help
"""

import argparse
import sys
from pathlib import Path

from catalog import CATALOG
from detectors import ALL_DETECTORS
from reporter import to_json, to_markdown, print_terminal


def scan(root: Path) -> list:
    all_detections = []
    for DetectorClass in ALL_DETECTORS:
        detector = DetectorClass(root=root, catalog=CATALOG)
        detections = detector.detect()
        all_detections.extend(detections)
    return all_detections


def main():
    parser = argparse.ArgumentParser(
        description="Detect AI tools, models, and connectors used in a codebase.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scanner.py                        # scan current directory, terminal output
  python scanner.py /path/to/repo          # scan a specific repo
  python scanner.py --format markdown      # output Markdown report
  python scanner.py --format json          # output JSON (for CI/dashboards)
  python scanner.py --output report.md     # write report to file
        """,
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["terminal", "markdown", "json"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "--fail-on-new",
        metavar="BASELINE",
        help="Exit non-zero if new tools appear vs a previous JSON report (for CI gates)",
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"Error: path does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    print(f"\n  Scanning: {root}", file=sys.stderr)
    print(f"  Detectors: {', '.join(d.name for d in ALL_DETECTORS)}\n", file=sys.stderr)

    detections = scan(root)

    # ── Render output ────────────────────────────────────────────────────────
    if args.format == "json":
        output = to_json(detections, str(root))
    elif args.format == "markdown":
        output = to_markdown(detections, str(root))
    else:
        output = None  # printed directly below

    if output:
        if args.output:
            Path(args.output).write_text(output)
            print(f"  Report written to: {args.output}", file=sys.stderr)
        else:
            print(output)
    else:
        print_terminal(detections)

    # ── CI baseline comparison ────────────────────────────────────────────────
    if args.fail_on_new:
        import json as _json
        try:
            baseline = _json.loads(Path(args.fail_on_new).read_text())
            known_ids = {t["tool_id"] for t in baseline.get("tools", [])}
            current_ids = {d.tool_id for d in detections}
            new_tools = current_ids - known_ids
            if new_tools:
                from catalog import CATALOG as _cat
                print("\n  [CI] NEW AI tools detected (not in baseline):", file=sys.stderr)
                for t in new_tools:
                    print(f"    + {_cat[t]['label']}", file=sys.stderr)
                sys.exit(1)
        except (FileNotFoundError, _json.JSONDecodeError) as e:
            print(f"  [CI] Warning: could not load baseline: {e}", file=sys.stderr)

    print(
        f"\n  Done — {len({d.tool_id for d in detections})} unique tool(s) detected "
        f"across {len(detections)} signal(s).\n",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
