"""Tools: list_segments, get_segment_detail, get_segment_rank."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._service import IGPSportService


def register(server: FastMCP, service: IGPSportService) -> None:
    @server.tool()
    def list_segments_collected(
        page_no: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """List your collected (starred) segments with best times."""
        return service.list_segments_collected(page_no, page_size)

    @server.tool()
    def get_segment_detail(segments_id: str) -> dict[str, Any]:
        """Segment detail: name, distance, grade, KOM, fastest times & your PR."""
        return service.get_segment_detail(segments_id)

    @server.tool()
    def get_segment_rank(
        segments_id: str,
        page_no: int = 1,
        page_size: int = 30,
        query_type: int = 1,
    ) -> dict[str, Any]:
        """Segment leaderboard. queryType: 1=all-time, 2=yearly (or other dim)."""
        return service.get_segment_rank(segments_id, page_no, page_size, query_type)

    # ── Strava segment integration tools ───────────────────────────────────

    @server.tool()
    def sync_strava_segments(page: int = 1, per_page: int = 50) -> dict[str, Any]:
        """Fetch and sync starred Strava segments to local cache for offline activity matching."""
        return service.sync_strava_segments(page, per_page)

    @server.tool()
    def match_activity_segments(
        ride_id: str, segment_ids: list[int] | None = None
    ) -> dict[str, Any]:
        """Map-match GPS from an iGPSport activity FIT against Strava segments to compute efforts, power, HR, and VAM."""
        return service.match_activity_segments(ride_id, segment_ids)

    @server.tool()
    def get_strava_segment_leaderboard(segment_id: int) -> dict[str, Any]:
        """Get Strava leaderboard (KOM and top 10 rankings) for a segment."""
        return service.get_strava_segment_leaderboard(segment_id)

    @server.tool()
    def compare_segment_efforts(
        segment_id: int, ride_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """Compare all historical efforts and PRs on a Strava segment across iGPSport rides."""
        return service.compare_segment_efforts(segment_id, ride_ids)

