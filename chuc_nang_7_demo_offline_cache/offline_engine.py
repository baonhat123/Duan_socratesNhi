"""
Module: offline_engine.py
Chức năng 7: Bộ Điều Phối Chế Độ Demo Offline & Fallback Timeout (FR-10)
Đặc tả dự án: Socrates Nhí v3.0 (Mục 18 - Vận hành lúc thi)

Nhiệm vụ:
1. Quản lý trạng thái mạng: ONLINE, OFFLINE_DEMO, TIMEOUT_FALLBACK.
2. Tự động chuyển đổi sang cache khi:
   - Người dùng hoặc giám khảo bật chế độ Offline.
   - Gọi API gặp timeout (> 20 giây theo mục 18.1).
   - Không có kết nối mạng Internet hoặc lỗi API quota.
3. Cung cấp câu hỏi, phản hồi và gợi ý vi mô từ 12 bài mẫu được duyệt sư phạm.
4. Đảm bảo hiển thị huy hiệu trung thực: "Đang ở chế độ demo offline".
"""

import time
from typing import Optional, Tuple, Dict, Any, List

from .offline_model import (
    NetworkMode,
    OfflineSampleProblem,
    SocraticPhaseDialogue,
    KnowledgeStrand
)
from .offline_bank import (
    OFFLINE_SAMPLE_PROBLEMS,
    get_offline_problem_by_id,
    get_all_offline_problems
)

TIMEOUT_THRESHOLD_SECONDS = 20.0  # Ngưỡng timeout 20s theo quy định mục 18.1


import os
from pathlib import Path

# Đảm bảo nạp .env
try:
    from dotenv import load_dotenv
    _env_p = Path(__file__).resolve().parent.parent / ".env"
    if _env_p.exists():
        load_dotenv(_env_p)
    else:
        load_dotenv()
except Exception:
    pass


class OfflineDemoEngine:
    """
    Bộ máy điều phối chế độ Demo Offline và Cache Học liệu.
    """
    def __init__(self, force_offline: Optional[bool] = None):
        import sys
        is_testing = "unittest" in sys.modules or any("test" in arg.lower() for arg in sys.argv)
        has_key = bool(os.getenv("OPENAI_API_KEY", "").strip())

        if force_offline is True:
            self.mode: NetworkMode = NetworkMode.OFFLINE_DEMO
        elif force_offline is False:
            self.mode: NetworkMode = NetworkMode.ONLINE
        elif is_testing:
            # Luôn giữ offline trong unit test để kiểm thử chuẩn mực 100% không phụ thuộc mạng
            self.mode: NetworkMode = NetworkMode.OFFLINE_DEMO
        else:
            self.mode: NetworkMode = NetworkMode.ONLINE if has_key else NetworkMode.OFFLINE_DEMO

        self.active_problem_id: str = "VL01"
        self.current_phase_index: int = 0
        self.phase_keys = ["clarify", "recall", "reason", "check", "generalize"]

    def set_mode(self, mode: NetworkMode):
        """Thay đổi chế độ kết nối mạng."""
        self.mode = mode

    def set_force_offline(self, enabled: bool):
        """Bật/tắt cưỡng chế chế độ offline."""
        self.mode = NetworkMode.OFFLINE_DEMO if enabled else NetworkMode.ONLINE

    def is_offline(self) -> bool:
        """Kiểm tra xem hệ thống có đang ở chế độ offline hay không."""
        return self.mode in [NetworkMode.OFFLINE_DEMO, NetworkMode.TIMEOUT_FALLBACK]

    def select_problem(self, problem_id: str) -> Optional[OfflineSampleProblem]:
        """Chọn bài toán mẫu đang demo."""
        prob = get_offline_problem_by_id(problem_id)
        if prob:
            self.active_problem_id = problem_id
            self.current_phase_index = 0
            return prob
        return None

    def match_problem_from_text(self, text: str, strict: bool = False) -> Optional[OfflineSampleProblem]:
        """
        Tìm kiếm bài toán mẫu gần nhất dựa trên từ khóa trong đề bài.
        Nếu strict=False (mặc định), trả về bài toán mặc định (VL01) nếu không khớp.
        Nếu strict=True, trả về None nếu không khớp với bất kỳ bài mẫu nào.
        """
        text_lower = text.lower()

        # So khớp theo từ khóa đặc trưng của 12 bài mẫu
        if "12 km" in text_lower or "30 phút" in text_lower or "xe đạp" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["VL01"]
        elif "45 km/h" in text_lower or "đoàn tàu" in text_lower or "20 phút" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["VL02"]
        elif "bao gạo" in text_lower or "45 kg" in text_lower or "trọng lượng" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["VL03"]
        elif "khối gỗ" in text_lower or "15 n" in text_lower or "ma sát" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["VL04"]

        elif "carbon" in text_lower or "đốt than" in text_lower or "12 g" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["HH01"]
        elif "đá vôi" in text_lower or "caco3" in text_lower or "100 g" in text_lower or "nung" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["HH02"]
        elif "15 g muối" in text_lower or "nồng độ" in text_lower or "c%" in text_lower or "nước muối" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["HH03"]
        elif "cồn" in text_lower or "hiện tượng vật lý" in text_lower or "hiện tượng hóa học" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["HH04"]

        elif "quang hợp" in text_lower or "lá cây" in text_lower or "diệp lục" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["SH01"]
        elif "hạt" in text_lower or "nảy mầm" in text_lower or "hô hấp tế bào" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["SH02"]
        elif "khí khổng" in text_lower or "thoát hơi nước" in text_lower or "nắng nóng" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["SH03"]
        elif "hướng sáng" in text_lower or "cửa sổ" in text_lower or "ngọn cây" in text_lower:
            return OFFLINE_SAMPLE_PROBLEMS["SH04"]

        if strict:
            return None

        # Mặc định trả về bài VL01 nếu không ở chế độ strict
        return OFFLINE_SAMPLE_PROBLEMS.get(self.active_problem_id, OFFLINE_SAMPLE_PROBLEMS["VL01"])

    def get_phase_dialogue(
        self,
        phase_name: str,
        problem_id: Optional[str] = None
    ) -> SocraticPhaseDialogue:
        """
        Lấy gói lời thoại cache (feedback + question + micro_hint) cho một pha Socratic cụ thể.
        """
        pid = problem_id or self.active_problem_id
        prob = get_offline_problem_by_id(pid) or OFFLINE_SAMPLE_PROBLEMS["VL01"]

        phase_key = phase_name.lower()
        if phase_key not in prob.cached_phases:
            phase_key = "clarify"

        return prob.cached_phases[phase_key]

    def simulate_api_call_with_timeout(
        self,
        call_duration_seconds: float
    ) -> Tuple[bool, str]:
        """
        Mô phỏng cơ chế phát hiện timeout > 20s và kích hoạt Fallback Cache (Mục 18.1).
        """
        if call_duration_seconds > TIMEOUT_THRESHOLD_SECONDS:
            self.mode = NetworkMode.TIMEOUT_FALLBACK
            return (
                True,
                f"Đã kích hoạt Fallback: Thời gian phản hồi ({call_duration_seconds:.1f}s) "
                f"vượt ngưỡng an toàn {TIMEOUT_THRESHOLD_SECONDS}s. Tự động chuyển sang cache offline!"
            )
        return False, "Kết nối bình thường."


# Instance toàn cục để chia sẻ giữa các module
GLOBAL_OFFLINE_ENGINE = OfflineDemoEngine()
