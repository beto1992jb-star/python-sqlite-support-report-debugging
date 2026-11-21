# Python & SQLite Support Report — Debugging & Query Optimization

Audit, bug fixing, and performance optimization of an AI-generated Python + SQLite customer support reporting script (`support_report.py`).

## Overview
The original script crashed on execution, produced inaccurate SLA, resolution time, team coverage, and CSAT metrics, and took ~10 seconds to run due to an N+1 query pattern.

## Key Fixes Applied
- **Runtime & Unpacking (`Python`):** Added missing `.fetchall()` call and aligned loop variable unpacking with the `TEAM_SQL` `SELECT` column order.
- **SLA & Metric Precision (`SQL` & `Python`):** Converted `julianday()` differences from days to hours (`* 24`), matched lowercase `'high'` priority in the SLA `CASE` expression, and replaced integer floor division (`//`) with true division for SLA compliance percentages.
- **Outer Join Preservation (`SQL`):** Moved `t.created_at >= ?` from `WHERE` into the `LEFT JOIN` `ON` clause so teams with zero 2026 tickets (e.g., `Retention`) remain visible with `n/a`.
- **Fixed Reference Date (`SQL`):** Replaced dynamic `date('now', '-7 days')` with a parameterized `AS_OF` date (`2026-11-15`) for open backlog calculations.
- **Ranking & State Isolation (`Python`):** Fixed `rows[:n - 1]` off-by-one slicing in `top_agents` and replaced the mutable default argument `collected=[]` in `numbered()`.
- **Performance Optimization (`SQL` & `Python`):** Replaced per-agent N+1 queries with a single grouped query (`AGENT_SQL`), reducing runtime from ~10s to under 0.5s.

## Files
- `support_report.py` — Corrected script with inline `FIXED:` comments explaining every change.
