"""
Runner Độc Lập: run_chuc_nang_8.py
Chức năng 8: Rubric Đánh giá Tiến bộ Lập luận (0-6 điểm) & Bảng 5 Chỉ số Đo lường Sư phạm
Đặc tả dự án: Socrates Nhí v3.0 (Mục 3 & Mục 16.3)
Tương thích Flet 1.0+ và Flet 0.x
"""

import sys
import os
from pathlib import Path

# Đảm bảo import được các module từ thư mục gốc
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import flet as ft
from chuc_nang_8_rubric_danh_gia_tien_bo.rubric_view import RubricDashboardView


def main(page: ft.Page):
    page.title = "Socrates Nhí - Chức năng 8: Rubric Đánh giá Tiến bộ Sư phạm & 5 Chỉ số Khoa học (Mục 16.3 & 3)"
    if hasattr(page, "window") and page.window is not None:
        try:
            page.window.width = 980
            page.window.height = 720
            page.window.min_width = 800
            page.window.min_height = 600
        except Exception:
            pass
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    dashboard = RubricDashboardView(page=page, is_standalone=True)
    page.add(dashboard.build())
    page.update()


if __name__ == "__main__":
    from app_tich_hop_socrates.app_launcher import safe_run_app
    safe_run_app(main)

