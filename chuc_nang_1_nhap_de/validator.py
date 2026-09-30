"""
Module: validator.py
Chức năng 1 (FR-01): Nhập đề bài & Kiểm tra hợp lệ
Đặc tả: Socrates Nhí v3.0

Xử lý các tiêu chí chấp nhận:
- Giới hạn tệp <= 5 MB.
- Chỉ chấp nhận ảnh JPG/PNG hợp lệ.
- Kiểm tra PII cơ bản (số điện thoại, thông tin cá nhân) để cảnh báo học sinh.
- Lưu trữ tệp tạm an toàn trong thư mục temp (chuẩn bị cho xóa sau phiên theo mục 17.2).
"""

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Optional, List
from PIL import Image

from .input_model import ProblemInput, InputType

# Giới hạn kích thước tệp theo FR-01: 5 MB
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5,242,880 bytes
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# Thư mục tạm dành cho phiên làm việc Socrates Nhí
SOCRATES_TEMP_DIR = Path(tempfile.gettempdir()) / "socrates_nhi_uploads"
SOCRATES_TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Thư mục tài nguyên dùng chung phục vụ Flet Web Asset Server
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = WORKSPACE_ROOT / "assets"
ASSETS_UPLOADS_DIR = ASSETS_DIR / "uploads"
ASSETS_SAMPLE_DIR = ASSETS_DIR / "sample_assets"
ASSETS_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def resolve_image_asset_src(image_path: str) -> str:
    """
    Chuyển đổi đường dẫn ảnh cục bộ sang URL Web Asset tương thích 100% với Flet Web & Desktop.
    - Đảm bảo file được đồng bộ vào thư mục assets/ của dự án để FastAPI phục vụ tĩnh.
    - Trả về đường dẫn Web Asset (ví dụ: '/uploads/abc.png' hoặc '/sample_assets/xyz.png').
    """
    if not image_path:
        return ""
    p = Path(image_path)

    # 1. Kiểm tra nếu file trùng tên trong assets/sample_assets/
    sample_check = ASSETS_SAMPLE_DIR / p.name
    if sample_check.exists():
        return f"/sample_assets/{p.name}"

    if not p.exists():
        return image_path

    # 2. Nếu file đã nằm trong ASSETS_DIR
    try:
        rel = p.resolve().relative_to(ASSETS_DIR.resolve())
        return f"/{rel.as_posix()}"
    except ValueError:
        pass

    # 3. Nếu nằm ngoài ASSETS_DIR: sao chép ngay vào assets/uploads/
    ASSETS_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = ASSETS_UPLOADS_DIR / f"img_{os.urandom(4).hex()}_{p.name}"
    try:
        shutil.copy2(p, dest)
        return f"/uploads/{dest.name}"
    except Exception as e:
        print(f"[Asset Sync Error] {e}")
        return image_path



def validate_file_size(file_size_bytes: int) -> Tuple[bool, Optional[str]]:
    """Kiểm tra kích thước tệp không vượt quá 5MB."""
    if file_size_bytes <= 0:
        return False, "Tệp được chọn không có nội dung (0 bytes)."
    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        size_mb = file_size_bytes / (1024 * 1024)
        return False, f"Tệp ảnh quá lớn ({size_mb:.2f} MB)! Vui lòng chọn ảnh có dung lượng tối đa 5 MB."
    return True, None


def validate_file_format(file_path: str) -> Tuple[bool, Optional[str]]:
    """Kiểm tra định dạng phần mở rộng và tính toàn vẹn của tệp ảnh."""
    path = Path(file_path)
    if not path.exists():
        return False, f"Không tìm thấy tệp tại đường dẫn: {file_path}"
    
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Định dạng tệp '{ext}' không được hỗ trợ. Chỉ chấp nhận ảnh định dạng JPG, JPEG, PNG, WebP hoặc BMP."
    
    # Kiểm tra tệp ảnh thực tế bằng Pillow
    try:
        with Image.open(path) as img:
            img.verify()  # Xác minh đây là file ảnh hợp lệ không bị hỏng
    except Exception as e:
        return False, f"Tệp ảnh bị lỗi hoặc không thể mở được: {str(e)}"
    
    return True, None


