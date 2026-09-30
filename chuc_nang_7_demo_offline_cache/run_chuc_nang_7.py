"""
Runner: run_chuc_nang_7.py
Chạy độc lập kiểm thử Chức năng 7: Chế Độ Demo Offline & Ngân Hàng 12 Bài Mẫu KHTN 7 Đủ 5 Pha (FR-10)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+)
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft
from chuc_nang_7_demo_offline_cache.offline_view import OfflineCacheControlView


def main(page: ft.Page):
    page.title = "Socrates Nhí - Chức năng 7: Chế Độ Demo Offline & 12 Bài Mẫu 5 Pha (FR-10)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.GREY_50

    if hasattr(page, "window") and page.window is not None:
        try:
            page.window.width = 1120
            page.window.height = 920
        except Exception:
            pass

    def on_study(prob):
        page.open(
            ft.SnackBar(
                content=ft.Text(f"🚀 Ban Giám Khảo đã chọn bài: {prob.title} ({prob.problem_id})!"),
                bgcolor=ft.Colors.INDIGO_700
            )
        )
        page.update()

    view = OfflineCacheControlView(
        page=page,
        on_select_problem_for_study=on_study,
        is_standalone=True
    )
    page.add(view.build())


if __name__ == "__main__":
    from app_tich_hop_socrates.app_launcher import safe_run_app
    safe_run_app(main)

