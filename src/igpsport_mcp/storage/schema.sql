-- SQLite schema for igpsport-mcp local cache (~/.cache/igpsport-mcp/activities.db).
-- Activity list/summary are cached so repeat requests for the same ride hit zero API.

CREATE TABLE IF NOT EXISTS activities (
    ride_id           TEXT PRIMARY KEY,
    name              TEXT,
    start_time        TEXT NOT NULL,           -- ISO 8601 with timezone
    duration_s        INTEGER,
    distance_km       REAL,
    elevation_gain_m  REAL,
    sport_type        TEXT,
    avg_power_w       REAL,
    avg_hr_bpm        REAL,
    fit_path          TEXT,                    -- local cached FIT, NULL until downloaded
    raw_json          TEXT,                    -- original list-item payload
    fetched_at        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_activities_start_time ON activities (start_time);

-- Derived metrics computed locally from the FIT; keyed by ride.
-- No FK to activities so that get_activity_summary works without a prior list_activities.
CREATE TABLE IF NOT EXISTS activity_metrics (
    ride_id              TEXT PRIMARY KEY,
    normalized_power_w   REAL,
    intensity_factor     REAL,
    tss                  REAL,
    work_kj              REAL,
    max_power_w          REAL,
    max_hr_bpm           REAL,
    avg_cadence_rpm      REAL,
    metrics_json         TEXT,                 -- full computed summary blob
    computed_at          TEXT NOT NULL
);

-- Athlete profile / training parameters snapshot.
CREATE TABLE IF NOT EXISTS athlete_profile (
    id          INTEGER PRIMARY KEY CHECK (id = 1),
    profile_json TEXT NOT NULL,
    fetched_at   TEXT NOT NULL
);

-- Strava segments metadata and geometry
CREATE TABLE IF NOT EXISTS strava_segments (
    segment_id       INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    activity_type    TEXT,
    distance_m       REAL,
    average_grade    REAL,
    maximum_grade    REAL,
    elevation_high_m REAL,
    elevation_low_m  REAL,
    start_lat        REAL,
    start_lng        REAL,
    end_lat          REAL,
    end_lng          REAL,
    climb_category   INTEGER,
    polyline         TEXT,                 -- Encoded polyline summary
    raw_json         TEXT,
    fetched_at       TEXT NOT NULL
);

-- Matched segment efforts on iGPSport rides
CREATE TABLE IF NOT EXISTS strava_segment_efforts (
    id                 TEXT PRIMARY KEY,   -- f"{ride_id}_{segment_id}_{start_offset_s}"
    ride_id            TEXT NOT NULL,
    segment_id         INTEGER NOT NULL,
    name               TEXT NOT NULL,
    start_time         TEXT NOT NULL,
    elapsed_time_s     INTEGER NOT NULL,
    moving_time_s      INTEGER NOT NULL,
    distance_m         REAL,
    avg_power_w        REAL,
    normalized_power_w REAL,
    avg_hr_bpm         REAL,
    max_hr_bpm         REAL,
    avg_cadence_rpm    REAL,
    avg_speed_kmh      REAL,
    vam_mh             REAL,
    start_offset_s     INTEGER NOT NULL,
    end_offset_s       INTEGER NOT NULL,
    computed_at        TEXT NOT NULL,
    FOREIGN KEY(segment_id) REFERENCES strava_segments(segment_id)
);

CREATE INDEX IF NOT EXISTS idx_efforts_segment_id ON strava_segment_efforts (segment_id);
CREATE INDEX IF NOT EXISTS idx_efforts_ride_id ON strava_segment_efforts (ride_id);

-- Strava segment leaderboards cache
CREATE TABLE IF NOT EXISTS strava_leaderboards (
    segment_id       INTEGER PRIMARY KEY,
    leaderboard_json TEXT NOT NULL,
    kom_time_s       INTEGER,
    kom_athlete      TEXT,
    fetched_at       TEXT NOT NULL
);

