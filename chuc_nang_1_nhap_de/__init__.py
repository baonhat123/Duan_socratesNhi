"""
Package: chuc_nang_1_nhap_de
Chức năng 1 (FR-01): Nhập đề bài
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Chức năng phụ trách:
- Nhập văn bản đề bài
- Tải ảnh JPG/PNG <= 5MB qua FilePicker
- Chọn đề bài mẫu KHTN 7
- Kiểm tra dung lượng, định dạng ảnh bằng Pillow
- Cảnh báo bảo mật PII
- Đảm bảo KHÔNG gửi sang AI trước khi học sinh nhấn "Xác nhận đề bài"
"""

from .input_model import ProblemInput, InputType
from .validator import (
    process_image_input,
    process_text_input,
    validate_file_size,
    validate_file_format,
    check_pii_and_safety,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_EXTENSIONS
)
from .sample_bank import get_all_samples, get_sample_by_id
from .ui_component import ProblemInputView

__all__ = [
    "ProblemInput",
    "InputType",
    "ProblemInputView",
    "process_image_input",
    "process_text_input",
    "validate_file_size",
    "validate_file_format",
    "check_pii_and_safety",
    "MAX_FILE_SIZE_BYTES",
    "ALLOWED_EXTENSIONS",
    "get_all_samples",
    "get_sample_by_id"
]
