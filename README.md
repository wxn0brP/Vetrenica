# Vetrenica

This project monitors live ATC (Air Traffic Control) radio feeds from **Warsaw Chopin Airport (EPWA)**, transcribes the audio in real-time using Whisper AI, and provides an API for processing audio segments.

## Features

- Real-time monitoring of ATC radio feeds from EPWA (Warsaw)
- Live audio transcription using Faster Whisper
- Automatic aircraft identification based on transcription and nearby traffic
- API for processing audio segments
- Web interface for real-time interaction
- SSE (Server-Sent Events) for live updates

## Setup

Requires Python 3.12+ and ffmpeg.

```bash
./setup.sh
```

The script creates a `.venv`, installs Python dependencies from `requirements.txt`, and verifies ffmpeg availability. Then run:

```bash
# terminal 1: API server
bun run src/index.ts

# terminal 2: live transcription pipeline
.venv/bin/python py/live.py
```

## How It Works

The project consists of three main components:

1. **Live Transcription (Python)**: The `live.py` script streams live ATC audio from LiveATC.net for EPWA, detects voice activity using WebRTC VAD, and transcribes utterances in-process using the Whisper ATC model. Finished transcriptions are sent to the Bun API.
2. **Processing API (Bun)**: A web API that receives transcriptions, identifies the aircraft, and pushes updates to connected clients.
3. **Aircraft Identification**: Uses OpenSky Network API to fetch nearby aircraft and Ollama LLM to match the speaker with the aircraft call sign.

### Data Sources

| Service | URL | Purpose |
|---------|-----|---------|
| LiveATC.net | `https://s1-fmt2.liveatc.net/epwa_app` | Live ATC radio stream for Warsaw Chopin (EPWA) |
| OpenSky Network | `https://opensky-network.org/api/states/all` | Real-time aircraft positions near EPWA |
| Ollama | `http://localhost:11434/api/generate` | LLM for aircraft identification from transcription |

## API Endpoints

### Bun API (Port 55524)

The main API server built with FalconFrame.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves the main web interface |
| `/process` | POST | Processes a new transcription (JSON body) |
| `/process` | GET | Processes a new transcription (query param, for quick tests) |
| `/live` | WebSocket | SSE endpoint for real-time transcription updates |

#### `/process` Parameters

- `text` (required): The transcription text to process
- Example: `POST /process` with body `{"text": "LOT one two three, runway two four"}`

#### WebSocket `/`

Connects via WebSocket to receive real-time transcription updates. Events include:
- `data`: Transcription result with segments and identified speaker

## Architecture

```
|-----------------|
|  LiveATC.net    |  (https://s1-fmt2.liveatc.net/epwa_app)
|   EPWA Stream   |
|-----------------|
         |
         |
        \ /
|-----------------|
|   live.py       |  (VAD + Whisper transcription,
|  Python Script  |   single worker queue)
|--------|--------|
         | POST /process {"text": "..."}
        \ /
|-------------------|
|   Bun API         |  (Port 55524)
| /process endpoint |
|--------|----------|
         |
    |-------------|
    |             |
   \ /           \ /
|-----------| |--------------|
| OpenSky   | | Ollama       |
| Aircraft  | | Speaker ID   |
| Positions | | (LLM)        |
|-----------| |--------------|
    |              |
    |------|-------|
           |
          \ /
    |-----------------------|
    | WebSocket clients     |
    | (transcript + speaker)|
    |-----------------------|
```

## License

MIT
