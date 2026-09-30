"""
Runner: run_chuc_nang_4.py
Chạy độc lập kiểm thử Chức năng 4 (FR-04: Hội thoại gợi mở theo State Machine Socratic 5 pha)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+)
"""

import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft
from chuc_nang_4_hoi_thoai_socratic.socratic_view import SocraticChatView


def main(page: ft.Page):
    page.title = "Socrates Nhí - Chức năng 4: Hội thoại Socratic 5 pha (FR-04)"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Thiết lập kích thước cửa sổ an toàn
    if hasattr(page, "window") and page.window is not None:
        try:
            page.window.width = 950
            page.window.height = 850
        except Exception:
            pass

    def on_session_complete(summary_data: dict):
        print("\n" + "=" * 60)
        print(" [CHỨC NĂNG 4 THÀNH CÔNG] ĐÃ HOÀN THÀNH PHIÊN HỌC SOCRATIC")
        print("=" * 60)
        print(f"Tổng số lượt hoàn thành: {summary_data.get('turn_count')}")
        print(f"Pha kết thúc: {summary_data.get('next_phase')}")
        print("=" * 60 + "\n")

    chat_view = SocraticChatView(page, on_session_complete=on_session_complete, is_standalone=True)
    page.add(chat_view.build())


if __name__ == "__main__":
    from app_tich_hop_socrates.app_launcher import safe_run_app
    safe_run_app(main)

