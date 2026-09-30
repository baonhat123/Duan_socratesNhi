"""
Runner: run_chuc_nang_5.py
Chạy độc lập kiểm thử Chức năng 5 (FR-06, FR-08, FR-09: Sơ đồ Tư duy & Tổng kết Buổi học)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+)
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft
from chuc_nang_5_so_do_tong_ket.mindmap_view import MindmapSummaryView


def main(page: ft.Page):
    page.title = "Socrates Nhí - Chức năng 5: Sơ đồ Tư duy & Tổng kết Buổi học (FR-06, FR-08, FR-09)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.GREY_50

    if hasattr(page, "window") and page.window is not None:
        try:
            page.window.width = 1080
            page.window.height = 920
        except Exception:
            pass

    def on_restart():
        print("\n" + "=" * 60)
        print(" [CHỨC NĂNG 5] HỌC SINH YÊU CẦU BẮT ĐẦU BÀI TẬP MỚI!")
        print("=" * 60 + "\n")

    view = MindmapSummaryView(
        page=page,
        problem_text=(
            "Một người đi xe đạp chuyển động đều trên quãng đường thẳng s = 12 km "
            "trong thời gian t = 30 phút. Hãy xác định tốc độ v của người đó theo đơn vị km/h và m/s."
        ),
        topic="Vật lý – Chuyển động và Tốc độ",
        strand_name="Mạch 1: Vật lý THCS (Cơ học & Năng lượng)",
        given_facts=["s = 12 km", "t = 30 phút"],
        core_concepts=["Tốc độ chuyển động", "Đổi đơn vị tốc độ (km/h ↔ m/s)"],
        target_variable="Tốc độ v (km/h và m/s)",
        total_turns=4,
        on_restart=on_restart,
        is_standalone=True
    )
    page.add(view.build())


if __name__ == "__main__":
    from app_tich_hop_socrates.app_launcher import safe_run_app
    safe_run_app(main)

