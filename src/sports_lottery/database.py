from __future__ import annotations

from pathlib import Path
import sqlite3


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    lottery_date TEXT NOT NULL,
    match_no TEXT NOT NULL,
    competition TEXT NOT NULL,
    kickoff_time TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    handicap INTEGER,
    spf_home_odds REAL,
    spf_draw_odds REAL,
    spf_away_odds REAL,
    rqspf_home_odds REAL,
    rqspf_draw_odds REAL,
    rqspf_away_odds REAL,
    source_url TEXT,
    collected_at TEXT,
    CHECK (home_score IS NULL OR home_score >= 0),
    CHECK (away_score IS NULL OR away_score >= 0),
    UNIQUE (lottery_date, match_no)
);

CREATE INDEX IF NOT EXISTS idx_matches_kickoff ON matches(kickoff_time);
CREATE INDEX IF NOT EXISTS idx_matches_home ON matches(home_team, kickoff_time);
CREATE INDEX IF NOT EXISTS idx_matches_away ON matches(away_team, kickoff_time);
CREATE INDEX IF NOT EXISTS idx_matches_competition ON matches(competition, kickoff_time);
"""


INSERT_SQL = """
INSERT INTO matches (
    match_id, lottery_date, match_no, competition, kickoff_time,
    home_team, away_team, home_score, away_score, handicap,
    spf_home_odds, spf_draw_odds, spf_away_odds,
    rqspf_home_odds, rqspf_draw_odds, rqspf_away_odds,
    source_url, collected_at
) VALUES (
    :match_id, :lottery_date, :match_no, :competition, :kickoff_time,
    :home_team, :away_team, :home_score, :away_score, :handicap,
    :spf_home_odds, :spf_draw_odds, :spf_away_odds,
    :rqspf_home_odds, :rqspf_draw_odds, :rqspf_away_odds,
    :source_url, :collected_at
)
ON CONFLICT(match_id) DO UPDATE SET
    home_score=excluded.home_score,
    away_score=excluded.away_score,
    handicap=excluded.handicap,
    spf_home_odds=excluded.spf_home_odds,
    spf_draw_odds=excluded.spf_draw_odds,
    spf_away_odds=excluded.spf_away_odds,
    rqspf_home_odds=excluded.rqspf_home_odds,
    rqspf_draw_odds=excluded.rqspf_draw_odds,
    rqspf_away_odds=excluded.rqspf_away_odds,
    source_url=excluded.source_url,
    collected_at=excluded.collected_at;
"""


def connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(Path(path))
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA_SQL)
    return connection


def import_rows(connection: sqlite3.Connection, rows: list[dict[str, object]]) -> int:
    before = connection.total_changes
    with connection:
        connection.executemany(INSERT_SQL, rows)
    return connection.total_changes - before

