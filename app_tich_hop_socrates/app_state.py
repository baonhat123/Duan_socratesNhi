"""
Module: app_state.py
Ứng dụng Tích hợp Socrates Nhí (Kết hợp Đầy đủ Chức năng 1, 2, 3, 4)
Đặc tả: Socrates Nhí v3.0

Quản lý trạng thái phiên làm việc liên tục của học sinh qua 4 bước:
- Bước 1: Tiếp nhận đề bài (ProblemInput từ chuc_nang_1_nhap_de)
- Bước 2: Trích xuất OCR & Xác nhận nội dung (ConfirmedProblem từ chuc_nang_2_ocr_xac_nhan)
- Bước 3: Phân loại kiến thức bài toán & Bản đồ khái niệm (ClassificationResult từ chuc_nang_3_phan_loai_kien_thuc)
- Bước 4: Chu trình gợi mở Socratic 5 pha (từ chuc_nang_4_hoi_thoai_socratic)
"""

from dataclasses import dataclass
from typing import Optional
from chuc_nang_1_nhap_de.input_model import ProblemInput
from chuc_nang_2_ocr_xac_nhan.ocr_model import OcrResult, ConfirmedProblem
from chuc_nang_3_phan_loai_kien_thuc.classifier_model import ClassificationResult


class AppStep:
    STEP_1_INPUT = "step_1_input"            # Bước 1: Nhập đề bài
    STEP_2_OCR = "step_2_ocr"                # Bước 2: Trích xuất & Sửa OCR
    STEP_3_CLASSIFIER = "step_3_classifier"  # Bước 3: Phân loại & Bản đồ khái niệm
    STEP_4_SOCRATIC = "step_4_socratic"      # Bước 4: Hội thoại Socratic 5 pha


@dataclass
class SessionState:
    """
    Trạng thái phiên làm việc hoàn chỉnh của học sinh xuyên suốt 4 bước.
    """
    current_step: str = AppStep.STEP_1_INPUT
    problem_input: Optional[ProblemInput] = None
    ocr_result: Optional[OcrResult] = None
    confirmed_problem: Optional[ConfirmedProblem] = None
    classification_result: Optional[ClassificationResult] = None
    is_offline_demo: bool = False

    def reset(self):
        """Khôi phục trạng thái ban đầu."""
        self.current_step = AppStep.STEP_1_INPUT
        self.problem_input = None
        self.ocr_result = None
        self.confirmed_problem = None
        self.classification_result = None
