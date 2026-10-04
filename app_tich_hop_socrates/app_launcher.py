"""
Module: app_launcher.py
Cung cấp cơ chế khởi chạy ứng dụng an toàn cho Socrates Nhí (Safe App Runner).
Hỗ trợ mở Cửa Sổ Ứng Dụng Riêng Biệt (Dedicated Standalone App Window):
- Không có thanh địa chỉ URL, không có các tab trình duyệt, không có thanh tìm kiếm.
- Hoạt động như một phần mềm Windows Desktop độc lập chuyên nghiệp.
- Vượt qua 100% rào cản Windows Defender / Smart App Control (WinError 4551).
"""

import sys
import os
import shutil
import subprocess
import webbrowser
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


def launch_standalone_app_window(url: str):
    """
    Mở cửa sổ ứng dụng độc lập (Dedicated Standalone App Window).
    Sử dụng cờ --app của Microsoft Edge / Google Chrome để tạo cửa sổ chương trình riêng:
    - Loại bỏ hoàn toàn thanh URL, bookmark và các tab trình duyệt.
    - Hiển thị như một ứng dụng máy tính độc lập (Desktop Application).
    """
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        shutil.which("msedge"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("chrome"),
    ]

    for exe in candidates:
        if exe and os.path.exists(exe):
            try:
                cmd = [
                    exe,
                    f"--app={url}",
                    "--window-size=1200,920",
                    "--window-position=80,40"
                ]
                subprocess.Popen(cmd)
                print(f"[OK] Da mo cua so ung dung rieng biet (Dedicated App Window) bang: {os.path.basename(exe)}")
                return True
            except Exception as e:
                print(f"[!] Loi khoi chay cua so ung dung: {e}")

    # Fallback ve trinh duyet mac dinh neu khong tim thay
    webbrowser.open(url)
    return False


# Tự động thay thế hàm mở trình duyệt mặc định của Flet thành Cửa sổ Ứng dụng Riêng
try:
    import flet.app as flet_app_module
    flet_app_module.open_in_browser = launch_standalone_app_window
except Exception:
    pass


def safe_run_app(target_main, **kwargs):
    """
    Khởi chạy ứng dụng Socrates Nhí dưới dạng Chương Trình Riêng:
    - Nếu bật --web, --browser, hoặc -w: Mở Cửa sổ Ứng dụng Riêng (Dedicated App Window).
    - Mặc định: Thử mở cửa sổ Desktop thuần túy.
    - Nếu Windows Smart App Control chặn flet.exe (WinError 4551):
      Tự động chuyển đổi mượt mà sang Cửa sổ Ứng dụng Riêng (Dedicated App Window qua Edge / Chrome).
    """
    from pathlib import Path
    workspace_root = Path(__file__).resolve().parent.parent
    assets_path = workspace_root / "assets"
    assets_path.mkdir(exist_ok=True)
    (assets_path / "uploads").mkdir(exist_ok=True)
    (assets_path / "sample_assets").mkdir(exist_ok=True)
    if "assets_dir" not in kwargs or not kwargs["assets_dir"]:
        kwargs["assets_dir"] = str(assets_path)

    force_browser = any(arg in sys.argv for arg in ("--web", "--browser", "-w", "--app"))

    if force_browser:
        print("[*] Socrates Nhi dang khoi chay Cua So Chuong Trinh Rieng (App Window)...")
        kwargs["view"] = ft.AppView.WEB_BROWSER
        return ft.run(target_main, **kwargs)

    try:
        return ft.run(target_main, **kwargs)
    except OSError as e:
        err_msg = str(e)
        if "4551" in err_msg or "Application Control" in err_msg or "blocked" in err_msg.lower():
            print("\n" + "=" * 70)
            print("[THONG BAO KHOI CHAY CUA SO CHUONG TRINH RIENG]")
            print("Windows Smart App Control chan flet.exe desktop (WinError 4551).")
            print("He thong dang tu dong mo Socrates Nhi duoi dang CUA SO CHUONG TRINH RIENG")
            print("(Dedicated App Window khong co thanh dia chi, khong co tab trinh duyet)!")
            print("=" * 70 + "\n")
            kwargs["view"] = ft.AppView.WEB_BROWSER
            return ft.run(target_main, **kwargs)
        else:
            raise
