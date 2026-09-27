"""
Package: chuc_nang_3_phan_loai_kien_thuc
Chức năng 3 (FR-03): Phân loại kiến thức bài toán & Bản đồ khái niệm
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Chức năng phụ trách:
- Phân loại bài toán vào 3 mạch kiến thức (Cơ học, Hóa học, Sinh học)
- Ước lượng cấp độ nhận thức (Cơ bản, Thông hiểu, Vận dụng)
- Bóc tách dữ kiện đã cho (facts) và đại lượng cần tìm
- Chọn TỐI ĐA 3 khái niệm cốt lõi từ Bản đồ do đội biên soạn (LLM chỉ chọn, không tự bịa)
- Giao diện trực quan hóa Bản đồ khái niệm trước khi bước vào chu trình Socratic
"""

from .classifier_model import (
    KnowledgeStrand,
    DifficultyLevel,
    CoreConcept,
    ClassificationResult
)
from .concept_bank import CONCEPT_MAP, get_all_curated_concepts, get_concept_by_key
from .classifier_engine import KnowledgeClassifier
from .classifier_view import KnowledgeClassifierView

__all__ = [
    "KnowledgeStrand",
    "DifficultyLevel",
    "CoreConcept",
    "ClassificationResult",
    "CONCEPT_MAP",
    "get_all_curated_concepts",
    "get_concept_by_key",
    "KnowledgeClassifier",
    "KnowledgeClassifierView"
]
