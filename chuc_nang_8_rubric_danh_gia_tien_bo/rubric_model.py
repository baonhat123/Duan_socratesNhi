"""
Module: rubric_model.py
Chức năng 8: Rubric Đánh giá Tiến bộ Lập luận (0-6 điểm) & 5 Chỉ số Đo lường Sư phạm
Đặc tả dự án: Socrates Nhí v3.0 (Mục 3 & Mục 16.3)

Định nghĩa cấu trúc dữ liệu cho:
- Rubric 3 tiêu chí đánh giá năng lực lập luận (0-2 điểm mỗi tiêu chí, tổng 0-6 điểm).
- Tiêu chuẩn ĐẠT TIẾN BỘ LẬP LUẬN (>= 4/6 điểm).
- Bảng 5 Chỉ số Đo lường Khoa học phục vụ Hội thi Sáng tạo trẻ Quốc gia AI 2026.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class MetricStatus(str, Enum):
    ACHIEVED = "achieved"          # Đạt mục tiêu (Màu xanh)
    IN_PROGRESS = "in_progress"    # Đang bám sát (Màu cam)
    NOT_ACHIEVED = "not_achieved"  # Chưa đạt (Màu đỏ)


@dataclass
class CriterionScore:
    """Điểm số và bằng chứng cho một tiêu chí trong Rubric sư phạm."""
    criterion_id: str             # "given_data", "core_concepts", "next_step"
    title: str                    # Tên tiêu chí
    score: int                    # 0, 1, hoặc 2
    max_score: int = 2
    level_name: str = ""          # "Chưa đạt", "Đạt một phần", "Thành thạo"
    evidence: str = ""            # Trích dẫn câu nói của học sinh làm bằng chứng
    rubric_rule: str = ""         # Diễn giải quy tắc chấm theo mục 16.3
    pedagogical_feedback: str = ""# Lời khen hoặc hướng dẫn cải thiện sư phạm


@dataclass
class RubricAssessment:
    """
    Bản đánh giá tiến bộ lập luận hoàn chỉnh của một học sinh sau phiên học (Mục 16.3).
    Tổng điểm: 0 - 6 điểm. Đạt chuẩn khi tổng điểm >= 4/6.
    """
    session_id: str
    problem_title: str
    strand: str                                 # "Vật lý", "Hóa học", "Sinh học"
    given_data_score: CriterionScore            # Tiêu chí 1: Nêu dữ kiện (0-2 điểm)
    core_concepts_score: CriterionScore         # Tiêu chí 2: Nêu khái niệm (0-2 điểm)
    next_step_score: CriterionScore             # Tiêu chí 3: Nêu bước tiếp theo (0-2 điểm)
    evaluator_mode: str = "ai_auto"             # "ai_auto" hoặc "teacher_manual"
    evaluator_name: str = "Gia sư AI Socrates Nhí"
    evaluator_notes: str = ""                   # Ghi chú của giáo viên / giám khảo
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total_score(self) -> int:
        """Tổng điểm lập luận 3 tiêu chí (0 - 6)."""
        return (
            self.given_data_score.score +
            self.core_concepts_score.score +
            self.next_step_score.score
        )

    @property
    def is_passed(self) -> bool:
        """Quy tắc Mục 16.3: Học sinh được công nhận 'Đạt tiến bộ' khi tổng điểm >= 4/6."""
        return self.total_score >= 4

    @property
    def progress_level(self) -> str:
        """Xếp loại sư phạm."""
        total = self.total_score
        if total >= 6:
            return "Xuất sắc (Lập luận chủ động 100%)"
        elif total >= 4:
            return "Đạt tiến bộ (Tự suy luận vững vàng)"
        elif total >= 2:
            return "Cần thêm gợi mở (Còn phụ thuộc gợi ý)"
        else:
            return "Mới bắt đầu (Cần đồng hành từng bước)"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "problem_title": self.problem_title,
            "strand": self.strand,
            "total_score": self.total_score,
            "max_total": 6,
            "is_passed": self.is_passed,
            "progress_level": self.progress_level,
            "evaluator_mode": self.evaluator_mode,
            "evaluator_name": self.evaluator_name,
            "evaluator_notes": self.evaluator_notes,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "criteria": [
                {
                    "id": self.given_data_score.criterion_id,
                    "title": self.given_data_score.title,
                    "score": self.given_data_score.score,
                    "max": self.given_data_score.max_score,
                    "evidence": self.given_data_score.evidence,
                    "feedback": self.given_data_score.pedagogical_feedback
                },
                {
                    "id": self.core_concepts_score.criterion_id,
                    "title": self.core_concepts_score.title,
                    "score": self.core_concepts_score.score,
                    "max": self.core_concepts_score.max_score,
                    "evidence": self.core_concepts_score.evidence,
                    "feedback": self.core_concepts_score.pedagogical_feedback
                },
                {
                    "id": self.next_step_score.criterion_id,
                    "title": self.next_step_score.title,
                    "score": self.next_step_score.score,
                    "max": self.next_step_score.max_score,
                    "evidence": self.next_step_score.evidence,
                    "feedback": self.next_step_score.pedagogical_feedback
                }
            ]
        }


@dataclass
class MetricItem:
    """Một chỉ số đo lường hiệu quả khoa học trong Mục 3 của đặc tả."""
    key: str
    name: str
    target_str: str              # Ví dụ: "≥ 80%"
    target_val: float            # 80.0
    current_val: float           # 85.0
    numerator: int               # 17 (Tử số)
    denominator: int             # 20 (Mẫu số)
    unit: str                    # "%", "★", "phiên"
    description: str
    status: MetricStatus = MetricStatus.ACHIEVED

    @property
    def is_achieved(self) -> bool:
        return self.current_val >= self.target_val


@dataclass
class ProjectMetrics5:
    """
    Bảng 5 Chỉ số Đo lường Thành công MVP chính thức (Mục 3 & Mục 16.2).
    Được xuất nguyên văn vào Hồ sơ Dự thi Bảng A và bảng thuyết trình.
    """
    ocr_accuracy: MetricItem             # 1. Tỷ lệ OCR dùng được (Mục tiêu >= 80%)
    socratic_integrity: MetricItem       # 2. Tỷ lệ giữ đúng chế độ gợi mở (Mục tiêu >= 90%)
    reasoning_progress: MetricItem       # 3. Tiến bộ lập luận >= 4/6 (Mục tiêu >= 70%)
    student_satisfaction: MetricItem     # 4. Hài lòng học sinh (Mục tiêu >= 4.0 / 5.0)
    demo_stability: MetricItem           # 5. Độ ổn định demo (Mục tiêu >= 9/10 = 90%)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def all_achieved(self) -> bool:
        return all(m.is_achieved for m in [
            self.ocr_accuracy,
            self.socratic_integrity,
            self.reasoning_progress,
            self.student_satisfaction,
            self.demo_stability
        ])
