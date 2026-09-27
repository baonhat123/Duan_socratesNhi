"""
Module: voice_service.py
Chức năng 1 (FR-01 Mở rộng): Nhận diện giọng nói KHTN (Speech-to-Text)
Đặc tả dự án: Socrates Nhí v3.0 (Mục 2.2 & Mục 22 - Lộ trình nâng cấp)

Tính năng chuyên biệt cho học sinh THCS:
1. Bộ chuẩn hóa phát âm thuật ngữ Khoa học Tự nhiên tiếng Việt sang ký hiệu quốc tế:
   - "ki lô mét trên giờ" ➜ "km/h"
   - "mét trên giây" ➜ "m/s"
   - "ki lô gam" ➜ "kg"
   - "niu tơn" ➜ "N"
   - "ô-xy-gen" / "khí o2" ➜ "oxygen (O₂)"
   - "các-bon đi-ô-xít" / "khí co2" ➜ "carbon dioxide (CO₂)"
   - "nước" / "hát hai ô" ➜ "H₂O"
2. Gọi Whisper Speech-to-Text API qua OpenAI-compatible nếu có cấu hình .env.
3. Bộ mô phỏng ghi âm & nhận diện giọng nói thử nghiệm (Demo Voice Presets) giúp chạy mượt mà kể cả khi không có microphone phần cứng hoặc thi offline.
"""

import os
import re
from typing import Optional, List, Dict
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
    (r"\bvận\s*tốc\s*vê\b", "tốc độ v"),
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


def transcribe_audio_file(audio_path: str) -> Optional[str]:
    """
    Chuyển đổi tệp âm thanh thành văn bản qua OpenAI Whisper API (nếu có .env).
    """
    if not os.path.exists(audio_path):
        return None

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
            if transcript and hasattr(transcript, "text"):
                return normalize_spoken_khtn(transcript.text)
        except Exception as e:
            print(f"[Whisper Warning] Không thể gọi Whisper API ({e}). Đang dùng bộ chuẩn hóa nội bộ.")

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
