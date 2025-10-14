from faster_whisper import WhisperModel
from flask import Flask, request, jsonify
import os
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
SEGMENTS_DIR = "segments"

try:
    logger.info("Loading Whisper model...")
    model = WhisperModel("medium", compute_type="float32")
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    model = None

def validate_filename(filename: str) -> str:
    """
    Validate filename to prevent path traversal attacks
    and ensure it's a valid WAV file in segments directory
    """
    if '/' in filename or '\\' in filename or '..' in filename:
        raise ValueError("Invalid filename")
    
    if not filename.endswith('.wav'):
        filename += '.wav'
    
    full_path = os.path.join(SEGMENTS_DIR, filename)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"File not found: {filename}")
    
    if not os.path.realpath(full_path).startswith(os.path.realpath(SEGMENTS_DIR) + os.sep):
        raise ValueError("Access denied")
    
    return full_path

def transcribe_audio(filename: str) -> List[Dict[str, Any]]:
    """
    Transcribe audio file using Whisper model
    """
    logger.info(f"Transcribing file: {filename}")
    
    try:
        segments, info = model.transcribe(filename, beam_size=5)
        
        result = []
        for segment in segments:
            result.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip()
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise

@app.route('/', methods=['GET'])
def transcribe_endpoint():
    """
    Endpoint for audio transcription
    GET /?id=filename (bez ścieżki i rozszerzenia)
    """
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500
    
    filename = request.args.get('id')
    
    if not filename:
        return jsonify({"error": "Missing 'id' parameter"}), 400
    
    if not filename.strip():
        return jsonify({"error": "Filename cannot be empty"}), 400
    
    try:
        full_path = validate_filename(filename)
        segments = transcribe_audio(full_path)
        
        return jsonify({
            "status": "success",
            "filename": filename,
            "segments": segments
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
        
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
        
    except Exception as e:
        logger.error(f"Server error: {e}")
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    if not os.path.exists(SEGMENTS_DIR):
        logger.warning(f"Directory '{SEGMENTS_DIR}' does not exist. Creating...")
        os.makedirs(SEGMENTS_DIR)
    
    logger.info("Starting HTTP server on port 55523...")
    logger.info(f"Serving files from: {os.path.abspath(SEGMENTS_DIR)}")
    app.run(host='0.0.0.0', port=55523, debug=False)
