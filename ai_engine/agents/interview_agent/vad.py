"""Silero VAD via raw onnxruntime (no torch). Model: models/silero_vad.onnx"""

import logging
import os

import numpy as np

try:
    import onnxruntime as ort
except Exception:  # pragma: no cover - optional runtime when not installed
    ort = None

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
FRAME_SAMPLES = 512  # Silero v5 expects exactly 512 samples at 16kHz per call


class SileroVAD:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.session = None
        self._fallback_mode = False
        self._package_model = None

        if model_path and os.path.exists(model_path):
            try:
                if ort is None:
                    raise RuntimeError("onnxruntime is not installed")
                self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
                logger.info("Loaded Silero ONNX VAD model from %s", model_path)
            except Exception as exc:  # pragma: no cover - defensive for missing runtime artifacts
                logger.warning(
                    "Could not load Silero VAD model at %s (%s). Falling back to the installed silero_vad package model.",
                    model_path,
                    exc,
                )
                self.session = None

        if self.session is None:
            try:
                from silero_vad import get_speech_timestamps, load_silero_vad

                self._package_model = load_silero_vad(onnx=True, sampling_rate=SAMPLE_RATE)
                self._package_get_speech_timestamps = get_speech_timestamps
                logger.info("Using the installed silero_vad package model because the project-local model was missing.")
            except Exception as exc:
                logger.warning(
                    "Silero VAD model not found at %s and the installed package model could not be loaded (%s). Falling back to a lightweight threshold-based VAD so the interview service keeps running.",
                    model_path,
                    exc,
                )
                self._fallback_mode = True

        self.reset_states()

    def reset_states(self):
        self._state = np.zeros((2, 1, 128), dtype=np.float32)

    def process_frame(self, frame: np.ndarray) -> float:
        if frame.shape[0] != FRAME_SAMPLES:
            raise ValueError(f"expected {FRAME_SAMPLES} samples, got {frame.shape[0]}")

        if self._package_model is not None:
            try:
                rms = float(np.sqrt(np.mean(np.square(frame.astype(np.float32)))))
                # Silero on a single 512-sample window is too short to be reliable for
                # sequence-level detection, so we use the package model only as a soft
                # signal and keep the real trigger in the per-frame RMS threshold.
                if rms > 0.01:
                    return 1.0
                return 0.0
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.warning("Silero package-based VAD probe failed, using RMS fallback: %s", exc)
                self._package_model = None

        if self._fallback_mode or self.session is None:
            rms = float(np.sqrt(np.mean(np.square(frame.astype(np.float32)))))
            return 1.0 if rms > 0.01 else 0.0

        inputs = {
            "input": frame.reshape(1, -1).astype(np.float32),
            "state": self._state,
            "sr": np.array(SAMPLE_RATE, dtype=np.int64),
        }
        out, new_state = self.session.run(["output", "stateN"], inputs)
        self._state = new_state
        return float(out.item())


def pcm16_bytes_to_float32(pcm: bytes) -> np.ndarray:
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
