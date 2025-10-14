# Vetrenica

This project monitors live ATC (Air Traffic Control) radio feeds, transcribes the audio in real-time using Whisper AI, and provides an API for processing audio segments.

## Features

- Real-time monitoring of ATC radio feeds
- Live audio transcription using Faster Whisper
- API for processing audio segments
- Web interface for interaction

## How It Works

The project consists of two main components:

1. **Live Monitoring (Python)**: The `split.py` script streams live ATC audio from predefined URLs, and saves audio segments to the `segments/` directory.
2. **Segment Processing API (Bun + Python)**: A web API for processing pre-recorded audio segments.

### Segment Processing API

The system uses two services:

1. **Bun API** (`src/index.ts`): 
   - Serves a web interface at `/`
   - SSE endpoint at `/live`
   - Provides a processing endpoint at `/new?id=filename`
   - Communicates with the Python transcription service

2. **Python Transcription Service** (`ts.py`):
   - Flask-based HTTP server running on port 55523
   - Provides a transcription endpoint at `GET /?id=filename`
   - Uses Faster Whisper model to transcribe WAV files in the `segments/` directory

## API Endpoints

### Bun FalconFrame API

- `GET /` - Serves the main web interface
- `GET /new` - Processes a new audio segment
  - Parameter: `id` - filename of the WAV file (without extension) in the `segments/` directory
  - Example: `GET /new?id=1`

### Python Transcription API

- `GET /` - Transcribes an audio file
  - Parameter: `id` - filename of the WAV file (without extension) in the `segments/` directory
  - Example: `GET /?id=1`
  - Response:
    ```json
    {
      "status": "success",
      "filename": "1",
      "segments": [
        {
          "start": 0.0,
          "end": 5.5,
          "text": "Transcribed text here"
        }
      ]
    }
    ```


## License

MIT