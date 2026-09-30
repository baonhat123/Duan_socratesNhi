"""
Module: app_state.py
Ứng dụng Tích hợp Socrates Nhí (Kết hợp Đầy đủ Chức năng 1, 2, 3, 4 & 5)
Đặc tả: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Quản lý trạng thái phiên làm việc liên tục của học sinh qua 5 Trạm:
- Trạm 1: Tiếp nhận đề bài (ProblemInput từ chuc_nang_1_nhap_de)
- Trạm 2: Trích xuất OCR & Xác nhận nội dung (ConfirmedProblem từ chuc_nang_2_ocr_xac_nhan)
- Trạm 3: Phân loại kiến thức bài toán & Bản đồ khái niệm (ClassificationResult từ chuc_nang_3_phan_loai_kien_thuc)
- Trạm 4: Chu trình gợi mở Socratic 5 pha (từ chuc_nang_4_hoi_thoai_socratic)
- Trạm 5: Sơ đồ Tư duy & Tự đúc kết, Khảo sát 1-5 sao (từ chuc_nang_5_so_do_tong_ket)
"""

from dataclasses import dataclass
from typing import Optional
from chuc_nang_1_nhap_de.input_model import ProblemInput
from chuc_nang_2_ocr_xac_nhan.ocr_model import OcrResult, ConfirmedProblem
from chuc_nang_3_phan_loai_kien_thuc.classifier_model import ClassificationResult
from chuc_nang_5_so_do_tong_ket.mindmap_model import SessionSummary
from app_tich_hop_socrates.auth_service import UserAccount


class AppStep:
    STEP_1_INPUT = "step_1_input"            # Trạm 1: Nhập đề bài
    STEP_2_OCR = "step_2_ocr"                # Trạm 2: Trích xuất & Sửa OCR
    STEP_3_CLASSIFIER = "step_3_classifier"  # Trạm 3: Phân loại & Bản đồ khái niệm
    STEP_4_SOCRATIC = "step_4_socratic"      # Trạm 4: Hội thoại Socratic 5 pha
    STEP_5_MINDMAP = "step_5_mindmap"        # Trạm 5: Sơ đồ Tư duy & Tổng kết


@dataclass
class SessionState:
    """
    Trạng thái phiên làm việc hoàn chỉnh của học sinh xuyên suốt 5 trạm.
    """
    current_step: str = AppStep.STEP_1_INPUT
    problem_input: Optional[ProblemInput] = None
    ocr_result: Optional[OcrResult] = None
    confirmed_problem: Optional[ConfirmedProblem] = None
    classification_result: Optional[ClassificationResult] = None
    session_summary: Optional[SessionSummary] = None
    is_offline_demo: bool = False
    is_socratic_completed: bool = False  # Đã hoàn thành tự đúc kết kiến thức cốt lõi chưa
    current_user: Optional[UserAccount] = None  # Tài khoản học sinh đang đăng nhập

    def reset(self):
        """Khôi phục trạng thái ban đầu."""
        self.current_step = AppStep.STEP_1_INPUT
        self.problem_input = None
        self.ocr_result = None
        self.confirmed_problem = None
        self.classification_result = None
        self.session_summary = None
        self.is_socratic_completed = False
