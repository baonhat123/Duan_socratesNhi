# -*- coding: utf-8 -*-
"""
File: build_desktop.py
Tự động đóng gói ứng dụng Socrates Nhí thành tệp thực thi độc lập (Standalone .exe)
Đặc tả: Socrates Nhí v3.0 (Mục 8.1 & Mục 18 - Đóng gói chạy Offline cho Ban Giám khảo & Khảo sát)

Cách sử dụng:
    python build_desktop.py
Hoặc chạy tệp:
    build_windows.bat
"""

import sys
import subprocess
import shutil
import zipfile
from pathlib import Path

# Cấu hình UTF-8 cho console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE_ROOT = Path(__file__).resolve().parent

def check_pyinstaller():
    """Kiểm tra xem PyInstaller đã được cài đặt chưa."""
    try:
        import PyInstaller
        print(f"[OK] Da tim thay PyInstaller: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("[Thong bao] Chua cai dat PyInstaller. Dang tien hanh cai dat nhanh...")
        res = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=False)
        return res.returncode == 0

def build_executable():
    """Thực thi lệnh đóng gói Flet Pack / PyInstaller."""
    print("=" * 60)
    print("[BAT DAU] DONG GOI UNG DUNG SOCRATES NHI CHO WINDOWS DESKTOP")
    print("=" * 60)

    if not check_pyinstaller():
        print("[LOI] Khong the cai dat PyInstaller. Hay chay: pip install pyinstaller")
        return False

    app_name = "Socrates_Nhi"
    main_script = WORKSPACE_ROOT / "main.py"
    dist_dir = WORKSPACE_ROOT / "dist"
    build_dir = WORKSPACE_ROOT / "build"

    # Danh sách các thư mục mã nguồn chức năng và tài nguyên chuẩn
    sub_packages = [
        "chuc_nang_1_nhap_de",
        "chuc_nang_2_ocr_xac_nhan",
        "chuc_nang_3_phan_loai_kien_thuc",
        "chuc_nang_4_hoi_thoai_socratic",
        "chuc_nang_5_so_do_tong_ket",
        "chuc_nang_6_guardrail_chong_ro_dap_an",
        "chuc_nang_7_demo_offline_cache",
        "chuc_nang_8_rubric_danh_gia_tien_bo",
        "app_tich_hop_socrates",
        "so_tay_hoc_tap",
        "assets"
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
        sys.executable, "-m", "flet_cli.cli", "pack",
        str(main_script),
        "--name", app_name,
        "--onedir",             # Đóng gói dạng thư mục ứng dụng hoàn chỉnh
        "-y",                   # Tự động ghi đè bản build cũ
    ] + add_data_args + [
        "--hidden-import", "PIL",
        "--hidden-import", "dotenv",
    ]

    print(f"\n[Dang chay lenh dong goi Flet Pack]: {' '.join(cmd[:8])} ...\n")
    result = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT))

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("[THANH CONG] DONG GOI HOAN TAT!")
        output_folder = dist_dir / app_name
        exe_file = output_folder / f"{app_name}.exe"

        # Sao chép .env.example sang thư mục dist làm mẫu (KHÔNG CÓ KEY THẬT)
        if env_example.exists() and output_folder.exists():
            shutil.copy2(env_example, output_folder / ".env.example")

        # BẢO MẬT TUYỆT ĐỐI (Mục 8.1 & 19.1): Xóa sạch file .env khỏi dist để không bao giờ lộ API Key
        for bad_env in output_folder.rglob('.env*'):
            if bad_env.is_file() and bad_env.name == '.env':
                try:
                    bad_env.unlink()
                    print("[BAO MAT] Da go bo file .env khoi thu muc dist de bao ve API Key!")
                except Exception:
                    pass

        # Sao chép dữ liệu sổ tay học tập sang thư mục dist nếu chưa có
        source_so_tay = WORKSPACE_ROOT / "so_tay_hoc_tap"
        target_so_tay = output_folder / "so_tay_hoc_tap"
        if source_so_tay.exists() and not target_so_tay.exists():
            shutil.copytree(source_so_tay, target_so_tay)

        # Sao chép assets sang thư mục dist nếu chưa có
        source_assets = WORKSPACE_ROOT / "assets"
        target_assets = output_folder / "assets"
        if source_assets.exists() and not target_assets.exists():
            shutil.copytree(source_assets, target_assets)

        # Tự động nén thành file .zip để người dùng gửi bạn bè khảo sát
        zip_output = dist_dir / f"{app_name}_Windows.zip"
        print(f"\n[Dang nen file ZIP de gui ban be]: {zip_output.name} ...")
        with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_folder.rglob('*'):
                if file_path.is_file():
                    # QUY TẮC AN TOÀN: Tuyệt đối không bao giờ nén file .env vào file zip!
                    if file_path.name == ".env":
                        continue
                    arcname = file_path.relative_to(dist_dir)
                    zipf.write(file_path, arcname)
        
        zip_size_mb = zip_output.stat().st_size / (1024 * 1024)
        print(f"[ZIP FILE SAN SANG]: {zip_output} ({zip_size_mb:.1f} MB)")
        print(f"Thu muc ung dung: {output_folder}")
        print(f"Tep chay chinh: {exe_file}")
        print("Ban co the gui file .zip nay cho ban be, giai nen va nhap dup .exe de khao sat ngay!")
        print("=" * 60)
        return True
    else:
        print("\n[THAT BAI] Dong goi that bai. Vui long kiem tra thong bao loi o tren.")
        return False

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
