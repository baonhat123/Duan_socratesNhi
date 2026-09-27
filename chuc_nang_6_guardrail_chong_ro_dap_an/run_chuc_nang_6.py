"""
Runner: run_chuc_nang_6.py
Chạy độc lập kiểm thử Chức năng 6: Bảng Điều Khiển An Toàn & Hậu Kiểm Chống Rò Đáp Án 3 Tầng (FR-07)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+)
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft
from chuc_nang_6_guardrail_chong_ro_dap_an.guardrail_view import GuardrailPlaygroundView


def main(page: ft.Page):
    page.title = "Socrates Nhí - Chức năng 6: Bảng Điều Khiển An Toàn 3 Tầng (FR-07)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.GREY_50

    if hasattr(page, "window") and page.window is not None:
        try:
            page.window.width = 1080
            page.window.height = 920
        except Exception:
            pass

    view = GuardrailPlaygroundView(
        page=page,
        is_standalone=True
    )
    page.add(view.build())


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
    else:
        raise RuntimeError("Không tìm thấy hàm khởi chạy Flet!")
