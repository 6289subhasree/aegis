"""Download the Whisper model once, so the demo works with no internet.

    python -m app.tools.download_models            # uses WHISPER_MODEL (default: small)
    python -m app.tools.download_models medium     # or name a size
"""

import sys

from ..config import get_settings


def main() -> None:
    size = sys.argv[1] if len(sys.argv) > 1 else get_settings().whisper_model
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper is not installed. Run: pip install -r requirements-ml.txt")
    print(f"Downloading Whisper '{size}' (one time, needs internet)...")
    WhisperModel(size, device="cpu", compute_type="int8")
    print("Done. The model is cached on this computer; no internet is needed from now on.")


if __name__ == "__main__":
    main()
