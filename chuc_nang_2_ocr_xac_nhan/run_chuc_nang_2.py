"""
Runner: run_chuc_nang_2.py
Chạy độc lập kiểm thử Chức năng 2 (FR-02: Trích xuất OCR & Xác nhận đề bài)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+)
"""

import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft
from chuc_nang_2_ocr_xac_nhan.ocr_view import OcrConfirmationView
from chuc_nang_2_ocr_xac_nhan.ocr_model import ConfirmedProblem


def main(page: ft.Page):
    page.title = "Socrates Nhí - Chức năng 2: Trích xuất OCR & Xác nhận đề bài (FR-02)"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Thiết lập kích thước cửa sổ an toàn
    if hasattr(page, "window") and page.window is not None:
        try:
            page.window.width = 950
            page.window.height = 850
        except Exception:
            pass

    def on_problem_confirmed(problem: ConfirmedProblem):
        print("\n" + "=" * 60)
        print(" [CHỨC NĂNG 2 THÀNH CÔNG] ĐÃ XÁC NHẬN NỘI DUNG ĐỀ BÀI")
        print("=" * 60)
        print(f"Văn bản chốt: {problem.confirmed_text}")
        print(f"Học sinh có sửa đổi không (was_edited): {problem.was_edited}")
        if problem.formulas:
            print(f"Công thức KHTN phát hiện: {problem.formulas}")
        if problem.units:
            print(f"Đơn vị đo lường: {problem.units}")
        print("Sẵn sàng chuyển giao dữ liệu sang Chức năng 3 (Phân loại kiến thức)!")
        print("=" * 60 + "\n")

    ocr_view = OcrConfirmationView(page, on_confirm=on_problem_confirmed, is_standalone=True)
    page.add(ocr_view.build())


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
    else:
        raise RuntimeError("Không tìm thấy hàm khởi chạy Flet!")
