import subprocess
import webrtcvad
import collections
import os
import time
import logging
import queue
import threading
import numpy as np
import torch
import librosa
import requests
from transformers import WhisperProcessor, WhisperForConditionalGeneration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_RATE = 8000
FRAME_DURATION_MS = 30
FRAME_DURATION_SEC = FRAME_DURATION_MS / 1000.0
FRAME_SIZE_BYTES = int(SAMPLE_RATE * 2 * FRAME_DURATION_SEC)
URL = "https://s1-fmt2.liveatc.net/epwa_app"
BUN_URL = "http://localhost:55524/process"
SEND_TIMEOUT_SEC = 10
STATS_INTERVAL_SEC = 10
FFMPEG_LOG_PATH = "/tmp/vetrenica/ffmpeg.log"

utterance_seq = 0


def next_utterance_id():
    global utterance_seq
    utterance_seq += 1
    return f"utt-{utterance_seq:06d}"


def audio_stats(audio_np):
    if audio_np.size == 0:
        return "samples=0 duration=0.00s rms=0.00000 peak=0.00000"

    rms = float(np.sqrt(np.mean(np.square(audio_np))))
    peak = float(np.max(np.abs(audio_np)))
    duration = audio_np.size / SAMPLE_RATE
    return f"samples={audio_np.size} duration={duration:.2f}s rms={rms:.5f} peak={peak:.5f}"


logger.info("Loading WhisperATC model...")
model = WhisperForConditionalGeneration.from_pretrained(
    "jlvdoorn/whisper-large-v3-atco2-asr", torch_dtype=torch.float32
)
model.eval()
processor = WhisperProcessor.from_pretrained("jlvdoorn/whisper-large-v3-atco2-asr")

if torch.cuda.is_available():
    model = model.cuda()
logger.info("Model loaded")

transcribe_queue = queue.Queue()


def send_transcription(utterance_id, transcription):
    send_started_at = time.monotonic()
    response = requests.post(
        BUN_URL,
        json={"text": transcription},
        timeout=SEND_TIMEOUT_SEC,
    )
    logger.info(
        "[%s] sent to bun: status=%s elapsed=%.3fs body=%r",
        utterance_id,
        response.status_code,
        time.monotonic() - send_started_at,
        response.text[:200],
    )


def transcribe_and_send(utterance_id, audio_np):
    started_at = time.monotonic()
    try:
        logger.info("[%s] transcribe start: %s", utterance_id, audio_stats(audio_np))
        resample_started_at = time.monotonic()
        audio_16k = librosa.resample(audio_np, orig_sr=SAMPLE_RATE, target_sr=16000)
        logger.info(
            "[%s] resampled audio: samples=%s duration=%.2fs elapsed=%.3fs",
            utterance_id,
            audio_16k.size,
            audio_16k.size / 16000,
            time.monotonic() - resample_started_at,
        )

        input_features = processor(
            audio_16k, sampling_rate=16000, return_tensors="pt"
        ).input_features
        logger.info(
            "[%s] processor features shape=%s",
            utterance_id,
            tuple(input_features.shape),
        )

        if torch.cuda.is_available():
            input_features = input_features.cuda()
            logger.info("[%s] moved features to cuda", utterance_id)

        with torch.no_grad():
            generate_started_at = time.monotonic()
            predicted_ids = model.generate(
                input_features, language="en", task="transcribe", max_new_tokens=256
            )
            logger.info(
                "[%s] model.generate complete: tokens=%s elapsed=%.3fs",
                utterance_id,
                predicted_ids.shape[-1],
                time.monotonic() - generate_started_at,
            )

        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[
            0
        ].strip()

        if transcription:
            logger.info(
                "[%s] transcription ready: chars=%s text=%r",
                utterance_id,
                len(transcription),
                transcription[:200],
            )
            send_transcription(utterance_id, transcription)
        else:
            logger.info("[%s] empty transcription, nothing sent", utterance_id)
    except Exception as e:
        logger.exception("[%s] error while transcribing/sending: %s", utterance_id, e)
    finally:
        logger.info(
            "[%s] transcribe flow done elapsed=%.3fs",
            utterance_id,
            time.monotonic() - started_at,
        )


def transcribe_worker():
    while True:
        utterance_id, audio_np = transcribe_queue.get()
        try:
            transcribe_and_send(utterance_id, audio_np)
        finally:
            transcribe_queue.task_done()


