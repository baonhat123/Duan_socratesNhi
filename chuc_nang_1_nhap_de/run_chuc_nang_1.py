"""
Runner: run_chuc_nang_1.py
Chạy độc lập kiểm thử Chức năng 1 (FR-01: Nhập đề bài)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+ và Flet 0.x)
"""

import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft
from chuc_nang_1_nhap_de.ui_component import ProblemInputView
from chuc_nang_1_nhap_de.input_model import ProblemInput


def main(page: ft.Page):
    page.title = "Socrates Nhí - Chức năng 1: Nhập đề bài (FR-01)"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Thiết lập kích thước cửa sổ tương thích mọi phiên bản Flet
    if hasattr(page, "window") and page.window is not None:
        try:
            page.window.width = 900
            page.window.height = 800
        except Exception:
            pass

    def on_problem_confirmed(problem: ProblemInput):
        print("\n" + "=" * 55)
        print(" [CHỨC NĂNG 1 THÀNH CÔNG] ĐÃ XÁC NHẬN ĐỀ BÀI")
        print("=" * 55)
        print(f"Loại đầu vào: {problem.input_type.value}")
        print(f"Trạng thái xác nhận (is_confirmed): {problem.is_confirmed}")
        if problem.file_path:
            print(f"Đường dẫn file tạm an toàn: {problem.file_path}")
            print(f"Dung lượng: {problem.file_size_mb:.2f} MB")
        if problem.text_content:
            print(f"Nội dung văn bản: {problem.text_content[:100]}...")
        if problem.safety_warnings:
            print(f"Cảnh báo an toàn PII: {problem.safety_warnings}")
        print("Sẵn sàng chuyển giao dữ liệu sang Chức năng 2 (FR-02: OCR & Xác nhận)!")
        print("=" * 55 + "\n")

    input_view = ProblemInputView(page, on_confirm=on_problem_confirmed)
    page.add(input_view.build())


if __name__ == "__main__":
    from app_tich_hop_socrates.app_launcher import safe_run_app
    safe_run_app(main)

