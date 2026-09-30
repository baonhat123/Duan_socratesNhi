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
from app_tich_hop_socrates.ai_service import load_project_env
load_project_env()

from app_tich_hop_socrates.main_app import main
from app_tich_hop_socrates.app_launcher import safe_run_app

if __name__ == "__main__":
    safe_run_app(main)