def spawn_ffmpeg(cmd):
    ffmpeg_log = open(FFMPEG_LOG_PATH, "ab")
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=ffmpeg_log)


def stop_ffmpeg(proc):
    if proc is None:
        return
    try:
        proc.kill()
    except OSError:
        pass
    proc.wait()


def run():
    worker_thread = threading.Thread(target=transcribe_worker, daemon=True)
    worker_thread.start()

    vad = webrtcvad.Vad(3)
    recording = []
    silence_count = 0
    is_recording = False
    current_utterance_id = None
    frame_count = 0
    speech_frame_count = 0
    last_stats_at = time.monotonic()

    pre_padding_frames = int(1.0 / FRAME_DURATION_SEC)
    post_padding_frames = int(2.0 / FRAME_DURATION_SEC)
    ring_buffer = collections.deque(maxlen=pre_padding_frames)

    cmd = ["ffmpeg", "-i", URL, "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-"]
    proc = spawn_ffmpeg(cmd)

    logger.info(
        "LiveATC stream %s sample_rate=%s frame_ms=%s frame_bytes=%s pre_padding=%s post_padding=%s ffmpeg_log=%s",
        URL,
        SAMPLE_RATE,
        FRAME_DURATION_MS,
        FRAME_SIZE_BYTES,
        pre_padding_frames,
        post_padding_frames,
        FFMPEG_LOG_PATH,
    )

    try:
        while True:
            pcm_data = proc.stdout.read(FRAME_SIZE_BYTES)
            if len(pcm_data) != FRAME_SIZE_BYTES:
                logger.info(
                    "Stream ended or short read, restarting: got=%s expected=%s recording=%s buffered_frames=%s",
                    len(pcm_data),
                    FRAME_SIZE_BYTES,
                    is_recording,
                    len(recording),
                )
                stop_ffmpeg(proc)
                time.sleep(1)
                proc = spawn_ffmpeg(cmd)
                ring_buffer = collections.deque(maxlen=pre_padding_frames)
                recording = []
                is_recording = False
                silence_count = 0
                current_utterance_id = None
                continue

            frame_count += 1
            ring_buffer.append(pcm_data)
            is_speech = vad.is_speech(pcm_data, SAMPLE_RATE)
            if is_speech:
                speech_frame_count += 1

            now = time.monotonic()
            if now - last_stats_at >= STATS_INTERVAL_SEC:
                logger.info(
                    "vad stats: frames=%s speech_frames=%s recording=%s ring=%s recording_frames=%s silence_frames=%s queue=%s",
                    frame_count,
                    speech_frame_count,
                    is_recording,
                    len(ring_buffer),
                    len(recording),
                    silence_count,
                    transcribe_queue.qsize(),
                )
                frame_count = 0
                speech_frame_count = 0
                last_stats_at = now

            if is_recording:
                recording.append(pcm_data)
                if is_speech:
                    silence_count = 0
                else:
                    silence_count += 1
                    if silence_count > post_padding_frames:
                        logger.info(
                            "[%s] utterance end: frames=%s silence_frames=%s queue=%s",
                            current_utterance_id,
                            len(recording),
                            silence_count,
                            transcribe_queue.qsize(),
                        )
                        audio_np = (
                            np.frombuffer(b"".join(recording), dtype=np.int16).astype(
                                np.float32
                            )
                            / 32768.0
                        )
                        transcribe_queue.put((current_utterance_id, audio_np))
                        recording = []
                        is_recording = False
                        silence_count = 0
                        current_utterance_id = None
            else:
                if is_speech:
                    current_utterance_id = next_utterance_id()
                    recording = list(ring_buffer)
                    ring_buffer = collections.deque(maxlen=pre_padding_frames)
                    recording.append(pcm_data)
                    is_recording = True
                    silence_count = 0
                    logger.info(
                        "[%s] utterance start: pre_padding_frames=%s first_speech_frame=%s",
                        current_utterance_id,
                        len(recording) - 1,
                        frame_count,
                    )
    finally:
        logger.info("shutting down, stopping ffmpeg")
        stop_ffmpeg(proc)


if __name__ == "__main__":
    os.makedirs("/tmp/vetrenica", exist_ok=True)
    run()
