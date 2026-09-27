"""
Module: app_state.py
Ứng dụng Tích hợp Socrates Nhí (Kết hợp Chức năng 1 & Chức năng 2)
Đặc tả: Socrates Nhí v3.0

Quản lý trạng thái phiên làm việc liên tục của học sinh qua các màn hình:
- Bước 1: Tiếp nhận đề bài (ProblemInput từ chuc_nang_1_nhap_de)
- Bước 2: Trích xuất OCR & Xác nhận nội dung (ConfirmedProblem từ chuc_nang_2_ocr_xac_nhan)
- Bước 3: Sẵn sàng kết nối bộ điều phối Socratic
"""

from dataclasses import dataclass, field
from typing import Optional, List
from chuc_nang_1_nhap_de.input_model import ProblemInput, InputType
from chuc_nang_2_ocr_xac_nhan.ocr_model import OcrResult, ConfirmedProblem


class AppStep:
    STEP_1_INPUT = "step_1_input"      # Màn hình 1: Nhập đề bài
    STEP_2_OCR = "step_2_ocr"          # Màn hình 2: Trích xuất & Sửa OCR
    STEP_3_SOCRATIC = "step_3_socratic" # Màn hình 3: Hội thoại Socratic (sắp tới)


@dataclass
class SessionState:
    """
    Trạng thái phiên làm việc hoàn chỉnh của học sinh.
    Được chia sẻ xuyên suốt toàn bộ luồng tương tác ứng dụng.
    """
    current_step: str = AppStep.STEP_1_INPUT
    problem_input: Optional[ProblemInput] = None
    ocr_result: Optional[OcrResult] = None
    confirmed_problem: Optional[ConfirmedProblem] = None
    is_offline_demo: bool = False

    def reset(self):
        """Khôi phục trạng thái ban đầu."""
        self.current_step = AppStep.STEP_1_INPUT
        self.problem_input = None
        self.ocr_result = None
        self.confirmed_problem = None
