"""Voice endpoint tests use a fake speech-to-text backend, so no model download is needed.
The real Whisper adapter is exercised manually with `python -m app.tools.transcribe`."""

import pytest

from app.api import reports as reports_api
from app.services.stt import Transcript

AUDIO = {"audio": ("clip.webm", b"fake-audio-bytes", "audio/webm")}


class FakeSTT:
    def __init__(self, transcript: Transcript):
        self.transcript = transcript
        self.calls = []

    def transcribe(self, audio, language=None):
        self.calls.append((audio, language))
        return self.transcript


@pytest.fixture()
def hindi(monkeypatch):
    fake = FakeSTT(
        Transcript(
            text="छत पर पाँच लोग फँसे हैं, पानी तेज़ी से बढ़ रहा है",
            english="Five people are trapped on the roof, water rising fast",
            language="hi",
        )
    )
    monkeypatch.setattr(reports_api, "get_stt", lambda: fake)
    return fake


def test_hindi_voice_report_is_translated_ranked_and_keeps_original(client, hindi):
    r = client.post("/reports/voice", files=AUDIO, data={"lat": "21.94", "lon": "88.86", "language": "hi"})
    assert r.status_code == 201
    body = r.json()
    assert body["language"] == "hi"
    assert "छत" in body["transcript"]  # the original is preserved for responders
    assert "trapped" in body["english"].lower()
    assert body["report"]["channel"] == "voice"
    assert body["report"]["original_text"] == body["transcript"]
    assert body["report"]["translated_text"] == body["english"]
    assert body["incident"]["effective_tier"] == "CRITICAL"  # scored from the English text
    assert hindi.calls[0][1] == "hi"  # the language hint reached the STT backend


def test_voice_and_text_reports_of_same_incident_merge(client, hindi):
    client.post(
        "/reports",
        json={"text": "5 people stuck on rooftop, water rising fast, please help", "lat": 21.94, "lon": 88.86},
    )
    r = client.post("/reports/voice", files=AUDIO, data={"lat": "21.941", "lon": "88.861"}).json()
    assert r["merged"] is True
    assert r["incident"]["report_count"] == 2
    assert len(client.get("/incidents").json()) == 1


def test_silent_recording_is_rejected(client, monkeypatch):
    monkeypatch.setattr(
        reports_api, "get_stt", lambda: FakeSTT(Transcript(text="", english="", language="en"))
    )
    r = client.post("/reports/voice", files=AUDIO)
    assert r.status_code == 422
    assert client.get("/incidents").json() == []


def test_empty_and_oversized_uploads_rejected(client, hindi, monkeypatch):
    assert client.post("/reports/voice", files={"audio": ("a.webm", b"", "audio/webm")}).status_code == 422
    monkeypatch.setattr(reports_api, "MAX_AUDIO_BYTES", 4)
    assert client.post("/reports/voice", files=AUDIO).status_code == 413


def test_voice_without_whisper_gives_clear_501(client):
    r = client.post("/reports/voice", files=AUDIO)
    assert r.status_code == 501
    assert "STT_BACKEND=whisper" in r.json()["detail"]


def test_original_text_is_kept_for_text_reports_too(client):
    body = client.post("/reports", json={"text": "Bridge collapsed, village cut off"}).json()
    assert body["report"]["original_text"] == "Bridge collapsed, village cut off"


class _Seg:
    def __init__(self, text):
        self.text = text


class _Info:
    def __init__(self, language):
        self.language = language


def _fake_whisper_model(calls, heard_lang, results):
    class FakeModel:
        def __init__(self, *a, **kw):
            pass

        def transcribe(self, audio, task, language, vad_filter, beam_size):
            calls.append({"task": task, "language": language, "vad": vad_filter})
            return [_Seg(results[task])], _Info(heard_lang)

    return FakeModel


try:
    import faster_whisper
    HAS_FASTER_WHISPER = True
except ImportError:
    faster_whisper = None  # type: ignore
    HAS_FASTER_WHISPER = False


@pytest.mark.skipif(not HAS_FASTER_WHISPER, reason="faster_whisper not installed; install requirements-voice.txt")
def test_whisper_adapter_runs_translate_pass_only_for_non_english(monkeypatch):
    from app.services.stt import WhisperSTT

    calls = []
    monkeypatch.setattr(
        faster_whisper,
        "WhisperModel",
        _fake_whisper_model(calls, "hi", {"transcribe": " हिंदी पाठ ", "translate": " English text "}),
    )
    tr = WhisperSTT().transcribe(b"x", "hi")
    assert (tr.text, tr.english, tr.language) == ("हिंदी पाठ", "English text", "hi")
    assert [c["task"] for c in calls] == ["transcribe", "translate"]
    assert all(c["vad"] for c in calls)  # silence filtering on


@pytest.mark.skipif(not HAS_FASTER_WHISPER, reason="faster_whisper not installed; install requirements-voice.txt")
def test_whisper_adapter_single_pass_for_english(monkeypatch):
    from app.services.stt import WhisperSTT

    calls = []
    monkeypatch.setattr(
        faster_whisper, "WhisperModel", _fake_whisper_model(calls, "en", {"transcribe": "Help, flood"})
    )
    tr = WhisperSTT().transcribe(b"x")
    assert (tr.text, tr.english, tr.language) == ("Help, flood", "Help, flood", "en")
    assert [c["task"] for c in calls] == ["transcribe"]
