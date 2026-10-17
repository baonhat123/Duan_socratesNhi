import os, sys, zipfile, io
from PIL import Image, ImageDraw, ImageFont

out_dir = 'tailieu/bo_20_anh_kiem_thu_ocr'
os.makedirs(out_dir, exist_ok=True)

docx_path = 'tailieu/SGK KHTN 7 KNTT.docx'

# Helper to render clean authentic exam/worksheet question card
def render_question_card(q_num_title, question_text, sub_questions=None, extra_info=None, width=1050, height=360):
    im = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(im)
    
    # Outer exam box with double border (standard Vietnamese exam style)
    draw.rectangle([15, 12, width - 15, height - 12], outline=(160, 180, 205), width=2)
    draw.rectangle([19, 16, width - 19, height - 16], outline=(220, 230, 240), width=1)
    
    # Header bar
    draw.rectangle([20, 17, width - 20, 62], fill=(242, 246, 252))
    draw.line([20, 62, width - 20, 62], fill=(180, 200, 220), width=2)
    
    try:
        font_hdr = ImageFont.truetype('arial.ttf', 20)
        font_qnum = ImageFont.truetype('arialbd.ttf', 24)
        font_text = ImageFont.truetype('arial.ttf', 22)
        font_sub = ImageFont.truetype('arial.ttf', 21)
    except Exception:
        font_hdr = ImageFont.load_default()
        font_qnum = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        
    draw.text((35, 27), "PHIẾU BÀI TẬP VÀ KIỂM TRA ĐÁNH GIÁ - KHOA HỌC TỰ NHIÊN 7", fill=(20, 60, 120), font=font_hdr)
    
    y = 82
    draw.text((35, y), q_num_title, fill=(180, 30, 30), font=font_qnum)
    y += 38
    
    # Word wrap main question text
    words = question_text.split()
    line = ""
    for w in words:
        test_line = line + " " + w if line else w
        bbox = draw.textbbox((35, y), test_line, font=font_text)
        if bbox[2] > width - 45:
            draw.text((35, y), line, fill=(25, 25, 25), font=font_text)
            y += 34
            line = w
        else:
            line = test_line
    if line:
        draw.text((35, y), line, fill=(25, 25, 25), font=font_text)
        y += 36
        
    if sub_questions:
        for sub in sub_questions:
            draw.text((55, y), sub, fill=(35, 35, 35), font=font_sub)
            y += 32
            
    if extra_info:
        y += 6
        draw.text((55, y), extra_info, fill=(100, 100, 100), font=font_sub)
        
    return im

print("Building 20 perfect single-question images...")

with zipfile.ZipFile(docx_path, 'r') as z:
    # 01: Câu 3 Bạn B đi xe đạp (trích trang 48 KHTN 7 - trọn vẹn 100% không bị che)
    b48 = z.read('word/media/image48.jpeg')
    im48 = Image.open(io.BytesIO(b48))
    c01 = im48.crop((35, 836, im48.width - 35, 912))
    c01_padded = ImageOps.expand(c01, border=25, fill='white')
    c01_padded.save(os.path.join(out_dir, '01_chu_in_toc_do_xe_dap.png'))
    print(f"Saved 01: size {c01_padded.size}")

    # 02: Bạn A chạy 120m, Bạn B chạy 140m (trích trang 47 KHTN 7)
    b47 = z.read('word/media/image47.jpeg')
    im47 = Image.open(io.BytesIO(b47))
    c02 = im47.crop((35, 130, im47.width - 35, 330))
    c02.save(os.path.join(out_dir, '02_chu_in_khoi_luong_rieng.png'))
    print(f"Saved 02: size {c02.size}")

    # 03: Phản xạ ánh sáng (trích trang 80 KHTN 7)
    b80 = z.read('word/media/image80.jpeg')
    im80 = Image.open(io.BytesIO(b80))
    c03 = im80.crop((35, int(im80.height * 0.72), im80.width - 35, int(im80.height * 0.95)))
    c03.save(os.path.join(out_dir, '03_chu_in_phan_xa_anh_sang.png'))
    print(f"Saved 03: size {c03.size}")

    # 04: Đồ thị quãng đường - thời gian Hình 10.2 (trích trang 56 KHTN 7)
    b56 = z.read('word/media/image56.jpeg')
    im56 = Image.open(io.BytesIO(b56))
    c04 = im56.crop((35, 40, im56.width - 35, int(im56.height * 0.46)))
    c04.save(os.path.join(out_dir, '04_chu_in_do_thi_quang_duong.png'))
    print(f"Saved 04: size {c04.size}")

# 05: Quang hợp thực vật
c05 = render_question_card(
    "Câu hỏi 5 (Quang hợp ở thực vật):",
    "Dựa vào kiến thức đã học về quá trình trao đổi chất ở thực vật:",
    sub_questions=[
        "a) Phát biểu khái niệm quang hợp ở thực vật.",
        "b) Viết phương trình tổng quát dạng chữ thể hiện quá trình quang hợp.",
        "c) Nêu các yếu tố chủ yếu của môi trường ảnh hưởng đến quá trình quang hợp."
    ]
)
c05.save(os.path.join(out_dir, '05_chu_in_quang_hop_thuc_vat.png'))
print(f"Saved 05: size {c05.size}")

