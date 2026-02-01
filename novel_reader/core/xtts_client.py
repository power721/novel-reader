import requests
from pathlib import Path

XTTS_URL = "http://127.0.0.1:9000/tts"


def xtts_tts(text: str, output_path: str) -> str:
    resp = requests.post(
        XTTS_URL,
        json={"text": text},
        timeout=300,
    )
    resp.raise_for_status()

    wav_path = resp.json()["wav_path"]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(wav_path).rename(output_path)

    return output_path
