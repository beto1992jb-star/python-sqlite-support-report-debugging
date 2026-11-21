"""
Customer support report.

Reads support.db and prints, as of a fixed date:
  - team performance for tickets created in 2026 (tickets, average
    resolution time, SLA compliance and average CSAT)
  - the top 5 agents by CSAT (at least 20 rated tickets)
  - the open backlog older than 7 days, by priority

SLA targets (hours to resolve): high = 4, medium = 24, low = 72.
"""
import sqlite3
import time  # -- FIXED: import time to measure execution runtime for verification

DB_FILE = "support.db"
AS_OF = "2026-11-15"
YEAR_START = "2026-01-01"

TEAM_SQL = """
SELECT a.team,
       COUNT(DISTINCT t.ticket_id) AS tickets,
       ROUND(AVG((julianday(t.resolved_at) - julianday(t.created_at)) * 24), 1) AS avg_hours, -- -- FIXED: convert days to hours (* 24)
       SUM(CASE WHEN t.resolved_at IS NOT NULL
                 AND (julianday(t.resolved_at) - julianday(t.created_at)) * 24 <=
                     CASE t.priority WHEN 'high' THEN 4 WHEN 'medium' THEN 24 ELSE 72 END -- -- FIXED: match lowercase 'high' priority
                THEN 1 ELSE 0 END) AS sla_met,
       COUNT(t.resolved_at) AS resolved,
       ROUND(AVG(c.score), 2) AS avg_csat
FROM agents a
LEFT JOIN tickets t ON t.agent_id = a.agent_id AND t.created_at >= ? -- -- FIXED: move date filter to LEFT JOIN to keep teams with no 2026 tickets
LEFT JOIN csat c ON c.ticket_id = t.ticket_id
GROUP BY a.team
ORDER BY a.team
"""

AGENT_SQL = """
SELECT a.name, a.team, COUNT(c.score) AS ratings, ROUND(AVG(c.score), 2) AS avg_score
FROM agents a
JOIN tickets t ON t.agent_id = a.agent_id
JOIN csat c ON c.ticket_id = t.ticket_id
WHERE t.created_at >= ?
GROUP BY a.agent_id
HAVING COUNT(c.score) >= 20
ORDER BY avg_score DESC, ratings DESC, a.name ASC -- -- FIXED: order by avg CSAT desc, ratings desc, then name asc
"""

BACKLOG_SQL = """
SELECT priority, COUNT(*)
FROM tickets
WHERE status = 'open' AND created_at < date(?, '-7 days') -- -- FIXED: use fixed reference date AS_OF instead of date('now')
GROUP BY priority
"""


def fmt(value, template):
    """Format a value, or show n/a when there is no data."""
    return "n/a" if value is None else template.format(value)


def team_report(conn):
    """One line per team."""
    rows = conn.execute(TEAM_SQL, (YEAR_START,)).fetchall()  # # FIXED: call fetchall() instead of referencing bound method
    lines = []
    for team, tickets, avg_hours, sla_met, resolved, avg_csat in rows:  # # FIXED: unpack columns in exact SELECT order
        sla_pct = (sla_met / resolved) * 100 if resolved else None  # # FIXED: use true division instead of floor division //
        lines.append(
            f"  {team} | {tickets:,} | {fmt(avg_hours, '{:.1f}')} | "
            f"{fmt(sla_pct, '{:.1f}%')} | {fmt(avg_csat, '{:.2f}')}"
        )
    return lines


def top_agents(conn, n=5):
    """The n agents with the highest average CSAT. Ties: more ratings first, then name."""
    rows = conn.execute(AGENT_SQL, (YEAR_START,)).fetchall()  # # FIXED: run single set-based query instead of N+1 queries per agent
    ranked = [(name, team, ratings, round(avg_score, 2)) for name, team, ratings, avg_score in rows]  # # FIXED: format scores cleanly
    ranked.sort(key=lambda r: (-r[3], -r[2], r[0]))  # # FIXED: ensure deterministic tie-breaking by score desc, ratings desc, name asc
    return ranked[:n]  # # FIXED: return top n items instead of n - 1


def backlog(conn):
    """Open tickets older than 7 days, by priority."""
    found = dict(conn.execute(BACKLOG_SQL, (AS_OF,)).fetchall())  # # FIXED: pass fixed reference date AS_OF as query parameter
    return {priority: found.get(priority, 0) for priority in ("high", "medium", "low")}


def numbered(lines, collected=None):  # # FIXED: avoid mutable default argument []
    """Add numbering to a list of lines."""
    if collected is None:  # # FIXED: initialize fresh list per call when not provided
        collected = []
    for line in lines:
        collected.append(f"  {len(collected) + 1}. {line}")
    return collected


def main():
    start_time = time.perf_counter()  # # FIXED: track runtime for verification output
    conn = sqlite3.connect(DB_FILE)

    print(f"=== SUPPORT REPORT (as of {AS_OF}) ===")

    print(f"\nTeam performance (tickets created since {YEAR_START}):")
    print("  team | tickets | avg_resolution_hours | sla_met | avg_csat")
    for line in team_report(conn):
        print(line)

    print("\nTop 5 agents by CSAT (at least 20 rated tickets):")
    agent_lines = [f"{name} ({team}): {score:.2f} ({ratings} ratings)"
                   for name, team, ratings, score in top_agents(conn)]
    for line in numbered(agent_lines):
        print(line)

    print("\nOpen backlog older than 7 days:")
    backlog_lines = [f"{priority}: {count}" for priority, count in backlog(conn).items()]
    for line in numbered(backlog_lines):
        print(line)

    conn.close()
    elapsed = time.perf_counter() - start_time  # # FIXED: compute total runtime
    print(f"\nVerification: executed in {elapsed:.3f}s")  # # FIXED: print verification timing line


if __name__ == "__main__":
    main()