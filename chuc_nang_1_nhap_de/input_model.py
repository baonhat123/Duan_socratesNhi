"""
Module: input_model.py
Chức năng 1 (FR-01): Nhập đề bài
Đặc tả: Socrates Nhí v3.0

Mô hình dữ liệu tiếp nhận và đóng gói đề bài của học sinh (Văn bản hoặc Ảnh JPG/PNG).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class InputType(str, Enum):
    TEXT = "text"          # Học sinh tự gõ đề bài
    IMAGE = "image"        # Học sinh tải ảnh bài tập (JPG/PNG <= 5MB)
    SAMPLE = "sample"      # Học sinh chọn từ ngân hàng đề mẫu KHTN 7


@dataclass
class ProblemInput:
    """
    Đối tượng lưu trữ dữ liệu đầu vào của đề bài.
    Đảm bảo nguyên tắc FR-01: Không gửi sang AI trước khi is_confirmed = True.
    """
    input_type: InputType
    text_content: str = ""
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: int = 0
    is_confirmed: bool = False
    validation_error: Optional[str] = None
    safety_warnings: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def file_size_mb(self) -> float:
        return self.file_size_bytes / (1024 * 1024)

    @property
    def is_valid(self) -> bool:
        return self.validation_error is None and (
            bool(self.text_content.strip()) or (self.file_path is not None and self.file_size_bytes > 0)
        )

    def to_dict(self) -> dict:
        return {
            "input_type": self.input_type.value,
            "text_content": self.text_content,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size_bytes": self.file_size_bytes,
            "file_size_mb": round(self.file_size_mb, 2),
            "is_confirmed": self.is_confirmed,
            "validation_error": self.validation_error,
            "safety_warnings": self.safety_warnings,
            "created_at": self.created_at.isoformat()
        }
