"""
Script: tao_shortcut_desktop.py
Tạo Shortcut icon 'Socrates Nhí 💡' trực tiếp trên màn hình Desktop của bạn.
Nhấp đúp vào icon trên Desktop để mở ngay Cửa sổ Ứng dụng Riêng (Dedicated App Window).
"""

import os
import sys
import subprocess
from pathlib import Path

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

WORKSPACE_ROOT = Path(__file__).resolve().parent

# Tìm đường dẫn Desktop thực tế của người dùng
desktop_candidates = [
    Path.home() / "OneDrive" / "Desktop",
    Path.home() / "Desktop",
    Path(os.environ.get("USERPROFILE", "")) / "OneDrive" / "Desktop",
    Path(os.environ.get("USERPROFILE", "")) / "Desktop",
]

dest_dir = None
for d in desktop_candidates:
    if d.exists():
        dest_dir = d
        break

if not dest_dir:
    dest_dir = Path.home() / "Desktop"
    dest_dir.mkdir(parents=True, exist_ok=True)

lnk_path = dest_dir / "Socrates_Nhi.lnk"
target_vbs = WORKSPACE_ROOT / "Chay_Socrates_Nhi.vbs"

# Dùng PowerShell WScript.Shell để tạo shortcut Windows chuẩn
ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{lnk_path}')
$s.TargetPath = '{target_vbs}'
$s.WorkingDirectory = '{WORKSPACE_ROOT}'
$s.Description = 'Socrates Nhí v3.0 - Trợ lý AI gợi mở tư duy KHTN THCS'
$s.IconLocation = 'C:\\Windows\\System32\\shell32.dll,43'
$s.Save()
"""

try:
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
    if lnk_path.exists():
        print(f"[OK] Đã tạo thành công biểu tượng ứng dụng trên Desktop:")
        print(f"👉 {lnk_path}")
    else:
        print(f"[Lỗi] Không thể tạo shortcut: {res.stderr}")
except Exception as e:
    print(f"[Lỗi]: {e}")