def check_pii_and_safety(text: str) -> List[str]:
    """
    Cảnh báo bảo mật thông tin cá nhân (PII) theo mục 17.1 của đặc tả:
    Cảnh báo nếu văn bản có dấu hiệu chứa số điện thoại hoặc từ khóa nhạy cảm.
    """
    warnings = []
    # Phát hiện mẫu số điện thoại Việt Nam (10 chữ số)
    phone_pattern = r"(?:\+84|0)(?:3[2-9]|5[6|8|9]|7[0|6-9]|8[1-5]|9[0-9])[0-9]{7}"
    if re.search(phone_pattern, text):
        warnings.append("Phát hiện dãy số giống số điện thoại. Em hãy che hoặc xóa số điện thoại để bảo vệ thông tin cá nhân nhé!")
    
    # Phát hiện từ khóa tên trường/lớp cụ thể nếu học sinh gõ vào
    class_pattern = r"\b(lớp\s+[0-9]{1,2}[a-zA-Z0-9]*|trường\s+thcs\s+[^\n,.]+)\b"
    if re.search(class_pattern, text, re.IGNORECASE):
        warnings.append("Lưu ý: Bạn không cần nhập tên trường hay lớp học. Ứng dụng luôn ẩn danh để bảo vệ em.")
        
    return warnings


def stage_uploaded_file(source_path: str) -> str:
    """
    Sao chép tệp ảnh đã chọn vào thư mục assets/uploads của ứng dụng
    để vừa phục vụ OCR nội bộ, vừa phục vụ hiển thị trên Flet Web.
    """
    src = Path(source_path)
    dest_filename = f"upload_{os.urandom(4).hex()}_{src.name}"

    ASSETS_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = ASSETS_UPLOADS_DIR / dest_filename
    shutil.copy2(src, dest_path)

    try:
        shutil.copy2(src, SOCRATES_TEMP_DIR / dest_filename)
    except Exception:
        pass

    return str(dest_path)



def process_image_input(file_path: str) -> ProblemInput:
    """
    Tiếp nhận và thẩm định tệp ảnh tải lên cho Chức năng 1.
    """
    path = Path(file_path)
    if not path.exists():
        return ProblemInput(
            input_type=InputType.IMAGE,
            validation_error=f"Không tìm thấy tệp: {file_path}"
        )

    file_size = path.stat().st_size
    # 1. Kiểm tra kích thước
    size_ok, size_err = validate_file_size(file_size)
    if not size_ok:
        return ProblemInput(
            input_type=InputType.IMAGE,
            file_path=file_path,
            file_name=path.name,
            file_size_bytes=file_size,
            validation_error=size_err
        )

    # 2. Kiểm tra định dạng ảnh
    format_ok, format_err = validate_file_format(file_path)
    if not format_ok:
        return ProblemInput(
            input_type=InputType.IMAGE,
            file_path=file_path,
            file_name=path.name,
            file_size_bytes=file_size,
            validation_error=format_err
        )

    # 3. Đưa vào vùng tạm an toàn
    staged_path = stage_uploaded_file(file_path)

    return ProblemInput(
        input_type=InputType.IMAGE,
        file_path=staged_path,
        file_name=path.name,
        file_size_bytes=file_size,
        is_confirmed=False,  # Chưa xác nhận -> Chưa được gửi AI
        safety_warnings=["Lưu ý an toàn: Hãy đảm bảo ảnh đã được che tên, lớp hoặc khuôn mặt."]
    )


def process_text_input(text_content: str) -> ProblemInput:
    """
    Tiếp nhận và thẩm định đề bài dạng văn bản cho Chức năng 1.
    """
    clean_text = text_content.strip()
    if not clean_text:
        return ProblemInput(
            input_type=InputType.TEXT,
            text_content="",
            validation_error="Đề bài không được để trống! Em hãy gõ nội dung câu hỏi hoặc bài tập nhé."
        )

    if len(clean_text) < 5:
        return ProblemInput(
            input_type=InputType.TEXT,
            text_content=clean_text,
            validation_error="Nội dung đề bài quá ngắn. Em hãy cung cấp thêm dữ kiện đề bài nhé."
        )

    warnings = check_pii_and_safety(clean_text)

    return ProblemInput(
        input_type=InputType.TEXT,
        text_content=clean_text,
        is_confirmed=False,  # Chưa xác nhận -> Chưa được gửi AI
        safety_warnings=warnings
    )


def process_sample_input(sample_id: str) -> ProblemInput:
    """
    Tiếp nhận và đóng gói đề bài mẫu từ Ngân hàng 12 bài chuẩn KHTN 7.
    """
    from .sample_bank import get_sample_by_id
    sample = get_sample_by_id(sample_id)
    return ProblemInput(
        input_type=InputType.SAMPLE,
        text_content=sample["content"],
        sample_id=sample["id"],
        sample_title=sample["title"],
        is_confirmed=False,
        safety_warnings=[]
    )

