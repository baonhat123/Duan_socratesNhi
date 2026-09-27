"""
File: main.py (Workspace Root)
Khởi chạy Ứng dụng Tích hợp Hoàn chỉnh Socrates Nhí
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)
"""

import sys
from pathlib import Path

# Thêm thư mục hiện tại vào sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft
from app_tich_hop_socrates.main_app import main

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
