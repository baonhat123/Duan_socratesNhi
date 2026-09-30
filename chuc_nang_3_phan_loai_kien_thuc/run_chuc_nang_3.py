"""
Runner: run_chuc_nang_3.py
Chạy độc lập kiểm thử Chức năng 3 (FR-03: Phân loại kiến thức bài toán & Bản đồ khái niệm)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+)
"""

import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft
from chuc_nang_3_phan_loai_kien_thuc.classifier_view import KnowledgeClassifierView
from chuc_nang_3_phan_loai_kien_thuc.classifier_model import ClassificationResult


def main(page: ft.Page):
    page.title = "Socrates Nhí - Chức năng 3: Phân loại kiến thức bài toán (FR-03)"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Thiết lập kích thước cửa sổ an toàn
    if hasattr(page, "window") and page.window is not None:
        try:
            page.window.width = 950
            page.window.height = 850
        except Exception:
            pass

    def on_proceed_to_socratic(res: ClassificationResult):
        print("\n" + "=" * 60)
        print(" [CHỨC NĂNG 3 THÀNH CÔNG] ĐÃ PHÂN LOẠI KIẾN THỨC BÀI TOÁN")
        print("=" * 60)
        print(f"Chủ đề: {res.topic}")
        print(f"Mạch kiến thức: {res.strand.value}")
        print(f"Cấp độ: {res.difficulty.value}")
        print(f"Dữ kiện bóc tách: {res.given_facts}")
        print(f"Đại lượng cần tìm: {res.target_variable}")
        print(f"Khái niệm cốt lõi (tối đa 3): {res.core_concepts}")
        print("Sẵn sàng bước vào Hội thoại Socratic 5 pha!")
        print("=" * 60 + "\n")

    view = KnowledgeClassifierView(
        page,
        on_proceed_to_socratic=on_proceed_to_socratic,
        is_standalone=True
    )
    page.add(view.build())


if __name__ == "__main__":
    from app_tich_hop_socrates.app_launcher import safe_run_app
    safe_run_app(main)

