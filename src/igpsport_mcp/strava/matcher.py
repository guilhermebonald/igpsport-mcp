"""Spatial GPS matching engine to detect and compute Strava segment efforts on FIT files."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from ..analysis import power
from .polyline import decode_polyline


def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in meters."""
    r = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def match_segment_on_dataframe(
    df: pd.DataFrame,
    segment: dict[str, Any],
    *,
    proximity_radius_m: float = 35.0,
    distance_tolerance_ratio: float = 0.25,
) -> list[dict[str, Any]]:
    """Find all matching efforts of a Strava segment within an activity DataFrame.

    *df* must have columns: ['timestamp', 'latitude', 'longitude'] and optionally
    ['power', 'heart_rate', 'cadence', 'speed', 'altitude', 'distance'].
    """
    if df.empty or "latitude" not in df.columns or "longitude" not in df.columns:
        return []

    # Filter out records without valid GPS
    gps_df = df.dropna(subset=["latitude", "longitude"]).copy()
    if len(gps_df) < 5:
        return []

    seg_id = segment.get("segment_id") or segment.get("id")
    seg_name = segment.get("name", f"Segment {seg_id}")
    seg_dist = float(segment.get("distance", segment.get("distance_m", 0.0)))
    polyline_str = segment.get("polyline") or segment.get("map", {}).get("polyline", "")

    # Retrieve start / end coordinates
    if polyline_str:
        coords = decode_polyline(polyline_str)
        start_pt = coords[0] if coords else None
        end_pt = coords[-1] if coords else None
    else:
        start_pt = (segment.get("start_lat"), segment.get("start_lng"))
        end_pt = (segment.get("end_lat"), segment.get("end_lng"))

    if not start_pt or not end_pt or None in start_pt or None in end_pt:
        return []

    lats = gps_df["latitude"].to_numpy()
    lons = gps_df["longitude"].to_numpy()
    timestamps = gps_df["timestamp"].to_numpy()

    # Calculate distance to start and end for each GPS point
    # Vectorized haversine approximations
    r = 6371000.0
    phi_s, lam_s = math.radians(start_pt[0]), math.radians(start_pt[1])
    phi_e, lam_e = math.radians(end_pt[0]), math.radians(end_pt[1])

    lat_rad = np.radians(lats)
    lon_rad = np.radians(lons)

    # Dist to start
    dphi_s = lat_rad - phi_s
    dlam_s = lon_rad - lam_s
    a_s = np.sin(dphi_s / 2.0) ** 2 + np.cos(phi_s) * np.cos(lat_rad) * np.sin(dlam_s / 2.0) ** 2
    dist_to_start = 2.0 * r * np.arcsin(np.clip(np.sqrt(a_s), 0, 1))

    # Dist to end
    dphi_e = lat_rad - phi_e
    dlam_e = lon_rad - lam_e
    a_e = np.sin(dphi_e / 2.0) ** 2 + np.cos(phi_e) * np.cos(lat_rad) * np.sin(dlam_e / 2.0) ** 2
    dist_to_end = 2.0 * r * np.arcsin(np.clip(np.sqrt(a_e), 0, 1))

    start_candidates = np.where(dist_to_start <= proximity_radius_m)[0]
    end_candidates = np.where(dist_to_end <= proximity_radius_m)[0]

    if len(start_candidates) == 0 or len(end_candidates) == 0:
        return []

    efforts: list[dict[str, Any]] = []
    first_activity_ts = pd.to_datetime(df["timestamp"].iloc[0], utc=True)

    # Cluster start candidates (group consecutive indices)
    start_clusters: list[int] = []
    prev_idx = -999
    for s_idx in start_candidates:
        if s_idx > prev_idx + 10:  # New entry window
            # Pick local minimum distance to start in this cluster
            start_clusters.append(s_idx)
        prev_idx = s_idx

    for s_idx in start_clusters:
        valid_ends = end_candidates[end_candidates > s_idx + 3]
        if len(valid_ends) == 0:
            continue

        # Find the earliest matching end point for this start
        e_idx = valid_ends[0]

        # Extract effort slice from original dataframe
        t_start = pd.to_datetime(timestamps[s_idx], utc=True)
        t_end = pd.to_datetime(timestamps[e_idx], utc=True)

        effort_df = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_end)]
        if effort_df.empty:
            continue

        elapsed_s = max(1, int((t_end - t_start).total_seconds()))

        # Distance validation if available
        if "distance" in effort_df.columns and not effort_df["distance"].dropna().empty:
            actual_dist_m = float(effort_df["distance"].iloc[-1] - effort_df["distance"].iloc[0])
        else:
            actual_dist_m = float(seg_dist)

        if seg_dist > 0 and abs(actual_dist_m - seg_dist) / seg_dist > distance_tolerance_ratio:
            # Traveled distance deviates significantly from segment distance
            continue

        # Telemetry metrics
        avg_power = (
            float(effort_df["power"].mean())
            if "power" in effort_df.columns and not effort_df["power"].dropna().empty
            else None
        )
        np_w = (
            power.normalized_power(effort_df["power"].fillna(0).tolist())
            if "power" in effort_df.columns and len(effort_df) >= 30
            else avg_power
        )
        avg_hr = (
            float(effort_df["heart_rate"].mean())
            if "heart_rate" in effort_df.columns and not effort_df["heart_rate"].dropna().empty
            else None
        )
        max_hr = (
            float(effort_df["heart_rate"].max())
            if "heart_rate" in effort_df.columns and not effort_df["heart_rate"].dropna().empty
            else None
        )
        avg_cad = (
            float(effort_df["cadence"].mean())
            if "cadence" in effort_df.columns and not effort_df["cadence"].dropna().empty
            else None
        )

        avg_speed_kmh = round((actual_dist_m / elapsed_s) * 3.6, 2) if elapsed_s > 0 else None

        elev_gain = 0.0
        if "altitude" in effort_df.columns and not effort_df["altitude"].dropna().empty:
            alts = effort_df["altitude"].to_numpy()
            diffs = np.diff(alts)
            elev_gain = float(np.sum(diffs[diffs > 0]))

        vam = (
            round((elev_gain / elapsed_s) * 3600.0, 1)
            if (elapsed_s > 0 and elev_gain > 5)
            else None
        )

        start_offset = int((t_start - first_activity_ts).total_seconds())
        end_offset = int((t_end - first_activity_ts).total_seconds())

        effort_dict = {
            "segment_id": int(seg_id),
            "name": seg_name,
            "start_time": t_start.isoformat(),
            "elapsed_time_s": elapsed_s,
            "moving_time_s": elapsed_s,
            "distance_m": round(actual_dist_m, 1),
            "avg_power_w": round(avg_power, 1) if avg_power is not None else None,
            "normalized_power_w": round(np_w, 1) if np_w is not None else None,
            "avg_hr_bpm": round(avg_hr, 1) if avg_hr is not None else None,
            "max_hr_bpm": round(max_hr, 1) if max_hr is not None else None,
            "avg_cadence_rpm": round(avg_cad, 1) if avg_cad is not None else None,
            "avg_speed_kmh": avg_speed_kmh,
            "elevation_gain_m": round(elev_gain, 1),
            "vam_mh": vam,
            "start_offset_s": start_offset,
            "end_offset_s": end_offset,
        }
        efforts.append(effort_dict)

    return efforts
