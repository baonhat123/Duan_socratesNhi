"""
Runner: run_app.py
Khởi chạy ứng dụng tích hợp hoàn chỉnh Socrates Nhí
Kết hợp: Chức năng 1 (Nhập đề) + Chức năng 2 (Trích xuất & Sửa OCR)
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft
from app_tich_hop_socrates.main_app import main

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
