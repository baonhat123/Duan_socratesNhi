"""
Package: chuc_nang_6_guardrail_chong_ro_dap_an
Chức năng 6 (FR-07): Hệ thống Chống Rò Đáp Án 3 Tầng & Hậu Kiểm An Toàn
Đặc tả: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)
"""

from .guardrail_model import (
    TierVerdict,
    TierCheckResult,
    GuardrailAudit,
    LOCKED_SAMPLE_ANSWERS
)
from .guardrail_engine import (
    ThreeTierGuardrail,
    audit_and_sanitize_response,
    FALLBACK_TEMPLATES
)
from .guardrail_view import GuardrailPlaygroundView

__all__ = [
    "TierVerdict",
    "TierCheckResult",
    "GuardrailAudit",
    "LOCKED_SAMPLE_ANSWERS",
    "ThreeTierGuardrail",
    "audit_and_sanitize_response",
    "FALLBACK_TEMPLATES",
    "GuardrailPlaygroundView"
]
