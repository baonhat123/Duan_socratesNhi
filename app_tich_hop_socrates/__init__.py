"""
Package: app_tich_hop_socrates
Ứng dụng Tích hợp Hoàn chỉnh Socrates Nhí (Flet + OpenAI-compatible)
Kết hợp Chức năng 1 (Tiếp nhận đề) và Chức năng 2 (Trích xuất OCR & Xác nhận)
"""

from .app_state import SessionState, AppStep
from .main_app import SocratesIntegratedApp, main

__all__ = ["SessionState", "AppStep", "SocratesIntegratedApp", "main"]