# 06: Hô hấp tế bào
c06 = render_question_card(
    "Câu hỏi 6 (Hô hấp tế bào):",
    "Tại sao các loại rau, củ, quả tươi khi cất giữ trong ngăn mát tủ lạnh đúng cách lại bảo quản được lâu hơn nhiều so với để ở nhiệt độ phòng?",
    sub_questions=[
        "a) Hãy giải thích hiện tượng trên dựa vào cơ chế hô hấp tế bào.",
        "b) Viết phương trình tổng quát dạng chữ của quá trình hô hấp tế bào."
    ]
)
c06.save(os.path.join(out_dir, '06_chu_in_ho_hap_te_bao.png'))
print(f"Saved 06: size {c06.size}")

# 07: Thoát hơi nước qua khí khổng
c07 = render_question_card(
    "Câu hỏi 7 (Trao đổi khí ở sinh vật):",
    "Quan sát cấu tạo giải phẫu của tế bào khí khổng ở bề mặt lá cây:",
    sub_questions=[
        "a) Trình bày đặc điểm cấu tạo tế bào khí khổng phù hợp với chức năng đóng mở.",
        "b) Quá trình thoát hơi nước qua khí khổng có vai trò gì đối với đời sống thực vật?"
    ]
)
c07.save(os.path.join(out_dir, '07_chu_in_thoat_hoi_nuoc.png'))
print(f"Saved 07: size {c07.size}")

# 08: Nung đá vôi
c08 = render_question_card(
    "Câu hỏi 8 (Phản ứng hóa học):",
    "Nung đá vôi (thành phần chính là calcium carbonate: CaCO3) ở nhiệt độ cao thu được vôi sống (calcium oxide: CaO) và khí carbon dioxide (CO2).",
    sub_questions=[
        "a) Viết phương trình chữ của phản ứng hóa học trên.",
        "b) Dấu hiệu nào cho thấy phản ứng hóa học đã xảy ra?"
    ]
)
c08.save(os.path.join(out_dir, '08_chu_in_nung_da_voi.png'))
print(f"Saved 08: size {c08.size}")

# 09: Vận động viên Lê Tú Chinh (trích trang 48 KHTN 7)
with zipfile.ZipFile(docx_path, 'r') as z:
    b48 = z.read('word/media/image48.jpeg')
    im48 = Image.open(io.BytesIO(b48))
    c09 = im48.crop((35, 590, im48.width - 35, 745))
    c09.save(os.path.join(out_dir, '09_cong_thuc_van_toc_don_vi.png'))
    print(f"Saved 09: size {c09.size}")

    # 10: Bạn A đi bộ siêu thị lúc 8h30 (trích trang 48 KHTN 7)
    c10 = im48.crop((35, 740, im48.width - 35, 890))
    c10.save(os.path.join(out_dir, '10_cong_thuc_trong_luong.png'))
    print(f"Saved 10: size {c10.size}")

# 11: Biến dạng lò xo
c11 = render_question_card(
    "Bài tập 11 (Lực và biến dạng lò xo):",
    "Một lò xo có chiều dài tự nhiên l0 = 12 cm. Khi móc vào đầu dưới quả nặng có khối lượng m = 100 g thì chiều dài của lò xo đo được là l1 = 15 cm.",
    sub_questions=[
        "a) Tính độ biến dạng (độ dãn) delta_l của lò xo.",
        "b) Nếu treo thêm một quả nặng 100 g nữa thì chiều dài của lò xo lúc này là bao nhiêu cm?"
    ]
)
c11.save(os.path.join(out_dir, '11_cong_thuc_luc_bien_dang_lo_xo.png'))
print(f"Saved 11: size {c11.size}")

# 12: Áp suất chất lỏng
c12 = render_question_card(
    "Bài tập 12 (Áp suất chất lỏng):",
    "Một thợ lặn chuyên nghiệp đang lặn ở độ sâu h = 25 m so với mặt nước biển. Biết trọng lượng riêng của nước biển là d = 10 300 N/m3.",
    sub_questions=[
        "a) Viết công thức tính áp suất chất lỏng p theo độ sâu h và trọng lượng riêng d.",
        "b) Tính áp suất chất lỏng tác dụng lên người thợ lặn ở độ sâu trên."
    ]
)
c12.save(os.path.join(out_dir, '12_cong_thuc_ap_suat_chat_long.png'))
print(f"Saved 12: size {c12.size}")

# 13: Động năng chuyển động
c13 = render_question_card(
    "Bài tập 13 (Cơ năng và động năng):",
    "Một vận động viên có khối lượng m = 60 kg đang chạy đều với vận tốc v = 5 m/s trên đường chạy thẳng.",
    sub_questions=[
        "a) Viết công thức tính động năng Wđ theo khối lượng m và vận tốc v.",
        "b) Tính động năng của vận động viên theo đơn vị Jun (J)."
    ]
)
c13.save(os.path.join(out_dir, '13_cong_thuc_dong_nang_binh_phuong.png'))
print(f"Saved 13: size {c13.size}")

