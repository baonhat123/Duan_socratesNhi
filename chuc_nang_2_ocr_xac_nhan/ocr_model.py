"""
Module: ocr_model.py
Chức năng 2 (FR-02): Trích xuất OCR & Xác nhận đề bài
Đặc tả: Socrates Nhí v3.0

Mô hình dữ liệu lưu trữ kết quả nhận diện OCR, thông tin độ nét ảnh
và trạng thái xác nhận / sửa đổi của học sinh.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class OcrResult:
    """
    Kết quả trích xuất ban đầu từ ảnh đề bài.
    """
    raw_text: str = ""                         # Văn bản thô ban đầu nhận dạng được
    formatted_text: str = ""                   # Văn bản đã chuẩn hóa công thức Unicode
    formulas_detected: List[str] = field(default_factory=list)  # Danh sách công thức phát hiện
    units_detected: List[str] = field(default_factory=list)     # Danh sách đơn vị đo phát hiện
    sharpness_score: float = 0.0               # Điểm độ nét của ảnh (0 - 100%)
    is_blurry: bool = False                    # True nếu ảnh quá mờ/nghiêng không đọc rõ
    confidence_score: float = 0.0              # Độ tin cậy OCR (0.0 đến 1.0)
    error_message: Optional[str] = None        # Thông báo lỗi nếu có
    source_file_path: Optional[str] = None     # Đường dẫn file ảnh nguồn

    @property
    def is_usable(self) -> bool:
        """Đạt tiêu chí chấp nhận FR-02: Không mờ và có nội dung văn bản."""
        return not self.is_blurry and bool(self.formatted_text.strip()) and self.error_message is None


@dataclass
class ConfirmedProblem:
    """
    Đối tượng đề bài hoàn chỉnh sau khi học sinh đã kiểm tra và xác nhận/sửa lỗi.
    Sẵn sàng chuyển giao cho Chức năng 3 (Phân loại kiến thức) & Chức năng 4 (Socratic State Machine).
    """
    original_text: str = ""                         # Văn bản OCR ban đầu
    confirmed_text: str = ""                        # Văn bản cuối cùng sau khi học sinh đã sửa
    was_edited: bool = False                        # Học sinh có chỉnh sửa chữ nào không
    formulas: List[str] = field(default_factory=list)
    units: List[str] = field(default_factory=list)
    source_type: str = "image"                      # "image", "text", hoặc "sample"
    image_path: Optional[str] = None
    confirmed_at: datetime = field(default_factory=datetime.now)
    confidence_score: float = 1.0                   # Độ tin cậy OCR / chuẩn hóa
    original_ocr_text: Optional[str] = None         # Bí danh tương thích ngược

    def __post_init__(self):
        if self.original_ocr_text and not self.original_text:
            self.original_text = self.original_ocr_text
        elif self.original_text and not self.original_ocr_text:
            self.original_ocr_text = self.original_text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "confirmed_text": self.confirmed_text,
            "was_edited": self.was_edited,
            "formulas": self.formulas,
            "units": self.units,
            "source_type": self.source_type,
            "image_path": self.image_path,
            "confirmed_at": self.confirmed_at.isoformat()
        }
