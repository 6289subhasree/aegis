"""Check speech recognition quality on a recording, without starting the server.

    python -m app.tools.transcribe recording.wav
    python -m app.tools.transcribe recording.wav hi      # hint the language

Prints what was heard in the original language and the English version that the system will
use. Use it to test Hindi accuracy before the demo; if "small" mishears, try WHISPER_MODEL=medium.
"""

import sys
import time
from pathlib import Path

from ..services.extraction import extract
from ..services.stt import WhisperSTT


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    language = sys.argv[2] if len(sys.argv) > 2 else None

    stt = WhisperSTT()
    t0 = time.time()
    tr = stt.transcribe(path.read_bytes(), language)
    secs = time.time() - t0

    print(f"language : {tr.language}")
    print(f"heard    : {tr.text}")
    print(f"english  : {tr.english}")
    ex = extract(tr.english)
    print(f"signals  : type={ex.incident_type} people={ex.people} life={ex.life} urgency={ex.urgency} isolation={ex.isolation}")
    print(f"time     : {secs:.1f}s")


if __name__ == "__main__":
    main()
