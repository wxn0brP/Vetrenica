# Vetrenica

This project monitors live ATC (Air Traffic Control) radio feeds from **Warsaw Chopin Airport (EPWA)**, transcribes the audio in real-time using Whisper AI, and provides an API for processing audio segments.

## Features

- Real-time monitoring of ATC radio feeds from EPWA (Warsaw)
- Live audio transcription using Faster Whisper
- Automatic aircraft identification based on transcription and nearby traffic
- API for processing audio segments
- Web interface for real-time interaction
- SSE (Server-Sent Events) for live updates

## How It Works

The project consists of three main components:

1. **Live Monitoring (Python)**: The `split.py` script streams live ATC audio from LiveATC.net for EPWA, detects voice activity using WebRTC VAD, and saves audio segments to the `segments/` directory.
2. **Segment Processing API (Bun + Python)**: A web API for processing pre-recorded audio segments.
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
| `/new` | GET | Processes a new audio segment |
| `/live` | WebSocket | SSE endpoint for real-time transcription updates |

#### `/new` Parameters

- `id` (required): Filename of the WAV file (without extension) in the `segments/` directory
- Example: `GET /new?id=1234`

#### WebSocket `/`

Connects via WebSocket to receive real-time transcription updates. Events include:
- `data`: Transcription result with segments

### Python Transcription API (Port 55523)

Flask-based server for audio transcription using Faster Whisper.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Transcribes an audio file |

#### `/` Parameters

- `id` (required): Filename of the WAV file (without extension) in the `segments/` directory
- Example: `GET /?id=1234`

#### Response Format

```json
{
  "status": "success",
  "filename": "1234",
  "segments": [
    {
      "start": 0.0,
      "end": 5.5,
      "text": "Transcribed text here"
    }
  ]
}
```

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
|   split.py      |  (Voice Activity Detection)
|  Python Script  |
|--------|--------|
         | saves WAV to /tmp/vetrenica/segments/
         |
        \ /
|-----------------|
|   Bun API       |  (Port 55524)
|  /new endpoint  |
|--------|--------|
         |
    |-------------|
    |             |
   \ /           \ /
|--------| |--------------|
| Python | | OpenSky API  |
| Flask  | | Aircraft     |
| Whisper| | Positions    |
|--------| |--------------|
    |              |
    |------|-------|
           |
          \ /
    |--------------|
    |   Ollama     |
    |  (LLM)       |
    |--------------|
           |
     |-------------|
     |             |
    \ /           \ /
|-----------| |---------|
| Frontend  | | Open    |
| WebSocket | | Flight  |
|           | | Radar   |
|-----------| |---------|
```

## License

MIT
