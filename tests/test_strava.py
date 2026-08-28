import pandas as pd
import pytest

from igpsport_mcp.strava.client import StravaClient
from igpsport_mcp.strava.matcher import match_segment_on_dataframe
from igpsport_mcp.strava.polyline import decode_polyline


def test_decode_polyline():
    # Encoded polyline for simple points: (38.5, -120.2), (40.7, -120.95), (43.252, -126.453)
    encoded = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    coords = decode_polyline(encoded)
    assert len(coords) == 3
    assert pytest.approx(coords[0][0], rel=1e-3) == 38.5
    assert pytest.approx(coords[0][1], rel=1e-3) == -120.2


def test_strava_client_not_configured():
    client = StravaClient()
    assert not client.is_configured
    with pytest.raises(ValueError, match="Strava credentials not configured"):
        client._ensure_access_token()


def test_strava_client_refresh_token(httpx_mock):
    httpx_mock.add_response(
        url="https://www.strava.com/oauth/token",
        method="POST",
        json={"access_token": "new_access_jwt", "expires_at": 9999999999.0, "refresh_token": "r2"},
    )
    client = StravaClient("id1", "sec1", "ref1")
    assert client.is_configured
    token = client._ensure_access_token()
    assert token == "new_access_jwt"
    assert client.refresh_token == "r2"


def test_segment_matching_on_dataframe():
    # Build synthetic GPS route passing through a known segment
    # Segment: (-23.55052, -46.633308) to (-23.55100, -46.63400)
    timestamps = pd.date_range("2026-08-28 10:00:00+00:00", periods=60, freq="1s")
    lats = [-23.55000 + (i * 0.00003) for i in range(60)]
    lons = [-46.63250 - (i * 0.00003) for i in range(60)]
    powers = [250.0 + (i % 10) for i in range(60)]
    hrs = [150 + (i % 5) for i in range(60)]
    cads = [90 for _ in range(60)]
    dists = [float(i * 10) for i in range(60)]

    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "latitude": lats,
            "longitude": lons,
            "power": powers,
            "heart_rate": hrs,
            "cadence": cads,
            "distance": dists,
        }
    )

    segment = {
        "segment_id": 12345,
        "name": "Subida Teste",
        "distance": 300.0,
        "start_lat": lats[10],
        "start_lng": lons[10],
        "end_lat": lats[40],
        "end_lng": lons[40],
    }

    efforts = match_segment_on_dataframe(df, segment, proximity_radius_m=50.0)
    assert len(efforts) == 1
    eff = efforts[0]
    assert eff["segment_id"] == 12345
    assert eff["elapsed_time_s"] >= 25
    assert eff["avg_power_w"] is not None
    assert eff["avg_hr_bpm"] is not None
