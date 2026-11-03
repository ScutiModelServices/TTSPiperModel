import asyncio

import pytest

from conftest import make_engine
from engine import EngineError, PiperEngine, Voice, parse_voices, voice_file


def speak(engine, text="hello", voice=None, speed=1.0):
    return asyncio.run(engine.synthesize(text, voice, speed))


def test_voice_file_follows_the_repository_layout():
    assert voice_file("en_US-lessac-medium") == "en/en_US/lessac/medium/en_US-lessac-medium"
    assert voice_file("de_DE-thorsten_emotional-medium") == "de/de_DE/thorsten_emotional/medium/de_DE-thorsten_emotional-medium"


def test_voice_lists_are_checked():
    assert parse_voices(" en_US-lessac-medium , en_GB-alba-low ") == ["en_US-lessac-medium", "en_GB-alba-low"]
    for bad in ("", " , ", "lessac", "../x-y-medium", "en_US-lessac-huge"):
        with pytest.raises(ValueError):
            parse_voices(bad)


def test_the_default_voice_is_the_first_and_loads_once():
    engine = make_engine()
    assert engine.default_voice == "en_US-lessac-medium" and not engine.ready
    first = speak(engine)
    speak(engine, "again")
    assert first["voice"] == "en_US-lessac-medium" and first["seconds"] == 0.5 and first["wav"][:4] == b"RIFF"
    assert engine.loads == [("en_US-lessac-medium", None)] and engine.ready
    assert [call["text"] for call in engine.made[0].calls] == ["hello", "again"]


def test_another_served_voice_loads_by_itself_and_an_unknown_one_is_404():
    engine = make_engine()
    assert speak(engine, voice="en_GB-alba-medium")["voice"] == "en_GB-alba-medium"
    assert engine.loads == [("en_GB-alba-medium", None)]
    with pytest.raises(EngineError) as error:
        speak(engine, voice="en_US-ryan-high")
    assert error.value.status == 404


def test_the_voices_can_change_while_running():
    engine = make_engine()
    engine.voices = "en_US-ryan-high"
    assert engine.voices == ["en_US-ryan-high"] and engine.default_voice == "en_US-ryan-high"
    with pytest.raises(ValueError):
        engine.voices = "nonsense"
    assert engine.voices == ["en_US-ryan-high"]


def test_speed_reaches_the_voice():
    engine = make_engine()
    speak(engine, speed=1.5)
    assert engine.made[0].calls[0]["speed"] == 1.5


def test_changing_the_threads_reloads_with_the_new_count():
    engine = make_engine()
    speak(engine)
    engine.num_thread = 3
    engine.num_thread = 3  # same value: nothing to drop
    speak(engine)
    assert engine.loads == [("en_US-lessac-medium", None), ("en_US-lessac-medium", 3)]


def test_a_new_download_by_another_replica_drops_the_loaded_voices(tmp_path):
    marker = tmp_path / "marker"
    one, two = make_engine(marker=marker), make_engine(marker=marker)
    speak(one)
    asyncio.run(two.unload())
    one.sync()
    assert not one.ready
    speak(one)
    assert len(one.loads) == 2


def test_the_revision_calls_use_the_repository():
    engine = make_engine(cached_sha=lambda repo: f"cached-{repo}", remote_sha=lambda repo: f"latest-{repo}")
    assert asyncio.run(engine.cached_sha()) == "cached-m" and asyncio.run(engine.remote_sha()) == "latest-m"


def test_voice_writes_a_wav_with_the_speed_as_length_scale():
    class Piper:
        scale = None

        def synthesize_wav(self, text, wav, syn_config):
            Piper.scale = syn_config.length_scale
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(22050)
            wav.writeframes(b"\0\0" * 22050)

    wav, seconds = Voice(Piper()).speak("hi", 2.0)
    assert Piper.scale == 0.5 and seconds == 1.0 and wav[:4] == b"RIFF"
