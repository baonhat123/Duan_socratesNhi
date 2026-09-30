"""
Module: voice_service.py
Chức năng 1 (FR-01 Mở rộng): Nhận diện giọng nói KHTN (Speech-to-Text)
Đặc tả dự án: Socrates Nhí v3.0 (Mục 2.2 & Mục 22 - Lộ trình nâng cấp)

Tính năng chuyên biệt cho học sinh THCS:
1. Thu âm Microphone trực tiếp thời gian thực (sounddevice + numpy).
2. Tự động chuyển đổi âm thanh thành văn bản tiếng Việt:
   - Ưu tiên: OpenAI Whisper API (whisper-1).
   - Fallback tự động: Google Speech Recognition tiếng Việt (vi-VN, miễn phí, không cần API key).
3. Bộ chuẩn hóa phát âm thuật ngữ Khoa học Tự nhiên tiếng Việt sang ký hiệu quốc tế:
   - "ki lô mét trên giờ" ➜ "km/h"
   - "mét trên giây" ➜ "m/s"
   - "ki lô gam" ➜ "kg"
   - "niu tơn" ➜ "N"
   - "ô-xy-gen" / "khí o2" ➜ "oxygen (O₂)"
   - "các-bon đi-ô-xít" / "khí co2" ➜ "carbon dioxide (CO₂)"
   - "nước" / "hát hai ô" ➜ "H₂O"
4. Bộ mô phỏng phát âm mẫu (Demo Voice Presets) giúp chạy thử nghiệm khi không có microphone hoặc thi offline.
"""

import os
import re
import time
import wave
import tempfile
import threading
from typing import Optional, List, Dict, Tuple
from pathlib import Path

from .input_model import ProblemInput, InputType
from .validator import check_pii_and_safety

# Bản đồ chuẩn hóa phát âm giọng nói sang ký hiệu chuẩn SGK KHTN 7
SPOKEN_KHTN_REPLACEMENTS = [
    (r"\bki\s*lô\s*mét\s*trên\s*giờ\b", "km/h"),
    (r"\bki\s*lô\s*mét\b", "km"),
    (r"\bmét\s*trên\s*giây\b", "m/s"),
    (r"\bmét\b", "m"),
    (r"\bki\s*lô\s*gam\b", "kg"),
    (r"\bniu\s*tơn\b", "N"),
    (r"\bcan\s*xi\s*các\s*bo\s*nát\b", "CaCO3"),
    (r"\baxit\s*clohydric\b", "HCl"),
    (r"\baxit\s*sunfuric\b", "H2SO4"),
    (r"\bhát\s*hai\s*ét\s*ô\s*bốn\b", "H2SO4"),
    (r"\bna\s*tri\s*clo\s*rua\b", "NaCl"),
    (r"\bkhí\s*các\s*bon\s*níc\b", "CO2"),
    (r"\bô\s*xy\s*gen\b", "oxygen (O₂)"),
    (r"\bô\s*xy\b", "O₂"),
    (r"\bcác\s*bon\s*đi\s*ô\s*xít\b", "carbon dioxide (CO₂)"),
    (r"\bcác\s*bon\b", "carbon (C)"),
    (r"\bhát\s*hai\s*ô\b", "H₂O"),
    (r"\bđộ\s*cê\b", "°C"),
    (r"\bđộ\s*xê\b", "°C"),
    (r"\bvận\s*tốc\s*vê\b", "tốc độ v"),
    (r"\btốc\s*độ\s*vê\b", "tốc độ v"),
    (r"\bquãng\s*đường\s*ét\b", "quãng đường s"),
    (r"\bthời\s*gian\s*tê\b", "thời gian t"),
    (r"\bkhối\s*lượng\s*em\b", "khối lượng m"),
    (r"\btrọng\s*lượng\s*pê\b", "trọng lượng P")
]

# Các mẫu câu phát âm thử nghiệm chuẩn bị sẵn phục vụ biểu diễn Demo lúc thi
DEMO_VOICE_PRESETS: List[Dict[str, str]] = [
    {
        "id": "voice_vl",
        "strand": "Vật lý",
        "title": "Vật lý: Tốc độ xe đạp",
        "raw_speech": "Một người đi xe đạp chuyển động đều trên quãng đường thẳng dài mười hai ki lô mét trong thời gian ba mươi phút. Hãy tính tốc độ của người đó theo đơn vị ki lô mét trên giờ và mét trên giây.",
        "icon": "directions_bike_rounded"
    },
    {
        "id": "voice_hh",
        "strand": "Hóa học",
        "title": "Hóa học: Đốt than bảo toàn khối lượng",
        "raw_speech": "Đốt cháy hoàn toàn sáu gam bột than carbon trong bình chứa khí ô xy gen. Sau phản ứng thu được hai mươi hai gam khí các bon đi ô xít. Hãy tính khối lượng khí ô xy gen đã tham gia phản ứng.",
        "icon": "local_fire_department_rounded"
    },
    {
        "id": "voice_sh",
        "strand": "Sinh học",
        "title": "Sinh học: Quang hợp và Thoát hơi nước",
        "raw_speech": "Giải thích vì sao vào những ngày nắng gắt đứng dưới bóng mát của tán cây xanh ta lại cảm thấy dễ chịu hơn so với đứng dưới mái tôn? Nêu vai trò của quá trình quang hợp và thoát hơi nước.",
        "icon": "eco_rounded"
    }
]


