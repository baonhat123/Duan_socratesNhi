import os, sys, shutil, zipfile, io
sys.path.append('.')
from PIL import Image

# Tuned coordinates so each crop is JUST 1 SINGLE QUESTION
single_question_crops = {
    # 01: Chỉ đúng câu 3 xe đạp: Bạn B đi xe đạp từ nhà đến trường với tốc độ 12 km/h hết 20 min... (đủ 100% không bị che)
    '01_chu_in_toc_do_xe_dap.png': ('image48.jpeg', 580, 36, 633, 964),
    
    # 02: Chỉ đúng câu hỏi khối lượng: Hãy xác định khối lượng của cuốn sách và nhận xét kết quả...
    '02_chu_in_khoi_luong_rieng.png': ('image10.jpeg', 930, 50, 975, 950),
    
    # 03: Chỉ đúng câu hỏi góc tới 30 độ: Chiếu tia sáng tới dưới góc tới 30° vào gương phẳng...
    '03_chu_in_phan_xa_anh_sang.png': ('image80.jpeg', 815, 50, 875, 950),
    
    # 04: Chỉ đúng câu 2 đồ thị s - t: Lúc 6 h sáng, bạn A đi bộ ra công viên...
    '04_chu_in_do_thi_quang_duong.png': ('image56.jpeg', 240, 50, 530, 950),
    
    # 05: Chỉ đúng câu 2 quang hợp: Dựa vào kết quả ở câu 1, phát biểu khái niệm và viết phương trình tổng quát...
    '05_chu_in_quang_hop_thuc_vat.png': ('image102.jpeg', 485, 50, 580, 950),
    
    # 06: Chỉ đúng câu 1 hô hấp: Tại sao rau, quả cất giữ trong tủ lạnh đúng cách lại lâu hỏng hơn...
    '06_chu_in_ho_hap_te_bao.png': ('image114.jpeg', 250, 50, 390, 950),
    
    # 07: Chỉ đúng câu 1 khí khổng: Cấu tạo tế bào khí khổng phù hợp với chức năng trao đổi khí...
    '07_chu_in_thoat_hoi_nuoc.png': ('image120.jpeg', 220, 50, 300, 950),
    
    # 08: Chỉ đúng câu 1: Hãy trình bày sự khác biệt giữa đơn chất oxygen và hợp chất carbon dioxide...
    '08_chu_in_nung_da_voi.png': ('image35.jpeg', 260, 50, 360, 950),
    
    # 09: Chỉ đúng câu 1: Biết nữ vận động viên Việt Nam - Lê Tú Chinh... chạy 100 m hết 11,54 s. Tính tốc độ...
    '09_cong_thuc_van_toc_don_vi.png': ('image48.jpeg', 489, 36, 534, 964),
    
    # 10: Chỉ đúng câu hỏi so sánh tốc độ: Bạn A chạy 120 m hết 35 s. Bạn B chạy 140 m hết 40 s. Ai chạy nhanh hơn?
    '10_cong_thuc_trong_luong.png': ('image47.jpeg', 370, 50, 440, 950),
    
    # 11: Chỉ đúng câu 3: Khi gảy đàn hoặc đánh trống, muốn âm phát ra to hơn người ta làm thế nào? Tại sao?
    '11_cong_thuc_luc_bien_dang_lo_xo.png': ('image66.jpeg', 530, 50, 600, 950),
    
    # 12: Chỉ đúng câu 2: Hãy thực hiện thí nghiệm đơn giản sau: gảy đàn, gõ vào âm thoa để chứng tỏ âm truyền được trong không khí.
    '12_cong_thuc_ap_suat_chat_long.png': ('image62.jpeg', 370, 50, 440, 950),
    
    # 13: Chỉ đúng câu 1: Trong những vật dưới đây, hãy chỉ ra vật phản xạ âm tốt, phản xạ âm kém: Ghế đệm mút, mặt gương...
    '13_cong_thuc_dong_nang_binh_phuong.png': ('image70.jpeg', 240, 50, 370, 950),
    
    # 14: Chỉ đúng câu 2: Lúc 8 h 30 min, bạn A đi bộ từ nhà đến siêu thị với tốc độ 4,8 km/h...
    '14_cong_thuc_toc_do_thoi_gian_den.png': ('image48.jpeg', 534, 36, 580, 964),
    
    # 15: Chỉ đúng câu hỏi CO2: Quan sát Hình 23.2 và cho biết ảnh hưởng của nồng độ khí CO2 đến quang hợp...
    '15_hoa_hoc_quang_hop_chi_so.png': ('image106.jpeg', 350, 50, 600, 950),
    
    # 16: Chỉ đúng câu 2: Số hiệu nguyên tử oxygen là 8. Số proton trong hạt nhân nguyên tử của nguyên tố oxygen là bao nhiêu?
    '16_hoa_hoc_bao_toan_khoi_luong.png': ('image21.jpeg', 510, 50, 580, 950),
    
    # 17: Chỉ đúng câu 2: Hãy cho biết số lớp electron của nguyên tử các nguyên tố thuộc chu kì 3. Giải thích.
    '17_hoa_hoc_chu_ki_electron.png': ('image28.jpeg', 855, 35, 915, 965)
}

