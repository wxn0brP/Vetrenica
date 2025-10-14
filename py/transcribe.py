from faster_whisper import WhisperModel
import os
from sys import argv

filename = "segments/" + argv[1] + ".wav"
if not os.path.exists(filename):
    print("File not found: ", filename)
    exit(1)

print("Read file: ", filename)
model = WhisperModel("medium", compute_type="float32")
segments, info = model.transcribe(filename, beam_size=5)

print("== Result ==")
for segment in segments:
    print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
