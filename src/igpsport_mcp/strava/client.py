"""Strava API v3 client with automatic OAuth2 token refresh."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

STRAVA_AUTH_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"


class StravaClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        *,
        http: httpx.Client | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._http = http or httpx.Client(base_url=STRAVA_API_BASE, timeout=30.0)

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token)

    def _ensure_access_token(self) -> str:
        """Fetch or refresh OAuth2 access token if needed."""
        if not self.is_configured:
            raise ValueError("Strava credentials not configured (client_id/client_secret/refresh_token missing)")

        now = time.time()
        if self._access_token and now < (self._token_expires_at - 300):
            return self._access_token

        # Refresh token
        response = self._http.post(
            STRAVA_AUTH_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self._token_expires_at = float(data["expires_at"])
        return self._access_token

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        token = self._ensure_access_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        response = self._http.request(method, path, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def get_starred_segments(self, page: int = 1, per_page: int = 50) -> list[dict[str, Any]]:
        """Fetch athlete starred segments."""
        return self._request("GET", "/segments/starred", params={"page": page, "per_page": per_page})

    def get_segment(self, segment_id: int) -> dict[str, Any]:
        """Fetch full segment details including polyline."""
        return self._request("GET", f"/segments/{segment_id}")

    def get_segment_leaderboard(
        self, segment_id: int, page: int = 1, per_page: int = 10
    ) -> dict[str, Any]:
        """Fetch public leaderboard for a segment."""
        return self._request("GET", f"/segments/{segment_id}/leaderboard", params={"page": page, "per_page": per_page})

    def explore_segments(
        self, south_west: tuple[float, float], north_east: tuple[float, float], activity_type: str = "riding"
    ) -> list[dict[str, Any]]:
        """Search segments inside a bounding box [lat_sw, lng_sw, lat_ne, lng_ne]."""
        bounds = f"{south_west[0]},{south_west[1]},{north_east[0]},{north_east[1]}"
        data = self._request(
            "GET", "/segments/explore", params={"bounds": bounds, "activity_type": activity_type}
        )
        return data.get("segments", [])
