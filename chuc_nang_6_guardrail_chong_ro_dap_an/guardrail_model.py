"""
Module: guardrail_model.py
Chức năng 6: Mô hình dữ liệu Hậu kiểm An toàn 3 Tầng (FR-07)
Đặc tả dự án: Socrates Nhí v3.0 (Mục 10)

Quy định chuẩn:
- Tầng 1: Ép schema tách bạch & Đối chiếu số liệu đáp án bị khóa.
- Tầng 2: Answer-leak classifier (LLM phán quyết thứ hai).
- Tầng 3: Pattern filter (Lớp chặn nhanh regex).
- Fallback an toàn: Xoay vòng 3 mẫu chuẩn mục 10.3 khi bị chặn.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


class TierVerdict(str, Enum):
    PASS = "pass"           # An toàn (Vượt qua)
    FLAGGED = "flagged"     # Nghi ngờ (Cần chuyển tầng 2 phân tích sâu)
    BLOCKED = "blocked"     # Đã chặn (Rò rỉ đáp số hoặc giải hộ)


@dataclass
class TierCheckResult:
    """Kết quả thẩm định của một tầng kiểm soát."""
    tier_number: int            # 1, 2, hoặc 3
    tier_name: str              # Tên tầng kiểm soát
    verdict: TierVerdict        # PASS, FLAGGED, hoặc BLOCKED
    reason: str                 # Giải thích lý do sư phạm / kỹ thuật
    matched_clues: List[str] = field(default_factory=list) # Dấu hiệu phát hiện

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier_number": self.tier_number,
            "tier_name": self.tier_name,
            "verdict": self.verdict.value,
            "reason": self.reason,
            "matched_clues": self.matched_clues
        }


@dataclass
class GuardrailAudit:
    """Hồ sơ kiểm định an toàn toàn diện của một phát ngôn AI."""
    original_text: str
    sanitized_text: str
    tier_results: List[TierCheckResult] = field(default_factory=list)
    is_safe: bool = True
    fallback_used: bool = False
    safety_flags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "sanitized_text": self.sanitized_text,
            "is_safe": self.is_safe,
            "fallback_used": self.fallback_used,
            "safety_flags": self.safety_flags,
            "tier_results": [t.to_dict() for t in self.tier_results],
            "timestamp": self.timestamp.isoformat()
        }


# Danh mục các đáp số bị khóa trong Ngân hàng Học liệu KHTN 7 (Mục 10 & 13)
LOCKED_SAMPLE_ANSWERS = [
    "24 km/h", "6.67 m/s", "6,67 m/s",
    "450 N", "450n",
    "16 g", "16g", "22 g", "22g",
    "6CO2", "6H2O", "C6H12O6",
    "15 km", "45 phút", "0.5 h"
]
