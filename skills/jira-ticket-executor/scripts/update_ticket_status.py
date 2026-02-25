#!/usr/bin/env python3
"""
Update ticket status inside a Markdown table row.

Usage:
  python update_ticket_status.py --file plans/05_jira_tickets_ejecucion.md --ticket UCL-001 --status DONE
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


VALID_STATUS = {"TODO", "IN_PROGRESS", "DONE", "BLOCKED"}


def update_status(content: str, ticket: str, status: str) -> str:
    pattern = re.compile(rf"^(\|\s*{re.escape(ticket)}\s*\|.*?\|\s*)(TODO|IN_PROGRESS|DONE|BLOCKED)(\s*\|.*)$")
    lines = content.splitlines()
    replaced = False

    for i, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            lines[i] = f"{match.group(1)}{status}{match.group(3)}"
            replaced = True
            break

    if not replaced:
        raise ValueError(f"Ticket {ticket} not found in Markdown table.")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Markdown file path")
    parser.add_argument("--ticket", required=True, help="Ticket ID, e.g. UCL-001")
    parser.add_argument("--status", required=True, choices=sorted(VALID_STATUS))
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    original = path.read_text(encoding="utf-8")
    updated = update_status(original, args.ticket, args.status)
    path.write_text(updated, encoding="utf-8")
    print(f"updated {args.ticket} -> {args.status}")


if __name__ == "__main__":
    main()
