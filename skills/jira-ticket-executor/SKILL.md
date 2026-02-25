---
name: jira-ticket-executor
description: Plan and execute implementation work as explicit Jira-style tickets with live status updates in Markdown. Use when users ask to break a plan into tasks/tickets, start executing immediately, and keep each ticket status updated (`TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`) as work is completed.
---

# Jira Ticket Executor

## Overview

Drive work in a ticket-first flow: define concrete tickets, execute them in order, and update ticket status in the same tracking file after each meaningful completion.

## Workflow

1. Create a new ticket board Markdown file if one does not exist.
2. Define tickets with unique IDs (`PROJ-001`, `UCL-001`, etc.).
3. Include for each ticket: summary, dependencies, acceptance criteria, and status.
4. Set the first executable ticket to `IN_PROGRESS`.
5. Execute the ticket end-to-end.
6. Update status to `DONE` only when acceptance criteria are met and files exist.
7. Move the next unblocked ticket to `IN_PROGRESS`.
8. Keep a short progress log section in the same file with timestamped entries.

## Ticket Rules

1. Keep tickets atomic and verifiable.
2. Do not keep multiple unrelated tickets in `IN_PROGRESS`.
3. Mark `BLOCKED` only when external input is required.
4. If scope changes, add a new ticket instead of silently modifying acceptance criteria.
5. Reference exact files touched when closing a ticket.

## Execution Rules

1. Prioritize foundational tickets first:
- project skeleton
- configs
- contracts
- runnable entrypoints
2. Run validation after each technical ticket:
- lint/format if available
- unit/smoke checks relevant to the change
3. Reflect execution truthfully in status:
- if partially complete, remain `IN_PROGRESS`
- if validation fails and cannot be fixed immediately, set `BLOCKED` with reason

## Anti-Leakage Guardrails (for ML workflows)

1. Enforce temporal split.
2. Enforce `t-1` feature construction.
3. Forbid post-match target leakage columns in feature matrix.
4. Fit transformations only on training folds.
5. Keep guardrail checks as ticket acceptance criteria.

## Resources

1. Use `references/jira_ticket_template.md` when creating a new board quickly.
2. Use `scripts/update_ticket_status.py` to update table status reliably.
