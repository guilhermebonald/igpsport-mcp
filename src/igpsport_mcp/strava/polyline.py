"""Strava Encoded Polyline algorithm decoder (standard Google Polyline format)."""

from __future__ import annotations


def decode_polyline(polyline_str: str) -> list[tuple[float, float]]:
    """Decode a Google encoded polyline string into a list of (latitude, longitude) tuples."""
    if not polyline_str:
        return []

    coordinates: list[tuple[float, float]] = []
    index = 0
    length = len(polyline_str)
    lat = 0
    lng = 0

    while index < length:
        # Latitude
        shift = 0
        result = 0
        while True:
            byte = ord(polyline_str[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        # Longitude
        shift = 0
        result = 0
        while True:
            byte = ord(polyline_str[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coordinates.append((lat / 1e5, lng / 1e5))

    return coordinates