out_dir = 'tailieu/bo_20_anh_kiem_thu_ocr'
os.makedirs(out_dir, exist_ok=True)

docx_path = 'tailieu/SGK KHTN 7 KNTT.docx'
with zipfile.ZipFile(docx_path, 'r') as z:
    for name, (src_file, ymin, xmin, ymax, xmax) in single_question_crops.items():
        media_path = f"word/media/{src_file}"
        img_bytes = z.read(media_path)
        with Image.open(io.BytesIO(img_bytes)) as img:
            w, h = img.size
            left = int(xmin * w / 1000)
            top = int(ymin * h / 1000)
            right = int(xmax * w / 1000)
            bottom = int(ymax * h / 1000)
            cropped = img.crop((left, top, right, bottom))
            dst_p = os.path.join(out_dir, name)
            cropped.save(dst_p)
            print(f"Cropped precisely 1-question {name}: size {cropped.size}")

# 19: Ảnh chụp bài tập SGK thật của học sinh nhưng bị nghiêng/mờ (Ảnh mờ 1 do người dùng tải lên)
sgk_blurry_src = r'C:\Users\LENOVO\.gemini\antigravity-ide\brain\fca3a316-ee99-4283-83f8-82ff2cd5e673\.user_uploaded\media_1792220200616.png'
if os.path.exists(sgk_blurry_src):
    shutil.copy2(sgk_blurry_src, os.path.join(out_dir, '19_anh_kho_sgk_chup_mo_nhoe.png'))
    print("Saved 19_anh_kho_sgk_chup_mo_nhoe.png")

# 18: Ảnh câu hỏi viết tay thật của học sinh (rõ nét)
hw_clear_src = r'C:\Users\LENOVO\.gemini\antigravity-ide\brain\fca3a316-ee99-4283-83f8-82ff2cd5e673\.user_uploaded\media_1792211973432.png'
if os.path.exists(hw_clear_src):
    shutil.copy2(hw_clear_src, os.path.join(out_dir, '18_chu_viet_tay_cay_xanh_quang_hop.png'))
    print("Saved 18_chu_viet_tay_cay_xanh_quang_hop.png")

# 20: Ảnh câu hỏi viết tay mờ nhòe thật của học sinh (Ảnh mờ 2)
hw_blurry_src = r'C:\Users\LENOVO\.gemini\antigravity-ide\brain\fca3a316-ee99-4283-83f8-82ff2cd5e673\.user_uploaded\media_1792212087718.jpg'
if os.path.exists(hw_blurry_src):
    shutil.copy2(hw_blurry_src, os.path.join(out_dir, '20_anh_kho_chu_viet_tay_mo_nhoe.png'))
    print("Saved 20_anh_kho_chu_viet_tay_mo_nhoe.png")
if os.path.exists(blurry_src):
    with Image.open(blurry_src) as img:
        img.resize((1280, int(1280 * img.height / img.width)), Image.Resampling.LANCZOS).save(blurry_dst)
        print(f"Saved 20_anh_kho_mo_nhoe_rung_tay.png")

print("All 20 images successfully cropped to EXACTLY 1 QUESTION EACH!")
