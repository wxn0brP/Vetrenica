import subprocess
import webrtcvad
import collections
import wave
import os
import time
import sys
import requests
import threading

output_dir = "/tmp/vetrenica/segments"
if not os.path.exists(output_dir):
    subprocess.run(["mkdir", "-p", output_dir])

def _fire_and_forget(url: str) -> None:
    """Performs a GET request and ignores any errors."""
    try:
        requests.get(url, timeout=3)
    except Exception:
        pass

def notify(filename: str, port: int = 55524) -> None:
    """Performs a "fire and forget" request to localhost."""
    url = f"http://localhost:{port}/new?id={filename}"
    threading.Thread(target=_fire_and_forget, args=(url,), daemon=True).start()

def main(url, before=1, after=2.0):
    global output_dir
    
    # Audio parameters
    sample_rate = 8000  # 8 kHz, typical for LiveATC
    frame_duration_ms = 30  # ms, supported by webrtcvad: 10,20,30
    frame_duration_sec = frame_duration_ms / 1000.0
    frame_size_bytes = int(sample_rate * 2 * frame_duration_sec)  # 16-bit mono: 8000 * 2 * 0.03 = 480 bytes

    # Padding in number of frames
    pre_padding_frames = int(before / frame_duration_sec)  # 0.5s before
    post_padding_frames = int(after / frame_duration_sec)  # 1s after

    # VAD
    vad = webrtcvad.Vad(3)  # Aggressiveness level: 0-3, 3 being the most aggressive

    # Ring buffer for pre-padding (last 0.5s)
    ring_buffer = collections.deque(maxlen=pre_padding_frames)

    # Buffer for recording
    recording = []
    silence_count = 0
    is_recording = False

    # Start ffmpeg to stream and convert to raw PCM (s16le, 8kHz, mono)
    cmd = [
        'ffmpeg',
        '-i', url,
        '-f', 's16le',
        '-ar', str(sample_rate),
        '-ac', '1',
        '-'  # Output to stdout
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    print(f"LiveATC stream {url}...")

    while True:
        # Read frame
        pcm_data = proc.stdout.read(frame_size_bytes)
        if len(pcm_data) != frame_size_bytes:
            print("End of stream or error.")
            break

        # Add to ring buffer (idle)
        ring_buffer.append(pcm_data)

        # Check VAD
        is_speech = vad.is_speech(pcm_data, sample_rate)

        if is_recording:
            recording.append(pcm_data)
            if is_speech:
                silence_count = 0
            else:
                silence_count += 1
                if silence_count > post_padding_frames:
                    # Save segment
                    current_time = str(int(time.time()))[-4:]
                    filename = os.path.join(output_dir, f"{current_time}.wav")
                    save_wav(filename, recording, sample_rate)
                    print(f"Save segment: {filename}")
                    notify(f"{current_time}")
                    recording = []
                    is_recording = False
                    silence_count = 0
                    # Ring buffer continues, as there may be a new voice soon
        else:
            if is_speech:
                # Start recording: add ring buffer + current frame
                recording = list(ring_buffer) + [pcm_data]
                is_recording = True
                silence_count = 0

def save_wav(filename, frames, sample_rate):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

if __name__ == "__main__":
    url = "https://s1-fmt2.liveatc.net/epwa_app"
    main(url)

