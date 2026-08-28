"""SQLite CRUD for the local cache.

Tools query the cache first and only hit the API on a miss; the FIT file is
cached permanently on disk (see ``IGPSportClient.download_fit``). This module
owns the activity-metadata table only; derived metrics are written by the
analysis layer in later phases.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any

SCHEMA_RESOURCE = "schema.sql"

_ACTIVITY_COLUMNS = (
    "ride_id",
    "name",
    "start_time",
    "duration_s",
    "distance_km",
    "elevation_gain_m",
    "sport_type",
    "avg_power_w",
    "avg_hr_bpm",
    "fit_path",
    "raw_json",
    "fetched_at",
)


def schema_sql() -> str:
    """Return the bundled schema DDL."""
    return resources.files(__package__).joinpath(SCHEMA_RESOURCE).read_text(encoding="utf-8")


def connect(db_path: Path) -> sqlite3.Connection:
    """Open (creating parent dirs) and initialize the cache database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(schema_sql())
    return conn


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def upsert_activity(conn: sqlite3.Connection, activity: dict[str, Any]) -> None:
    """Insert or update a single normalized activity row."""
    ride_id = activity.get("ride_id")
    if ride_id is None:
        return
    row = {col: activity.get(col) for col in _ACTIVITY_COLUMNS}
    row["ride_id"] = str(ride_id)
    if isinstance(row["raw_json"], (dict, list)):
        row["raw_json"] = json.dumps(row["raw_json"], ensure_ascii=False)
    row["fetched_at"] = row["fetched_at"] or _now_iso()

    placeholders = ", ".join(f":{c}" for c in _ACTIVITY_COLUMNS)
    updates = ", ".join(f"{c}=excluded.{c}" for c in _ACTIVITY_COLUMNS if c != "ride_id")
    conn.execute(
        f"INSERT INTO activities ({', '.join(_ACTIVITY_COLUMNS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(ride_id) DO UPDATE SET {updates}",
        row,
    )
    conn.commit()


def upsert_activities(conn: sqlite3.Connection, activities: list[dict[str, Any]]) -> None:
    if not activities:
        return
    rows = []
    for activity in activities:
        ride_id = activity.get("ride_id")
        if ride_id is None:
            continue
        row = {col: activity.get(col) for col in _ACTIVITY_COLUMNS}
        row["ride_id"] = str(ride_id)
        if isinstance(row["raw_json"], (dict, list)):
            row["raw_json"] = json.dumps(row["raw_json"], ensure_ascii=False)
        row["fetched_at"] = row["fetched_at"] or _now_iso()
        rows.append(row)

    placeholders = ", ".join(f":{c}" for c in _ACTIVITY_COLUMNS)
    updates = ", ".join(f"{c}=excluded.{c}" for c in _ACTIVITY_COLUMNS if c != "ride_id")
    conn.executemany(
        f"INSERT INTO activities ({', '.join(_ACTIVITY_COLUMNS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(ride_id) DO UPDATE SET {updates}",
        rows,
    )
    conn.commit()


def get_activity(conn: sqlite3.Connection, ride_id: str | int) -> dict[str, Any] | None:
    cur = conn.execute("SELECT * FROM activities WHERE ride_id = ?", (str(ride_id),))
    row = cur.fetchone()
    return dict(row) if row else None


