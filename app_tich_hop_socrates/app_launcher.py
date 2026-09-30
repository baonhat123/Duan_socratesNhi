"""
Module: app_launcher.py
Cung cấp cơ chế khởi chạy ứng dụng an toàn cho Socrates Nhí (Safe App Runner).
Hỗ trợ tương thích cả Desktop Client lẫn Trình duyệt Web (Web Browser),
tự động xử lý chính sách Windows Defender / Smart App Control (WinError 4551).
"""

import sys
import flet as ft

# Đảm bảo mã hóa console không bị lỗi UnicodeEncodeError trên terminal Windows (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def safe_run_app(target_main, **kwargs):
    """
    Khởi chạy ứng dụng Flet an toàn và linh hoạt:
    - Nếu có tham số dòng lệnh --web, --browser, hoặc -w: Chạy thẳng trên trình duyệt.
    - Mặc định: Thử mở cửa sổ Desktop.
    - Nếu Windows Smart App Control chặn flet.exe (WinError 4551 / Application Control policy):
      Tự động bắt lỗi và chuyển hướng mượt mà sang Trình duyệt Web (Edge / Chrome).
    """
    from pathlib import Path
    workspace_root = Path(__file__).resolve().parent.parent
    assets_path = workspace_root / "assets"
    assets_path.mkdir(exist_ok=True)
    (assets_path / "uploads").mkdir(exist_ok=True)
    (assets_path / "sample_assets").mkdir(exist_ok=True)
    if "assets_dir" not in kwargs or not kwargs["assets_dir"]:
        kwargs["assets_dir"] = str(assets_path)

    force_browser = any(arg in sys.argv for arg in ("--web", "--browser", "-w"))


    if force_browser:
        print("[*] Socrates Nhi dang khoi chay tren Trinh duyet Web...")
        kwargs["view"] = ft.AppView.WEB_BROWSER
        if hasattr(ft, "run"):
            return ft.run(target_main, **kwargs)
        elif hasattr(ft, "app"):
            return ft.app(target=target_main, **kwargs)

    try:
        if hasattr(ft, "run"):
            return ft.run(target_main, **kwargs)
        elif hasattr(ft, "app"):
            return ft.app(target=target_main, **kwargs)
    except OSError as e:
        err_msg = str(e)
        if "4551" in err_msg or "Application Control" in err_msg or "blocked" in err_msg.lower():
            print("\n" + "=" * 70)
            print("[THONG BAO TU DONG CHUYEN DOI]")
            print("Windows Smart App Control da chan file flet.exe desktop (WinError 4551).")
            print("He thong dang tu dong mo Socrates Nhi tren Trinh duyet Web (Edge / Chrome)...")
            print("Toan bo giao dien, du lieu va tinh nang AI hoat dong day du 100%!")
            print("=" * 70 + "\n")
            kwargs["view"] = ft.AppView.WEB_BROWSER
            if hasattr(ft, "run"):
                return ft.run(target_main, **kwargs)
            elif hasattr(ft, "app"):
                return ft.app(target=target_main, **kwargs)
        else:
            raise
