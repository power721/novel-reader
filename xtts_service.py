import os
import torch
from fastapi import FastAPI
from pydantic import BaseModel
from TTS.api import TTS
import soundfile as sf
import uuid
from pathlib import Path

# ==================== 配置 ====================

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
OUTPUT_DIR = Path("data/xtts_audio")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

USE_GPU = torch.cuda.is_available()
print(f"Using GPU: {USE_GPU}")

# ==================== 初始化 ====================

print("🔊 Loading XTTS model...")
tts = TTS(model_name=MODEL_NAME, gpu=True)
print("✅ XTTS loaded")

# 可选：speaker（不传就是默认）
DEFAULT_SPEAKER_WAV = "data/news.wav"

# ==================== API ====================

app = FastAPI()


class TTSRequest(BaseModel):
    text: str
    speaker_wav: str | None = None


class TTSResponse(BaseModel):
    wav_path: str


@app.post("/tts", response_model=TTSResponse)
def tts_endpoint(req: TTSRequest):
    text = req.text.strip()
    if not text:
        raise ValueError("empty text")

    out_file = OUTPUT_DIR / f"{uuid.uuid4().hex}.wav"

    tts.tts_to_file(
        text=text,
        speaker_wav=DEFAULT_SPEAKER_WAV,
        language="zh",
        file_path=str(out_file),
        temperature=0.2,  # 🔥 核心
        repetition_penalty=5.0,
        speed=1.0
    )

    return TTSResponse(wav_path=str(out_file))


# ==================== Warmup ====================

@app.on_event("startup")
def warmup():
    print("🔥 XTTS warmup...")
    tts.tts_to_file(
        text="系统初始化完成。",
        file_path=str(OUTPUT_DIR / "_warmup.wav"),
        speaker_wav=DEFAULT_SPEAKER_WAV,
        language="zh"
    )
    print("🔥 XTTS warmup done")