def list_activities(
    conn: sqlite3.Connection, limit: int = 20, offset: int = 0
) -> list[dict[str, Any]]:
    cur = conn.execute(
        "SELECT * FROM activities ORDER BY start_time DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    return [dict(row) for row in cur.fetchall()]


def set_fit_path(conn: sqlite3.Connection, ride_id: str | int, fit_path: Path) -> None:
    conn.execute(
        "UPDATE activities SET fit_path = ? WHERE ride_id = ?",
        (str(fit_path), str(ride_id)),
    )
    conn.commit()


# -- derived metrics cache ---------------------------------------------------

_METRICS_COLS = (
    "ride_id",
    "normalized_power_w",
    "intensity_factor",
    "tss",
    "work_kj",
    "max_power_w",
    "max_hr_bpm",
    "avg_cadence_rpm",
    "metrics_json",
    "computed_at",
)


def get_activity_metrics(conn: sqlite3.Connection, ride_id: str | int) -> dict[str, Any] | None:
    """Return cached derived metrics for *ride_id*, or None."""
    cur = conn.execute("SELECT * FROM activity_metrics WHERE ride_id = ?", (str(ride_id),))
    row = cur.fetchone()
    return dict(row) if row else None


def save_activity_metrics(
    conn: sqlite3.Connection, ride_id: str | int, summary: dict[str, Any]
) -> None:
    """Persist computed summary block for a ride.

    Gracefully handles legacy DBs with a FK constraint on ``ride_id`` — the
    in-memory cache still works, we just skip the SQLite write.
    """
    s = summary.get("summary") or summary
    row = {
        "ride_id": str(ride_id),
        "normalized_power_w": s.get("normalized_power_w"),
        "intensity_factor": s.get("intensity_factor"),
        "tss": s.get("tss"),
        "work_kj": s.get("work_kj"),
        "max_power_w": s.get("max_power_w"),
        "max_hr_bpm": s.get("max_hr_bpm"),
        "avg_cadence_rpm": s.get("avg_cadence_rpm"),
        "metrics_json": json.dumps(summary, ensure_ascii=False),
        "computed_at": _now_iso(),
    }
    placeholders = ", ".join(f":{c}" for c in _METRICS_COLS)
    updates = ", ".join(f"{c}=excluded.{c}" for c in _METRICS_COLS if c != "ride_id")
    try:
        conn.execute(
            f"INSERT INTO activity_metrics ({', '.join(_METRICS_COLS)}) VALUES ({placeholders}) "
            f"ON CONFLICT(ride_id) DO UPDATE SET {updates}",
            row,
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Legacy DB with FK on activities.ride_id and the row wasn't cached
        # via list_activities first. Degrade gracefully — next call that
        # goes through list_activities will populate the FK.
        pass


# ── Strava storage ──────────────────────────────────────────────────────────


def upsert_strava_segment(conn: sqlite3.Connection, segment: dict[str, Any]) -> None:
    """Insert or update a Strava segment definition."""
    segment_id = segment.get("segment_id") or segment.get("id")
    if not segment_id:
        return
    start_latlng = segment.get("start_latlng") or [None, None]
    end_latlng = segment.get("end_latlng") or [None, None]
    row = {
        "segment_id": int(segment_id),
        "name": str(segment.get("name", "")),
        "activity_type": segment.get("activity_type", "Ride"),
        "distance_m": float(segment.get("distance", 0.0)),
        "average_grade": float(segment.get("average_grade", 0.0)),
        "maximum_grade": float(segment.get("maximum_grade", 0.0)),
        "elevation_high_m": segment.get("elevation_high"),
        "elevation_low_m": segment.get("elevation_low"),
        "start_lat": start_latlng[0] if len(start_latlng) > 0 else None,
        "start_lng": start_latlng[1] if len(start_latlng) > 1 else None,
        "end_lat": end_latlng[0] if len(end_latlng) > 0 else None,
        "end_lng": end_latlng[1] if len(end_latlng) > 1 else None,
        "climb_category": segment.get("climb_category", 0),
        "polyline": segment.get("polyline") or segment.get("map", {}).get("polyline", ""),
        "raw_json": json.dumps(segment, ensure_ascii=False),
        "fetched_at": _now_iso(),
    }
    cols = list(row.keys())
    placeholders = ", ".join(f":{c}" for c in cols)
    updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "segment_id")
    conn.execute(
        f"INSERT INTO strava_segments ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT(segment_id) DO UPDATE SET {updates}",
        row,
    )
    conn.commit()


def get_strava_segments(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Retrieve all cached Strava segments."""
    cursor = conn.execute("SELECT * FROM strava_segments ORDER BY name ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    return rows


def get_strava_segment_by_id(conn: sqlite3.Connection, segment_id: int) -> dict[str, Any] | None:
    """Retrieve a single cached Strava segment."""
    cursor = conn.execute("SELECT * FROM strava_segments WHERE segment_id = ?", (segment_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def save_segment_effort(conn: sqlite3.Connection, effort: dict[str, Any]) -> None:
    """Insert or update a computed segment effort."""
    effort_id = effort.get("id") or f"{effort['ride_id']}_{effort['segment_id']}_{effort['start_offset_s']}"
    row = {
        "id": effort_id,
        "ride_id": str(effort["ride_id"]),
        "segment_id": int(effort["segment_id"]),
        "name": str(effort["name"]),
        "start_time": str(effort["start_time"]),
        "elapsed_time_s": int(effort["elapsed_time_s"]),
        "moving_time_s": int(effort.get("moving_time_s", effort["elapsed_time_s"])),
        "distance_m": float(effort.get("distance_m", 0.0)),
        "avg_power_w": effort.get("avg_power_w"),
        "normalized_power_w": effort.get("normalized_power_w"),
        "avg_hr_bpm": effort.get("avg_hr_bpm"),
        "max_hr_bpm": effort.get("max_hr_bpm"),
        "avg_cadence_rpm": effort.get("avg_cadence_rpm"),
        "avg_speed_kmh": effort.get("avg_speed_kmh"),
        "vam_mh": effort.get("vam_mh"),
        "start_offset_s": int(effort["start_offset_s"]),
        "end_offset_s": int(effort["end_offset_s"]),
        "computed_at": _now_iso(),
    }
    cols = list(row.keys())
    placeholders = ", ".join(f":{c}" for c in cols)
    updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "id")
    conn.execute(
        f"INSERT INTO strava_segment_efforts ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}",
        row,
    )
    conn.commit()


def get_segment_efforts(
    conn: sqlite3.Connection, segment_id: int, ride_id: str | None = None
) -> list[dict[str, Any]]:
    """Retrieve saved efforts for a segment, optionally filtered by ride."""
    if ride_id:
        cursor = conn.execute(
            "SELECT * FROM strava_segment_efforts WHERE segment_id = ? AND ride_id = ? "
            "ORDER BY elapsed_time_s ASC",
            (segment_id, str(ride_id)),
        )
    else:
        cursor = conn.execute(
            "SELECT * FROM strava_segment_efforts WHERE segment_id = ? "
            "ORDER BY elapsed_time_s ASC",
            (segment_id,),
        )
    return [dict(r) for r in cursor.fetchall()]


def upsert_strava_leaderboard(
    conn: sqlite3.Connection,
    segment_id: int,
    leaderboard_data: dict[str, Any],
    kom_time_s: int | None = None,
    kom_athlete: str | None = None,
) -> None:
    """Cache leaderboard data for a segment."""
    row = {
        "segment_id": segment_id,
        "leaderboard_json": json.dumps(leaderboard_data, ensure_ascii=False),
        "kom_time_s": kom_time_s,
        "kom_athlete": kom_athlete,
        "fetched_at": _now_iso(),
    }
    conn.execute(
        "INSERT INTO strava_leaderboards (segment_id, leaderboard_json, kom_time_s, kom_athlete, fetched_at) "
        "VALUES (:segment_id, :leaderboard_json, :kom_time_s, :kom_athlete, :fetched_at) "
        "ON CONFLICT(segment_id) DO UPDATE SET "
        "leaderboard_json=excluded.leaderboard_json, kom_time_s=excluded.kom_time_s, "
        "kom_athlete=excluded.kom_athlete, fetched_at=excluded.fetched_at",
        row,
    )
    conn.commit()


def get_strava_leaderboard(conn: sqlite3.Connection, segment_id: int) -> dict[str, Any] | None:
    """Retrieve cached leaderboard for a segment."""
    cursor = conn.execute("SELECT * FROM strava_leaderboards WHERE segment_id = ?", (segment_id,))
    row = cursor.fetchone()
    if not row:
        return None
    res = dict(row)
    with contextlib.suppress(Exception):
        res["data"] = json.loads(res["leaderboard_json"])
    return res

