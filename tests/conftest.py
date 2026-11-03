import io
import wave

import pytest

from engine import PiperEngine


@pytest.fixture(autouse=True)
def _tmp_tokens_file(tmp_path, monkeypatch):
    """Keeps tokens.json and settings.json out of the repo, and a saved setting from leaking into the next test."""
    monkeypatch.setenv("TTSPIPER_TOKENS_FILE", str(tmp_path / "tokens.json"))


def silence(seconds: float = 0.5, rate: int = 22050) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\0\0" * int(seconds * rate))
    return buf.getvalue()


class FakeVoice:
    """Stands in for a loaded voice: answers half a second of silence and records every call."""

    rate = 22050

    def __init__(self, name, threads):
        self.name, self.threads, self.calls = name, threads, []

    def speak(self, text, speed):
        self.calls.append({"text": text, "speed": speed})
        return silence(), 0.5

    def pieces(self, text, speed):
        """One 0.1 s piece per sentence, as the real voice does."""
        self.calls.append({"text": text, "speed": speed, "stream": True})
        for sentence in [s for s in text.split(".") if s.strip()]:
            yield b"\1\0" * (self.rate // 10)


def make_engine(**options):
    """An engine whose loader builds FakeVoice voices; `engine.loads` lists the (voice, threads) it was asked for."""
    loads = []

    def loader(repo, name, threads):
        loads.append((name, threads))
        voice = FakeVoice(name, threads)
        loaded.append(voice)
        return voice

    loaded = []
    if "cached_sha" in options:
        old = options["cached_sha"]
        options["cached_sha"] = lambda repo, voice: old(repo)
    if "download" in options:
        old_download = options["download"]
        options["download"] = lambda repo, voices: old_download(repo)
    options.setdefault("loader", loader)
    engine = PiperEngine("m", options.pop("voices", "en_US-lessac-medium,en_GB-alba-medium"), **options)
    engine.loads, engine.made = loads, loaded
    return engine
