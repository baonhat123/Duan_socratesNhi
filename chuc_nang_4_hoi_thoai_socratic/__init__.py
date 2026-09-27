"""
Package: chuc_nang_4_hoi_thoai_socratic
Chức năng 4 (FR-04 & FR-05): Hội thoại gợi mở tư duy theo State Machine Socratic 5 pha
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Chức năng phụ trách:
- Điều phối chu trình Socratic 5 pha (clarify, recall, reason, check, generalize)
- Phân tích 6 trạng thái câu trả lời của học sinh (correct, partial, unknown, misconception, answer_plea, off_topic)
- Ma trận chuyển pha nghiêm ngặt (Mục 5.2)
- Ngưỡng tối đa 7 lượt hội thoại, khép phiên kẹt ở pha 3 sau 5 lượt
- Hậu kiểm Guardrail chống rò rỉ đáp án
- Giao diện Chat Flet hiện đại kèm thẻ Gợi ý vi mô (micro_hint <= 140 ký tự)
"""

from .socratic_model import (
    SocraticPhase,
    StudentState,
    ChatMessage,
    TurnResponse,
    PHASE_NAMES,
    PHASE_DESCRIPTIONS
)
from .state_machine import SocraticStateMachine
from .socratic_engine import SocraticEngine
from .socratic_view import SocraticChatView

__all__ = [
    "SocraticPhase",
    "StudentState",
    "ChatMessage",
    "TurnResponse",
    "PHASE_NAMES",
    "PHASE_DESCRIPTIONS",
    "SocraticStateMachine",
    "SocraticEngine",
    "SocraticChatView"
]
