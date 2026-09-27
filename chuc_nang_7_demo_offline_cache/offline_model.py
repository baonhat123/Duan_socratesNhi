"""
Module: offline_model.py
Chức năng 7: Mô hình dữ liệu Chế độ Demo Offline & Cache Học liệu KHTN 7 (FR-10)
Đặc tả dự án: Socrates Nhí v3.0 (Mục 18 - Vận hành lúc thi)

Quy định chuẩn:
- 12 bài mẫu đại diện cho 3 mạch kiến thức (Vật lý, Hóa học, Sinh học).
- Mỗi bài mẫu chứa lời thoại cache chuẩn 5 pha Socratic (Clarify -> Recall -> Reason -> Check -> Generalize).
- Đã được duyệt sư phạm và kiểm tra qua Guardrail 3 Tầng không rò rỉ đáp án.
- Tự động chuyển đổi khi API timeout (> 20s), mất kết nối mạng hoặc khi người dùng bật công tắc Offline.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


class NetworkMode(str, Enum):
    ONLINE = "online"                   # Kết nối AI trực tuyến (OpenAI-compatible)
    OFFLINE_DEMO = "offline_demo"       # Chế độ Demo Offline (Sử dụng cache 12 bài mẫu)
    TIMEOUT_FALLBACK = "timeout_fallback" # Tự động chuyển sang cache do mạng yếu (> 20s)


class KnowledgeStrand(str, Enum):
    PHYSICS = "Vật lý THCS (Cơ học & Năng lượng)"
    CHEMISTRY = "Hóa học THCS (Chất & Biến đổi hóa học)"
    BIOLOGY = "Sinh học THCS (Cơ thể sống & Trao đổi chất)"


@dataclass
class SocraticPhaseDialogue:
    """Nội dung lời thoại cache cho một pha Socratic cụ thể."""
    phase_name: str                      # clarify, recall, reason, check, generalize
    feedback: str                        # Câu phản hồi động viên học sinh
    question: str                        # Câu hỏi gợi mở duy nhất của lượt
    micro_hint: str                      # Gợi ý vi mô (tối đa 140 ký tự)
    quick_replies: List[str] = field(default_factory=list) # Gợi ý câu trả lời nhanh cho học sinh


@dataclass
class OfflineSampleProblem:
    """Hồ sơ một bài toán mẫu được lưu trữ trong ngân hàng Cache Offline."""
    problem_id: str                      # Ví dụ: VL01, HH01, SH01
    title: str                           # Tiêu đề ngắn gọn
    strand: KnowledgeStrand              # Mạch kiến thức KHTN 7
    problem_text: str                    # Nội dung đề bài KHTN đầy đủ
    given_facts: List[str]               # Dữ kiện cho trước (ví dụ: s = 12 km, t = 30 phút)
    core_concepts: List[str]             # Tối đa 3 khái niệm cốt lõi
    target_variable: str                 # Đại lượng cần tìm
    common_pitfall: str                  # Lỗi tư duy học sinh thường mắc
    cached_phases: Dict[str, SocraticPhaseDialogue] = field(default_factory=dict) # Đủ 5 pha

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "title": self.title,
            "strand": self.strand.value,
            "problem_text": self.problem_text,
            "given_facts": self.given_facts,
            "core_concepts": self.core_concepts,
            "target_variable": self.target_variable,
            "common_pitfall": self.common_pitfall,
            "cached_phases_count": len(self.cached_phases)
        }
