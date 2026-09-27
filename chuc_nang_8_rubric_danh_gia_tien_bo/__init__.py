"""
Chức năng 8: Rubric Đánh giá Tiến bộ Lập luận (0-6 điểm) & Bảng 5 Chỉ số Đo lường Sư phạm
Đặc tả dự án: Socrates Nhí v3.0 (Mục 3 & Mục 16.3)
Cuộc thi Sáng tạo trẻ Quốc gia trong lĩnh vực Trí tuệ Nhân tạo 2026 - Bảng A
"""

from .rubric_model import (
    CriterionScore,
    RubricAssessment,
    ProjectMetrics5,
    MetricStatus
)
from .rubric_engine import RubricEngine, GLOBAL_RUBRIC_ENGINE
from .rubric_view import RubricDashboardView

__all__ = [
    "CriterionScore",
    "RubricAssessment",
    "ProjectMetrics5",
    "MetricStatus",
    "RubricEngine",
    "GLOBAL_RUBRIC_ENGINE",
    "RubricDashboardView"
]
