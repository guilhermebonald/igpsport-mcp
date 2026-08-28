<!-- mcp-name: io.github.guilhermebonald/igpsport-mcp -->
# igpsport-mcp

[Português](README.md) | **English** | [简体中文](README.zh-CN.md)

A local [MCP](https://modelcontextprotocol.io) server connecting your **iGPSport cycling and Strava data** to LLM clients such as Claude Desktop, Claude Code, and Cursor. Analyze rides in natural language, perform offline GPS map-matching against Strava segments without uploading to Strava, and push structured workouts directly to your bike computer.

---

## Key Features

- ⚡ **Derived Training Metrics**: Server-side NP, IF, TSS, hrTSS, CTL (Fitness), ATL (Fatigue), and TSB (Form) calculated locally (< 2% variance vs. Strava/TrainingPeaks).
- 🗺️ **Offline Strava Segments Integration**: Spatial map-matching engine (vectorized Haversine) running on raw iGPSport `.fit` telemetry. Computes times, speed, power, HR, and VAM against Strava starred segments, PRs, and KOMs **without uploading the ride to Strava**.
- 📋 **Structured Workout Prescription**: Compose workouts in natural language (e.g. *2x20min SST*) and push directly to iGPSport App / head unit with optional iCal calendar export.
- 🔒 **100% Local & Private**: Operates via stdio with local SQLite database (`activities.db`) and `.fit` file caching. Zero telemetry shared with third-party servers.
- 🌐 **Multi-Language & Multi-Region**: Portuguese (`pt`), English (`en`), and Chinese (`zh`). Compatible with International (`app.igpsport.com`) and China (`app.igpsport.cn` with WASM) servers.

---

## Demo

```
You:    Analyze my training load over the last 90 days and check if I hit any PRs on today's segments.
Claude: 
  📊 Training Load:
  - CTL (Fitness): 72 | ATL (Fatigue): 91 | TSB (Form): -19 (Significant fatigue buildup, suggest 3 recovery days).
  
  🏆 Matched Strava Segments for Ride 90672495 (49.46 km):
  1. Ponte Iúna até ICC (2.41 km): 7m02s (20.6 km/h, VAM 165 m/h) | Your PR: 4m27s | KOM: 3m36s
  2. SUBIDINHA (713 m, 11.9%): 4m59s (8.6 km/h, VAM 1,004 m/h) | Your PR/KOM: 3m23s
  3. Subida do Dante (538 m, 6.0%): 3m32s (9.1 km/h, VAM 571 m/h) | Your PR: 1m29s | KOM: 1m25s
```

---

## Quick Start

### 1. Install `uv` (Fast Python Package Manager)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install and run the Interactive Setup

```bash
uv tool install igpsport-mcp
igpsport-mcp --setup --lang en
```

The wizard saves credentials to:
- **macOS / Linux**: `~/.igpsport-mcp/config.json`
- **Windows**: `C:\Users\YourName\.igpsport-mcp\config.json`

### 3. Add to your MCP Client (Claude Desktop / Cursor)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "igpsport": {
      "command": "uvx",
      "args": ["igpsport-mcp"],
      "env": {
        "IGPSPORT_USERNAME": "your_email@example.com",
        "IGPSPORT_PASSWORD": "your_password",
        "IGPSPORT_REGION": "intl",
        "STRAVA_CLIENT_ID": "your_client_id",
        "STRAVA_CLIENT_SECRET": "your_client_secret",
        "STRAVA_REFRESH_TOKEN": "your_refresh_token"
      }
    }
  }
}
```

---

## CLI Commands

| Command | Purpose |
|---|---|
| `igpsport-mcp --setup` | Interactive setup wizard |
| `igpsport-mcp --check` | Verify iGPSport and Strava credentials |
| `igpsport-mcp --mcp-config` | Print MCP client JSON configuration block |
| `igpsport-mcp --lang en\|pt\|zh` | Set CLI display language (default `en` or `pt`) |
| `igpsport-mcp --version` | Display version |

---

## Available MCP Tools (21 Tools)

### 🚴 Activities & Performance (9 tools)
- `list_activities`: Paginated activity history with dates, distances, and sync status.
- `get_activity_summary`: Comprehensive summary (distance, elevation, NP, IF, TSS, hrTSS, power & HR zones).
- `get_activity_streams`: Continuous 1Hz time series (power, HR, cadence, altitude, speed) with downsampling.
- `get_activity_laps`: Lap-by-lap splits with per-lap averages.
- `get_athlete_profile`: Athlete profile (weight, max HR, FTP, LTHR, calculated zones).
- `get_athlete_stats`: Aggregated distance, duration, and elevation stats.
- `get_member_statistics`: Annual totals and personal bests.
- `compare_activities`: Side-by-side comparison of 2–5 activities.
- `estimate_thresholds`: FTP and LTHR estimation from historical Mean-Max Power (MMP).

### 📈 Training Load & Periodization (1 tool)
- `analyze_training_load`: Long-term Fitness (CTL, 42d), Fatigue (ATL, 7d), and Form (TSB) analysis.

### 🗺️ Strava Segments & Map-Matching (4 tools)
- `sync_strava_segments`: Cache starred Strava segments with polylines into local SQLite.
- `match_activity_segments`: Run spatial map-matching on iGPSport FIT files to calculate segment efforts, VAM, speed, power, and HR.
- `get_strava_segment_leaderboard`: Strava KOM/QOM and top 10 rankings.
- `compare_segment_efforts`: Historical effort comparisons on the same segment across rides.

### 🏔️ Native iGPSport Segments (3 tools - CN server only)
- `list_segments_collected`: Starred segments on iGPSport.
- `get_segment_detail`: Elevation, grade, and personal PR.
- `get_segment_rank`: Official iGPSport leaderboard.

### 📝 Structured Workouts (4 tools)
- `list_workouts`: List workouts saved on iGPSport cloud.
- `get_workout_detail`: Workout steps, targets, and intervals.
- `create_workout`: Compile workout IR into native head unit format (`dry_run` and iCal export supported).
- `delete_workout`: Delete workout (requires `confirm=True`).

---

## Configuration & Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `IGPSPORT_USERNAME` | ✅ | - | Account email (intl) or phone (CN) |
| `IGPSPORT_PASSWORD` | ✅ | - | Account password |
| `IGPSPORT_REGION` | Optional | `intl` | Region: `intl` (`app.igpsport.com`) or `cn` (`app.igpsport.cn`) |
| `STRAVA_CLIENT_ID` | Optional | - | Strava API Client ID |
| `STRAVA_CLIENT_SECRET` | Optional | - | Strava API Client Secret |
| `STRAVA_REFRESH_TOKEN` | Optional | - | Strava OAuth2 Refresh Token (`activity:read_all`) |
| `IGPSPORT_FTP` | Optional | Auto | FTP in watts (overrides cloud profile if specified) |
| `IGPSPORT_LTHR` | Optional | Auto | Lactate Threshold Heart Rate in bpm |
| `IGPSPORT_LANG` | Optional | `pt` | CLI interface language (`pt`, `en`, `zh`) |
| `IGPSPORT_CACHE_DIR` | Optional | `~/.cache/igpsport-mcp` | Cache directory |
| `IGPSPORT_LOG_LEVEL` | Optional | `INFO` | Log level |

---

## Credits & Attribution

- **Maintenance & Advanced Features (Strava Segments, PT i18n, Map-Matching)**: [Guilherme Bonald](https://github.com/guilhermebonald)
- **Original Author & Initial Reverse Engineering**: [dengxuhui](https://github.com/dengxuhui/igpsport-mcp)

Distributed under the MIT License.