def normalize_spoken_khtn(raw_text: str) -> str:
    """
    Chuẩn hóa văn bản nhận diện từ giọng nói sang thuật ngữ và ký hiệu chuẩn KHTN.
    """
    result = raw_text
    for pattern, replacement in SPOKEN_KHTN_REPLACEMENTS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result.strip()


class SystemAudioRecorder:
    """
    Bộ thu âm microphone thời gian thực sử dụng sounddevice + numpy.
    Hoạt động phi đồng bộ (background thread) an toàn, không gián đoạn giao diện.
    """
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self._frames = []
        self._stream = None
        self._lock = threading.Lock()
        self._start_time = 0.0

    def start_recording(self) -> Tuple[bool, str]:
        """
        Bắt đầu ghi âm từ microphone hệ thống.
        Trả về (success: bool, message: str)
        """
        with self._lock:
            if self.is_recording:
                return True, "Đang ghi âm..."
            try:
                import sounddevice as sd
                self._frames = []
                self.is_recording = True
                self._start_time = time.time()

                def audio_callback(indata, frames, time_info, status):
                    if self.is_recording:
                        self._frames.append(indata.copy())

                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype='int16',
                    callback=audio_callback
                )
                self._stream.start()
                return True, "Bắt đầu thu âm thành công."
            except Exception as e:
                self.is_recording = False
                return False, f"Không thể kích hoạt Microphone: {e}"

    def stop_recording(self) -> Optional[str]:
        """
        Dừng ghi âm và lưu dữ liệu ra file WAV tạm thời.
        Trả về đường dẫn tới file .wav hoặc None nếu không ghi nhận được âm thanh.
        """
        with self._lock:
            if not self.is_recording:
                return None
            self.is_recording = False

            try:
                if self._stream is not None:
                    self._stream.stop()
                    self._stream.close()
                    self._stream = None
            except Exception as e:
                print(f"[AudioRecorder Error] Khi đóng stream: {e}")

            if not self._frames:
                return None

            try:
                import numpy as np
                audio_data = np.concatenate(self._frames, axis=0)

                # Bỏ qua nếu thời lượng thu âm quá ngắn (< 0.3 giây)
                if len(audio_data) < int(self.sample_rate * 0.3):
                    return None

                temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_wav_path = temp_wav.name
                temp_wav.close()

                with wave.open(temp_wav_path, "wb") as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)  # 16-bit PCM = 2 bytes
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data.tobytes())

                return temp_wav_path
            except Exception as e:
                print(f"[AudioRecorder Error] Lưu file wav: {e}")
                return None

    def get_elapsed_seconds(self) -> int:
        """Lấy số giây đã ghi âm."""
        if self.is_recording and self._start_time > 0:
            return int(time.time() - self._start_time)
        return 0


# Bộ ghi âm toàn cục tái sử dụng
GLOBAL_AUDIO_RECORDER = SystemAudioRecorder()


def transcribe_audio_file(audio_path: str) -> Optional[str]:
    """
    Chuyển đổi tệp âm thanh thành văn bản tiếng Việt:
    1. Ưu tiên: OpenAI Whisper API nếu có cấu hình OPENAI_API_KEY.
    2. Fallback: Google Speech-to-Text API tiếng Việt (miễn phí, không cần key).
    3. Tự động chuẩn hóa phát âm sang thuật ngữ KHTN 7.
    """
    if not audio_path or not os.path.exists(audio_path):
        return None

    # 1. Thử OpenAI Whisper API nếu có cấu hình
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=base_url if base_url else None, api_key=api_key)
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="vi"
                )
            if transcript and hasattr(transcript, "text") and transcript.text.strip():
                return normalize_spoken_khtn(transcript.text.strip())
        except Exception as e:
            print(f"[Whisper Info] Chuyển tiếp sang Google STT: {e}")

    # 2. Fallback sang Google Speech-to-Text tiếng Việt (SpeechRecognition)
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="vi-VN")
            if text and text.strip():
                return normalize_spoken_khtn(text.strip())
    except sr.UnknownValueError:
        print("[STT Info] Không nhận diện được âm thanh (giọng quá nhỏ hoặc im lặng).")
    except Exception as e:
        print(f"[STT Error] Lỗi nhận diện giọng nói: {e}")

    return None


def process_voice_input(spoken_text: str) -> ProblemInput:
    """
    Tiếp nhận văn bản giọng nói và đóng gói vào đối tượng ProblemInput.
    """
    clean_text = spoken_text.strip()
    if not clean_text:
        return ProblemInput(
            input_type=InputType.VOICE,
            text_content="",
            validation_error="Chưa ghi nhận được âm thanh giọng nói! Em hãy bấm nút micro và nói to, rõ ràng nhé."
        )

    normalized = normalize_spoken_khtn(clean_text)

    if len(normalized) < 5:
        return ProblemInput(
            input_type=InputType.VOICE,
            text_content=normalized,
            validation_error="Nội dung câu nói quá ngắn. Em hãy đọc đầy đủ câu hỏi hoặc dữ kiện bài toán nhé!"
        )

    warnings = check_pii_and_safety(normalized)

    return ProblemInput(
        input_type=InputType.VOICE,
        text_content=normalized,
        is_confirmed=False,
        safety_warnings=warnings
    )


def get_demo_voice_presets() -> List[Dict[str, str]]:
    """Trả về danh sách các câu nói mẫu phục vụ demo."""
    return DEMO_VOICE_PRESETS
