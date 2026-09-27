"""
Module: socratic_model.py
Chức năng 4 (FR-04 & FR-05): Mô hình dữ liệu Hội thoại Socratic theo State Machine 5 pha
Đặc tả: Socrates Nhí v3.0

Định nghĩa:
- 5 Pha Socratic: clarify, recall, reason, check, generalize.
- 6 Kiểu câu trả lời của học sinh: correct, partial, unknown, misconception, answer_plea, off_topic.
- Cấu trúc tin nhắn hội thoại và đối tượng phản hồi mỗi lượt (TurnResponse).
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


class SocraticPhase(str, Enum):
    CLARIFY = "clarify"        # Pha 1: Làm rõ dữ kiện đề bài
    RECALL = "recall"          # Pha 2: Gợi nhớ khái niệm / công thức liên quan
    REASON = "reason"          # Pha 3: Lập luận nối dữ kiện với khái niệm
    CHECK = "check"            # Pha 4: Tự kiểm tra đơn vị, điều kiện, tính hợp lý
    GENERALIZE = "generalize"  # Pha 5: Khái quát quy tắc & lỗi cần tránh (khép phiên)


class StudentState(str, Enum):
    CORRECT = "correct"              # Trả lời đúng và đủ
    PARTIAL = "partial"              # Đúng một phần, còn thiếu ý
    UNKNOWN = "unknown"              # Không biết, bối rối, "em không biết"
    MISCONCEPTION = "misconception"  # Nhầm lẫn khái niệm bản chất
    ANSWER_PLEA = "answer_plea"      # Nài ép xin đáp số ("cho kết quả đi")
    OFF_TOPIC = "off_topic"          # Lạc đề ngoài bài học


# Tên tiếng Việt thân thiện của các pha Socratic
PHASE_NAMES: Dict[SocraticPhase, str] = {
    SocraticPhase.CLARIFY: "Pha 1: Làm rõ dữ kiện",
    SocraticPhase.RECALL: "Pha 2: Gợi nhớ kiến thức",
    SocraticPhase.REASON: "Pha 3: Lập luận logic",
    SocraticPhase.CHECK: "Pha 4: Tự kiểm tra kết quả",
    SocraticPhase.GENERALIZE: "Pha 5: Khái quát & Tổng kết"
}

PHASE_DESCRIPTIONS: Dict[SocraticPhase, str] = {
    SocraticPhase.CLARIFY: "Xác định rõ đề bài cho những dữ kiện và đại lượng nào.",
    SocraticPhase.RECALL: "Kích hoạt định luật, công thức hoặc hiện tượng đã học.",
    SocraticPhase.REASON: "Kết nối dữ kiện với công thức để tìm hướng giải quyết.",
    SocraticPhase.CHECK: "Đối chiếu đơn vị đo lường và tính hợp lý của kết quả.",
    SocraticPhase.GENERALIZE: "Tự đúc kết quy tắc quan trọng và lỗi sai cần tránh."
}


@dataclass
class ChatMessage:
    """Tin nhắn đơn lẻ trong luồng hội thoại."""
    sender: str                    # "socrates" hoặc "student"
    content: str                   # Nội dung chính
    phase: SocraticPhase           # Thuộc pha Socratic nào
    micro_hint: Optional[str] = None # Gợi ý vi mô (nếu có)
    feedback: Optional[str] = None   # Nhận xét tích cực cho câu trả lời trước
    student_state: Optional[StudentState] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TurnResponse:
    """
    Cấu trúc phản hồi bắt buộc cho mỗi lượt hội thoại của Socrates Nhí.
    Tuân thủ quy tắc sư phạm:
    - Đúng MỘT câu hỏi chính (next_question)
    - Tối đa 1 gợi ý vi mô (micro_hint <= 140 ký tự)
    - 1 câu phản hồi tích cực/cụ thể (feedback)
    - Không bao giờ chứa đáp số cuối cùng
    """
    phase: SocraticPhase
    next_phase: SocraticPhase
    student_state: StudentState
    feedback: str
    next_question: str
    micro_hint: Optional[str] = None
    turn_count: int = 1
    consecutive_unknown_count: int = 0
    is_session_closed: bool = False
    safety_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "next_phase": self.next_phase.value,
            "student_state": self.student_state.value,
            "feedback": self.feedback,
            "next_question": self.next_question,
            "micro_hint": self.micro_hint,
            "turn_count": self.turn_count,
            "consecutive_unknown_count": self.consecutive_unknown_count,
            "is_session_closed": self.is_session_closed,
            "safety_flags": self.safety_flags
        }
