<!-- mcp-name: io.github.guilhermebonald/igpsport-mcp -->
# igpsport-mcp

**English** | [Português](https://github.com/guilhermebonald/igpsport-mcp/blob/main/README.md) | [简体中文](https://github.com/guilhermebonald/igpsport-mcp/blob/main/README.zh-CN.md)

A local [MCP](https://modelcontextprotocol.io) server that connects your **iGPSport cycling data** to LLM clients like Claude. Analyze your training in natural language: *"How's my training load this week?"* *"Compare my two long rides from last week and this week."* *"What's my ranking on that climb I starred?"* *"How many kilometers did I ride this year, and what are my personal bests?"* — and even **have Claude prescribe workouts for you**: *"Build me a 2×20 SST session based on my FTP and push it to my head unit."*

**Key differentiator**: Derived training metrics — NP / IF / TSS / CTL / ATL / TSB — are **computed server-side in the MCP layer** before being returned. The LLM receives story-ready numbers, not raw stream data.

```
You:   What's my training load trend over the last 90 days? Should I back off?
Claude (via analyze_training_load):
       Current CTL (Fitness) 72, ATL (Fatigue) 91, TSB (Form) -19 — you're in a significant fatigue hole.
       TSS has been above CTL for the past two weeks. Consider a 3–5 day recovery block to get TSB back above -5…
```

## Demo

![igpsport-mcp demo](assets/demo.gif)

> ⚠️ **Unofficial project**. This tool works by **simulating iGPSport web client requests**. iGPSport may change their API at any time, which could break functionality. Please evaluate account risk yourself — **use at your own risk**. Runs entirely locally over stdio — **your data never touches any third-party server**.

## Quick Start (Recommended)

This tool is an MCP server and requires an **MCP-capable client** (e.g. [Claude Desktop](https://claude.ai/download) / Claude Code / Cursor). Once you have a client ready, three steps:

**1. Install uv** (a standalone tool — **you do not need Python pre-installed**, uv handles the runtime automatically):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2. Install globally and run the setup wizard** (interactively enter your phone/email and password — credentials stay local). The commands are the same on both systems; run them in **Terminal** on macOS or **PowerShell** on Windows:

```bash
uv tool install igpsport-mcp
igpsport-mcp --setup --lang en
```

> If `igpsport-mcp` is not found after installation, open a new terminal/PowerShell window so PATH updates take effect (uv places executables in `~/.local/bin` on macOS, `%USERPROFILE%\.local\bin` on Windows).

The wizard saves credentials to a config file (owner-readable only) and prints a **copy-paste ready** MCP configuration block. Config file locations:

- **macOS / Linux**: `~/.igpsport-mcp/config.json`
- **Windows**: `C:\Users\YourName\.igpsport-mcp\config.json`

**3. Paste the printed config into your client**, then restart the client.

> Want to verify your credentials before pasting? Run `igpsport-mcp --check --lang en`.
> Need to print the config snippet again later? `igpsport-mcp --mcp-config --lang en`.

## CLI Usage

| Command | Purpose |
|---|---|
| `igpsport-mcp --setup` | Interactive setup wizard: enter phone/email + password, saved to local config.json |
| `igpsport-mcp --mcp-config` | Print a copy-paste ready MCP client configuration block |
| `igpsport-mcp --check` | Perform a real login to verify credentials |
| `igpsport-mcp --lang en\|pt\|zh` | Set output language (also settable via `IGPSPORT_LANG` env var; default `zh`) |
| `igpsport-mcp --version` | Print version number |
| `igpsport-mcp --help` | Show help |

## Configuration (Environment Variables)

| Variable | Required | Description |
|---|---|---|
| `IGPSPORT_USERNAME` | ✅ | iGPSport account (phone number for CN / email for international) |
| `IGPSPORT_PASSWORD` | ✅ | Password |
| `IGPSPORT_REGION` | Optional | Region: `cn` (China server `app.igpsport.cn`) or `intl` (international server `app.igpsport.com`) |
| `IGPSPORT_FTP` | Optional | Functional Threshold Power in watts. **Auto-read from iGPSport profile**; set to override |
| `IGPSPORT_LTHR` | Optional | Lactate Threshold Heart Rate in bpm. **Auto-read from iGPSport profile**; set to override |
| `IGPSPORT_LANG` | Optional | Output language, `en`, `pt`, or `zh` (default `zh`) |
| `IGPSPORT_CACHE_DIR` | Optional | Cache directory |
| `IGPSPORT_LOG_LEVEL` | Optional | Default `INFO` |

## Available MCP Tools (17 tools)

- **Activities & Summary**: `list_activities`, `get_activity_summary`, `get_activity_laps`, `get_activity_streams`, `compare_activities`, `get_yearly_stats`, `get_personal_records`.
- **Advanced Training Analysis**: `analyze_training_load` (CTL/ATL/TSB), `estimate_thresholds` (MMP, FTP, LTHR).
- **Segments**: `list_starred_segments`, `get_segment_leaderboard`, `get_segment_efforts`.
- **Athlete**: `get_athlete_profile`.
- **Workouts**: `list_workouts`, `get_workout_detail`, `create_workout` (IR compilation for head unit), `delete_workout`.
