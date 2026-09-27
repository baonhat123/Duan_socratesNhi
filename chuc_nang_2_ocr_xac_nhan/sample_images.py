"""
Module: sample_images.py
Chức năng 2 (FR-02): Tạo và quản lý bộ ảnh mẫu kiểm thử OCR KHTN
Đặc tả: Socrates Nhí v3.0 (Mục 12 - Checklist OCR bộ 20 ảnh)

Tạo sẵn các ảnh mẫu thuộc 4 nhóm kiểm thử:
1. Ảnh chữ in rõ nét (Cơ học / Chuyển động)
2. Ảnh công thức Vật lý (v², km/h, N)
3. Ảnh phương trình Hóa học (H₂O, CO₂, quang hợp)
4. Ảnh mờ cố ý (Kiểm tra từ chối đúng cam kết "không đoán mò")
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

SAMPLE_DIR = Path(__file__).resolve().parent / "sample_assets"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def generate_sample_images() -> dict:
    """Tạo các file ảnh bài tập mẫu phục vụ kiểm thử Chức năng 2."""
    paths = {}

    # 1. Ảnh rõ nét - Cơ học
    path_co_hoc = SAMPLE_DIR / "ocr_co_hoc_toc_do.png"
    img1 = Image.new("RGB", (700, 260), color="#F8FAFC")
    d1 = ImageDraw.Draw(img1)
    d1.rectangle([(10, 10), (690, 250)], outline="#CBD5E1", width=2)
    d1.text((30, 30), "BAI TAP VAT LY 7 - CHUYEN DONG VA TOC DO", fill="#1E293B")
    d1.text((30, 80), "De bai: Mot nguoi di xe dap chuyen dong deu tren quang duong", fill="#334155")
    d1.text((30, 120), "dai s = 12 km trong thoi gian t = 30 phut.", fill="#334155")
    d1.text((30, 160), "Cau hoi: Tinh toc do v cua nguoi do theo don vi km/h va m/s.", fill="#0F172A")
    img1.save(path_co_hoc, format="PNG")
    paths["co_hoc"] = str(path_co_hoc)

    # 2. Ảnh công thức Vật lý (khối lượng, trọng lượng, lũy thừa)
    path_vat_ly = SAMPLE_DIR / "ocr_vat_ly_khoi_luong.png"
    img2 = Image.new("RGB", (700, 260), color="#F0FDF4")
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([(10, 10), (690, 250)], outline="#BBF7D0", width=2)
    d2.text((30, 30), "BAI TAP: KHOI LUONG VA TRONG LUONG", fill="#166534")
    d2.text((30, 80), "Thung hang co khoi luong m = 45 kg dat tren mat dat.", fill="#14532D")
    d2.text((30, 120), "Cong thuc lien he: P = 10m voi he so g = 10 N/kg.", fill="#14532D")
    d2.text((30, 160), "Hoi trong luong P cua thung hang bang bao nhieu Newton (N)?", fill="#052E16")
    img2.save(path_vat_ly, format="PNG")
    paths["vat_ly"] = str(path_vat_ly)

    # 3. Ảnh Hóa học (H2O, CO2, phản ứng hóa học)
    path_hoa_hoc = SAMPLE_DIR / "ocr_hoa_hoc_quang_hop.png"
    img3 = Image.new("RGB", (700, 260), color="#EFF6FF")
    d3 = ImageDraw.Draw(img3)
    d3.rectangle([(10, 10), (690, 250)], outline="#BFDBFE", width=2)
    d3.text((30, 30), "KHTN 7 - PHUONG TRINH QUANG HOP O THUC VAT", fill="#1E40AF")
    d3.text((30, 80), "Phuong trinh tong quat: 6CO2 + 6H2O -> C6H12O6 + 6O2", fill="#1D4ED8")
    d3.text((30, 120), "Dieu kien: Co anh sang mat troi va chat diep luc.", fill="#1E3A8A")
    d3.text((30, 160), "Hay cho biet chat tham gia va chat tao thanh cua phan ung.", fill="#172554")
    img3.save(path_hoa_hoc, format="PNG")
    paths["hoa_hoc"] = str(path_hoa_hoc)

    # 4. Ảnh mờ cố ý (Mô phỏng chụp rung tay / mất nét)
    path_blurry = SAMPLE_DIR / "ocr_anh_mo_rung_tay.png"
    img4 = Image.new("RGB", (700, 260), color="#FEF2F2")
    d4 = ImageDraw.Draw(img4)
    d4.text((30, 50), "De bai thi hoc ki KHTN 7 mo tit khong doc duoc", fill="#991B1B")
    d4.text((30, 100), "s = ??? km, v = ??? m/s, cong thuc bi nhoa", fill="#991B1B")
    # Áp dụng GaussianBlur mạnh
    img4_blurred = img4.filter(ImageFilter.GaussianBlur(radius=9))
    img4_blurred.save(path_blurry, format="PNG")
    paths["blurry"] = str(path_blurry)

    return paths


# Tự động tạo ảnh khi import module
SAMPLE_PATHS = generate_sample_images()
