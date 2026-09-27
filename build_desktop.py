"""
File: build_desktop.py
Tự động đóng gói ứng dụng Socrates Nhí thành tệp thực thi độc lập (Standalone .exe)
Đặc tả: Socrates Nhí v3.0 (Mục 8.1 & Mục 18 - Đóng gói chạy Offline cho Ban Giám khảo)

Cách sử dụng:
    python build_desktop.py
Hoặc chạy tệp:
    build_windows.bat
"""

import sys
import subprocess
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent

def check_pyinstaller():
    """Kiểm tra xem PyInstaller đã được cài đặt chưa."""
    try:
        import PyInstaller
        print(f"[OK] Đã tìm thấy PyInstaller: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("[Thông báo] Chưa cài đặt PyInstaller. Đang tiến hành cài đặt nhanh...")
        res = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=False)
        return res.returncode == 0

def build_executable():
    """Thực thi lệnh đóng gói PyInstaller."""
    print("=" * 60)
    print("🚀 BẮT ĐẦU ĐÓNG GÓI ỨNG DỤNG SOCRATES NHÍ CHO WINDOWS DESKTOP")
    print("=" * 60)

    if not check_pyinstaller():
        print("[LỖI] Không thể cài đặt PyInstaller. Hãy chạy: pip install pyinstaller")
        return False

    app_name = "Socrates_Nhi"
    main_script = WORKSPACE_ROOT / "main.py"
    dist_dir = WORKSPACE_ROOT / "dist"
    build_dir = WORKSPACE_ROOT / "build"

    # Danh sách các thư mục mã nguồn chức năng cần gom kèm
    sub_packages = [
        "chuc_nang_1_nhap_de",
        "chuc_nang_2_ocr_de_bai",
        "chuc_nang_3_phan_loai_kien_thuc",
        "chuc_nang_4_hoi_thoai_socratic",
        "chuc_nang_5_so_do_tu_duy",
        "chuc_nang_6_danh_gia_rubric",
        "chuc_nang_7_demo_offline_cache",
        "chuc_nang_8_tom_tat_khao_sat",
        "app_tich_hop_socrates"
    ]

    add_data_args = []
    for pkg in sub_packages:
        pkg_path = WORKSPACE_ROOT / pkg
        if pkg_path.exists():
            add_data_args.extend(["--add-data", f"{pkg_path};{pkg}"])

    # Thêm .env.example
    env_example = WORKSPACE_ROOT / ".env.example"
    if env_example.exists():
        add_data_args.extend(["--add-data", f"{env_example};."])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", app_name,
        "--onedir",             # Đóng gói dạng thư mục ứng dụng hoàn chỉnh
        "--windowed",           # Ẩn cửa sổ dòng lệnh đen khi mở giao diện
        "--noconfirm",          # Ghi đè thư mục dist cũ không cần hỏi
        "--clean",              # Dọn dẹp cache build
    ] + add_data_args + [
        "--hidden-import", "PIL",
        "--hidden-import", "flet",
        "--hidden-import", "dotenv",
        str(main_script)
    ]

    print(f"\n[Đang chạy lệnh PyInstaller]: {' '.join(cmd[:10])} ...\n")
    result = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT))

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ ĐÓNG GÓI THÀNH CÔNG!")
        output_folder = dist_dir / app_name
        exe_file = output_folder / f"{app_name}.exe"

        # Sao chép .env.example sang thư mục dist
        if env_example.exists() and output_folder.exists():
            shutil.copy2(env_example, output_folder / ".env.example")
            # Tạo sẵn tệp .env rỗng nếu chưa có
            target_env = output_folder / ".env"
            if not target_env.exists():
                shutil.copy2(env_example, target_env)

        print(f"📁 Thư mục ứng dụng: {output_folder}")
        print(f"🎯 Tệp chạy chính: {exe_file}")
        print("💡 Ban Giám khảo có thể nhấp đúp vào tệp .exe để chạy trực tiếp không cần cài đặt Python hay thư viện!")
        print("=" * 60)
        return True
    else:
        print("\n❌ Đóng gói thất bại. Vui lòng kiểm tra thông báo lỗi ở trên.")
        return False

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
