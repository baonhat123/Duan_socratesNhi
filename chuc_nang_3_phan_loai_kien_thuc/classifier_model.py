"""
Module: classifier_model.py
Chức năng 3 (FR-03): Mô hình Phân loại kiến thức bài toán & Bản đồ khái niệm
Đặc tả: Socrates Nhí v3.0 (Mục 6 - FR-03 & Mục 9 - Hợp đồng dữ liệu JSON Schema)

Quy định:
- AI trả chủ đề (topic), cấp độ ước lượng, dữ kiện cần dùng, đại lượng cần tìm.
- TỐI ĐA 3 khái niệm cốt lõi (core_concepts) được CHỌN từ bản đồ đội soạn, không tự bịa.
- Đúng schema JSON mục 9.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


class KnowledgeStrand(str, Enum):
    MECHANICS = "Cơ học / Đại lượng vật lý"
    CHEMISTRY = "Biến đổi chất / Phản ứng hóa học"
    BIOLOGY = "Cơ thể sống / Môi trường"


class DifficultyLevel(str, Enum):
    BASIC = "Cơ bản"
    UNDERSTANDING = "Thông hiểu"
    APPLICATION = "Vận dụng"


@dataclass
class CoreConcept:
    """Một khái niệm chuẩn trong Bản đồ khái niệm."""
    name: str                           # Tên khái niệm (ví dụ: "Tốc độ v = s/t")
    formula: Optional[str] = None       # Công thức chuẩn (nếu có)
    description: str = ""               # Mô tả ý nghĩa sư phạm
    common_pitfalls: List[str] = field(default_factory=list) # Lỗi sai thường gặp


@dataclass
class ClassificationResult:
    """
    Kết quả phân loại kiến thức theo đúng chuẩn JSON Schema mục 9.
    """
    topic: str                                  # Chủ đề bài toán (ví dụ: "Vật lý – Chuyển động và Tốc độ")
    strand: KnowledgeStrand                     # 1 trong 3 mạch kiến thức KHTN 7
    difficulty: DifficultyLevel                 # Cấp độ ước lượng
    given_facts: List[str] = field(default_factory=list)      # Các dữ kiện đã cho (s = 12 km, t = 30 phút)
    target_variable: str = ""                   # Đại lượng cần tìm (v = ? km/h, m/s)
    core_concepts: List[str] = field(default_factory=list)    # Tối đa 3 khái niệm lấy từ bản đồ đội soạn
    common_mistakes: List[str] = field(default_factory=list)  # Lỗi thường gặp cần tránh
    analysis_source: str = "concept_map_bank"   # "openai_json" hoặc "concept_map_bank"
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_valid_schema(self) -> bool:
        """Kiểm tra ràng buộc: Tối đa 3 khái niệm cốt lõi."""
        return len(self.core_concepts) <= 3 and bool(self.topic.strip())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "strand": self.strand.value,
            "difficulty": self.difficulty.value,
            "given_facts": self.given_facts,
            "target_variable": self.target_variable,
            "core_concepts": self.core_concepts[:3],
            "common_mistakes": self.common_mistakes,
            "analysis_source": self.analysis_source,
            "created_at": self.created_at.isoformat()
        }