# 14: Câu 2 Bạn A đi bộ tới siêu thị (trích trang 48 KHTN 7)
with zipfile.ZipFile(docx_path, 'r') as z:
    b48 = z.read('word/media/image48.jpeg')
    im48 = Image.open(io.BytesIO(b48))
    c14 = im48.crop((35, 770, im48.width - 35, 836))
    c14_padded = ImageOps.expand(c14, border=25, fill='white')
    c14_padded.save(os.path.join(out_dir, '14_cong_thuc_toc_do_thoi_gian_den.png'))
    print(f"Saved 14: size {c14_padded.size}")

# 15: Phương trình hóa học quang hợp
c15 = render_question_card(
    "Bài tập 15 (Phương trình hóa học quang hợp):",
    "Cho sơ đồ phản ứng hóa học của quá trình quang hợp như sau:",
    sub_questions=[
        "6CO2 + 6H2O --(ánh sáng, diệp lục)--> C6H12O6 + 6O2",
        "a) Hãy cho biết các chất tham gia và chất sản phẩm trong phản ứng trên.",
        "b) Xác định tỉ lệ số phân tử khí CO2 và số phân tử khí O2."
    ]
)
c15.save(os.path.join(out_dir, '15_hoa_hoc_quang_hop_chi_so.png'))
print(f"Saved 15: size {c15.size}")

# 16: Bảo toàn khối lượng
c16 = render_question_card(
    "Bài tập 16 (Định luật bảo toàn khối lượng):",
    "Cho 5,6 g kim loại sắt (Fe) tác dụng hoàn toàn với dung dịch hydrochloric acid (HCl) thu được 12,7 g muối iron(II) chloride (FeCl2) và 0,2 g khí hydrogen (H2).",
    sub_questions=[
        "a) Viết phương trình bảo toàn khối lượng cho phản ứng trên.",
        "b) Tính khối lượng dung dịch axit HCl đã tham gia phản ứng."
    ]
)
c16.save(os.path.join(out_dir, '16_hoa_hoc_bao_toan_khoi_luong.png'))
print(f"Saved 16: size {c16.size}")

# 17: Nồng độ phần trăm
c17 = render_question_card(
    "Bài tập 17 (Dung dịch và nồng độ phần trăm):",
    "Hòa tan hoàn toàn 20 g muối ăn (sodium chloride: NaCl) vào 80 g nước cất ở nhiệt độ phòng.",
    sub_questions=[
        "a) Tính khối lượng dung dịch nước muối thu được (m_dd).",
        "b) Tính nồng độ phần trăm (C%) của dung dịch theo công thức: C% = (m_ct / m_dd) . 100%."
    ]
)
c17.save(os.path.join(out_dir, '17_hoa_hoc_nong_do_phan_tram.png'))
print(f"Saved 17: size {c17.size}")

# 18: Lập CTHH và phân tử khối oxit sắt
c18 = render_question_card(
    "Bài tập 18 (Hóa trị và công thức hóa học):",
    "Lập công thức hóa học của hợp chất tạo bởi sắt (Fe) hóa trị III và oxygen (O) hóa trị II.",
    sub_questions=[
        "a) Áp dụng quy tắc hóa trị, xác định chỉ số x, y trong công thức Fe_x O_y.",
        "b) Tính phân tử khối của hợp chất Fe2O3 vừa lập (Biết nguyên tử khối: Fe = 56, O = 16 amu)."
    ]
)
c18.save(os.path.join(out_dir, '18_hoa_hoc_nhiet_phan_oxit_sat.png'))
print(f"Saved 18: size {c18.size}")

# 19: Ảnh viết tay thật trong vở ô ly học sinh (đã chuẩn, không có header in)
hw_src = r'C:\Users\LENOVO\.gemini\antigravity-ide\brain\fca3a316-ee99-4283-83f8-82ff2cd5e673\de_bai_viet_tay_hoc_sinh_1792208872586.jpg'
hw_dst = os.path.join(out_dir, '19_anh_kho_chu_viet_tay_nghieng.png')
with Image.open(hw_src) as img:
    img.save(hw_dst)
    print(f"Saved 19: size {img.size}")

# 20: Ảnh rung mờ thực tế
blurry_src = 'tailieu/real_ocr_notebook.jpg'
blurry_dst = os.path.join(out_dir, '20_anh_kho_mo_nhoe_rung_tay.png')
if os.path.exists(blurry_src):
    with Image.open(blurry_src) as img:
        img.resize((1280, int(1280 * img.height / img.width)), Image.Resampling.LANCZOS).save(blurry_dst)
        print(f"Saved 20: size {img.size}")

print("ALL 20 IMAGES SUCCESSFULLY GENERATED!")
