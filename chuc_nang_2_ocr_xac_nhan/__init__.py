"""
Package: chuc_nang_2_ocr_xac_nhan
Chức năng 2 (FR-02): Trích xuất OCR & Xác nhận/Biên tập đề bài
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Chức năng phụ trách:
- Đánh giá độ nét của ảnh (phát hiện và từ chối ảnh quá mờ/nhòe theo cam kết không đoán mò)
- Trích xuất văn bản đề bài (OpenAI-compatible Vision hoặc Bộ nhận dạng nội bộ)
- Chuẩn hóa công thức KHTN theo quy ước Unicode mục 12 (v², H₂O, CO₂, km/h, N)
- Giao diện đối chiếu ảnh gốc và ô biên tập công thức có thanh ký hiệu nhanh
- Đóng gói ConfirmedProblem sẵn sàng chuyển giao cho Chức năng 3 & 4
"""

from .ocr_model import OcrResult, ConfirmedProblem
from .ocr_engine import (
    process_image_ocr,
    calculate_image_sharpness,
    calculate_sharpness_percentage,
    is_image_too_blurry
)
from .formula_normalizer import (
    normalize_khtn_text,
    normalize_chemical_formulas,
    normalize_physics_powers,
    normalize_units_spacing,
    extract_formulas_and_units
)
from .ocr_view import OcrConfirmationView
from .sample_images import SAMPLE_PATHS

__all__ = [
    "OcrResult",
    "ConfirmedProblem",
    "process_image_ocr",
    "calculate_image_sharpness",
    "calculate_sharpness_percentage",
    "is_image_too_blurry",
    "normalize_khtn_text",
    "normalize_chemical_formulas",
    "normalize_physics_powers",
    "normalize_units_spacing",
    "extract_formulas_and_units",
    "OcrConfirmationView",
    "SAMPLE_PATHS"
]
