"""
Module: mindmap_model.py
Chức năng 5: Mô hình dữ liệu Sơ đồ Tư duy & Tổng kết Buổi học
Đặc tả dự án: Socrates Nhí v3.0 (FR-06, FR-08, FR-09)

Quy định bắt buộc:
1. FR-06: Sơ đồ tư duy hiển thị có từ 3 đến 6 nút.
2. FR-06: Tuyệt đối KHÔNG chứa đáp số cuối cùng, không vẽ chuỗi tính toán thay học sinh.
3. FR-08: Log tối thiểu ẩn danh, không lưu PII.
4. FR-09: Khung tự đúc kết 3 dòng và khảo sát 1-5 sao.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import uuid


class MindmapNodeType(str, Enum):
    TOPIC = "topic"         # Chủ đề / Phân môn
    FACT = "fact"           # Dữ kiện đã cho từ đề bài
    CONCEPT = "concept"     # Khái niệm & Công thức nền tảng
    CHECK = "check"         # Phương pháp tự kiểm tra / Lỗi cần tránh


@dataclass
class MindmapNode:
    """Nút biểu diễn trong Sơ đồ tư duy học tập."""
    id: str
    title: str
    node_type: MindmapNodeType
    subtitle: str = ""
    formula: Optional[str] = None
    icon_name: str = "lightbulb"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "node_type": self.node_type.value,
            "subtitle": self.subtitle,
            "formula": self.formula,
            "icon_name": self.icon_name
        }


@dataclass
class MindmapGraph:
    """Sơ đồ tư duy hiển thị (Mindmap Graph) tuân thủ nghiêm ngặt FR-06."""
    nodes: List[MindmapNode] = field(default_factory=list)
    connections: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def is_valid_count(self) -> bool:
        """Ràng buộc FR-06: Hiển thị từ 3 đến 6 nút."""
        return 3 <= len(self.nodes) <= 6

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "connections": self.connections,
            "node_count": len(self.nodes),
            "is_valid": self.is_valid_count
        }


@dataclass
class StudentSummary:
    """Khung Học sinh Tự đúc kết 3 dòng theo FR-09."""
    rule_learned: str = ""        # Quy tắc / Công thức em đã vận dụng
    pitfall_avoided: str = ""     # Lỗi sai / Bẫy em cần tránh
    next_step: str = ""           # Bước giải tiếp theo của em

    @property
    def is_filled(self) -> bool:
        return bool(self.rule_learned.strip() and self.next_step.strip())

    def to_dict(self) -> Dict[str, str]:
        return {
            "rule_learned": self.rule_learned,
            "pitfall_avoided": self.pitfall_avoided,
            "next_step": self.next_step
        }


@dataclass
class SessionSummary:
    """Tổng kết phiên học tập và nhật ký ẩn danh theo FR-08 & FR-09."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    problem_text: str = ""
    topic: str = "Khoa học Tự nhiên 7"
    strand: str = "Vật lý THCS"
    total_turns: int = 1
    final_phase: str = "generalize"
    mindmap: Optional[MindmapGraph] = None
    student_summary: Optional[StudentSummary] = None
    rating_stars: int = 5                  # Đánh giá 1 đến 5 sao
    feedback_comment: str = ""
    is_temp_cleared: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_anonymous_log(self) -> Dict[str, Any]:
        """Đảm bảo không chứa PII (tên, lớp, trường, SĐT)."""
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "strand": self.strand,
            "total_turns": self.total_turns,
            "final_phase": self.final_phase,
            "rating_stars": self.rating_stars,
            "student_summary": self.student_summary.to_dict() if self.student_summary else {},
            "created_at": self.created_at.isoformat(),
            "pii_protected": True
        }
