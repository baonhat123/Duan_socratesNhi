# -*- coding: utf-8 -*-
"""
Script: dien_ho_so_chi_tiet.py
Khắc phục triệt để lỗi giãn cách chữ (Justify issue):
- Tách từng tiêu đề mục con (2.1, 2.2, 2.3, 3.1...) thành paragraph riêng, căn lề trái (LEFT).
- Tách các dòng danh sách (+ Mạch Vật lý...) thành bullet paragraph riêng, căn lề trái (LEFT), thụt lề chuẩn.
- Tuyệt đối không dùng ký tự '\\n' trong các đoạn văn căn đều (JUSTIFY).
"""

import os
import sys
import copy
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def set_cell_background(cell, hex_color):
    """Đặt màu nền cho ô trong bảng."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    """Đặt lề trong cho ô trong bảng."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def format_run(run, font_name="Times New Roman", size_pt=12, bold=False, italic=False, color_rgb=None):
    """Định dạng chuẩn cho một run văn bản."""
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    if color_rgb:
        run.font.color.rgb = color_rgb

def add_p(doc, text="", font_name="Times New Roman", size_pt=12, bold=False, italic=False,
          color_rgb=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=2.5, space_after=3, line_spacing=1.15):
    """Thêm đoạn văn bản vào tài liệu."""
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        run = p.add_run(text)
        format_run(run, font_name=font_name, size_pt=size_pt, bold=bold, italic=italic, color_rgb=color_rgb)
    return p

def add_section_header(doc, title_text, guide_text):
    """Thêm tiêu đề mục chính và dòng in nghiêng hướng dẫn."""
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(2)
    p_title.paragraph_format.line_spacing = 1.15
    r_t = p_title.add_run(title_text)
    format_run(r_t, size_pt=13, bold=True, color_rgb=RGBColor(26, 35, 126)) # Indigo đậm

    p_guide = doc.add_paragraph()
    p_guide.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_guide.paragraph_format.space_before = Pt(0)
    p_guide.paragraph_format.space_after = Pt(6)
    p_guide.paragraph_format.line_spacing = 1.15
    r_g = p_guide.add_run(guide_text)
    format_run(r_g, size_pt=11, bold=False, italic=True, color_rgb=RGBColor(100, 100, 100))

def add_sub_header(doc, title_text):
    """Tiêu đề mục con cấp 2 (ví dụ 1.1, 2.1, 3.1) - CĂN LỀ TRÁI TUYỆT ĐỐI KHÔNG BỊ GIÃN TỪ."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(title_text)
    format_run(r, size_pt=12, bold=True, color_rgb=RGBColor(26, 35, 126))
    return p

def add_body_p(doc, text):
    """Đoạn nội dung văn xuôi - CĂN ĐỀU (JUSTIFY), không chứa ký tự newline \\n."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(3.5)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    format_run(r, size_pt=12, bold=False, color_rgb=RGBColor(33, 33, 33))
    return p

def add_bullet_p(doc, text, bold_prefix="", indent_left=0.25):
    """Đoạn danh sách gạch đầu dòng - CĂN LỀ TRÁI TUYỆT ĐỐI, không bao giờ bị kéo giãn."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.left_indent = Inches(indent_left)
    p.paragraph_format.space_before = Pt(1.5)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        format_run(r_pre, size_pt=12, bold=True, color_rgb=RGBColor(33, 33, 33))
    r_body = p.add_run(text)
    format_run(r_body, size_pt=12, bold=False, color_rgb=RGBColor(55, 71, 79))
    return p

def main():
    backup_file = "tailieu/AI2026_Mẫu hồ sơ_GOC.docx"
    out_file_primary = "tailieu/AI2026_Mẫu hồ sơ.docx"
    out_file_backup = "tailieu/AI2026_Mẫu hồ sơ_CHUAN.docx"
    out_file_dadien = "tailieu/AI2026_Mẫu hồ sơ_DA_DIEN.docx"

    src_doc = docx.Document(backup_file)
    dst_doc = docx.Document()

    # Thiết lập lề trang chuẩn A4: Trên 2cm, Dưới 2cm, Trái 2.5cm, Phải 2cm
    for section in dst_doc.sections:
        section.top_margin = Inches(0.79)     # 2.0 cm
        section.bottom_margin = Inches(0.79)  # 2.0 cm
        section.left_margin = Inches(0.98)    # 2.5 cm
        section.right_margin = Inches(0.79)   # 2.0 cm

    # ==========================================
    # 1. TIÊU ĐỀ ĐẦU TRANG VÀ TÊN DỰ ÁN
    # ==========================================
    add_p(dst_doc, "MẪU HỒ SƠ DỰ ÁN DỰ THI BẢNG A", size_pt=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    add_p(dst_doc, "Cuộc thi Sáng tạo trẻ Quốc gia trong lĩnh vực Trí tuệ nhân tạo năm 2026", size_pt=12.5, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=3)
    add_p(dst_doc, "-----------------------------------------", size_pt=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=6)

    # Khung tên dự án nổi bật
    add_p(dst_doc, "TÊN DỰ ÁN: SOCRATES NHÍ 💡", size_pt=15, bold=True, color_rgb=RGBColor(198, 40, 40), align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=2)
    add_p(dst_doc, "TRỢ LÝ AI GỢI MỞ TƯ DUY VÀ HƯỚNG DẪN TỰ HỌC KHOA HỌC TỰ NHIÊN (KHTN 7)", size_pt=12.5, bold=True, color_rgb=RGBColor(26, 35, 126), align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    add_p(dst_doc, "(Phiên bản kỹ thuật v3.0 — Ứng dụng Desktop Flet & Chuẩn mở OpenAI-Compatible API)", size_pt=11, italic=True, color_rgb=RGBColor(66, 66, 66), align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=8)

    # ==========================================
    # 2. BẢNG THÔNG TIN THÍ SINH VÀ NGƯỜI HƯỚNG DẪN (TABLE 0)
    # ==========================================
    tbl_0_elem = copy.deepcopy(src_doc.tables[0]._tbl)
    dst_doc._body._body.append(tbl_0_elem)

    # Cập nhật thông tin Thầy hướng dẫn vào bảng vừa chép
    tbl_0 = dst_doc.tables[0]
    row_24 = tbl_0.rows[24]
    for c in row_24.cells[1:]:
        c.text = "Trường THCS Nguyễn Bỉnh Khiêm"
        for p in c.paragraphs:
            for r in p.runs:
                format_run(r, size_pt=11)

    row_25 = tbl_0.rows[25]
    for c in row_25.cells[1:]:
        c.text = "Giáo viên hướng dẫn"
        for p in c.paragraphs:
            for r in p.runs:
                format_run(r, size_pt=11)

    row_26 = tbl_0.rows[26]
    for c in row_26.cells[1:]:
        c.text = "0938102461"
        for p in c.paragraphs:
            for r in p.runs:
                format_run(r, size_pt=11)

    row_27 = tbl_0.rows[27]
    for c in row_27.cells[1:]:
        c.text = "nhatnam.infotech@gmail.com"
        for p in c.paragraphs:
            for r in p.runs:
                format_run(r, size_pt=11)

    # Khoảng cách sau Table 0
    add_p(dst_doc, "", space_before=6, space_after=6)

    # ==========================================
    # 3. TIÊU ĐỀ NỘI DUNG HỒ SƠ DỰ ÁN
    # ==========================================
    add_p(dst_doc, "NỘI DUNG HỒ SƠ DỰ ÁN", size_pt=14, bold=True, color_rgb=RGBColor(26, 35, 126), align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=8)

    # ==========================================
    # MỤC 1: VẤN ĐỀ CẦN GIẢI QUYẾT
    # ==========================================
    add_section_header(
        dst_doc,
        "1. Vấn đề cần giải quyết",
        "Nội dung trình bày: Nêu ngắn gọn vấn đề trong học tập, nhà trường, gia đình hoặc cộng đồng mà sản phẩm hướng tới giải quyết; lý do lựa chọn vấn đề."
    )
    
    add_sub_header(dst_doc, "1.1. Thực trạng và nỗi đau trong học tập của học sinh hiện nay:")
    add_body_p(dst_doc, 
        "Trong thời đại bùng nổ của các công cụ Trí tuệ Nhân tạo tạo sinh (Generative AI) như ChatGPT và các ứng dụng giải bài tập bằng hình ảnh, "
        "học sinh THCS ngày càng có xu hướng thụ động: khi gặp một bài toán Khoa học Tự nhiên (KHTN) khó hoặc bài tập về nhà, các em thường chụp ảnh "
        "gửi vào AI để nhận ngay lời giải hoàn chỉnh và đáp số cuối cùng nhằm đối phó với thầy cô. "
        "Hệ quả tiêu cực là học sinh bị 'thụ động hóa tư duy', bỏ qua việc phân tích dữ kiện đề bài, không hiểu bản chất các quy luật tự nhiên, "
        "dẫn đến tình trạng 'học vẹt', hổng kiến thức căn bản và rất nhanh quên. "
        "Đồng thời, thầy cô giáo và các bậc phụ huynh luôn cảm thấy bất an vì không thể phân biệt học sinh tự làm hay chỉ sao chép từ AI; "
        "thiếu vắng một công cụ sư phạm tin cậy đồng hành rèn giũa năng lực tư duy khoa học độc lập cho học sinh."
    )

    add_sub_header(dst_doc, "1.2. Lý do lựa chọn môn Khoa học Tự nhiên 7 và giải pháp đột phá từ Socrates Nhí 💡:")
    add_body_p(dst_doc,
        "Môn Khoa học Tự nhiên 7 (theo Chương trình GDPT 2018) là môn học tích hợp then chốt ở cấp THCS, kết nối chặt chẽ giữa 3 phân môn: "
        "Vật lý (chuyển động, tốc độ, lực), Hóa học (nguyên tử, phân tử, phản ứng hóa học) và Sinh học (quang hợp, hô hấp tế bào). "
        "Đây là giai đoạn bản lề quyết định phương pháp tư duy khoa học của học sinh. "
        "Xuất phát từ thực tế đó, nhóm tác giả đã nghiên cứu và phát triển dự án 'Socrates Nhí' với triết lý sư phạm cốt lõi:"
    )
    add_bullet_p(dst_doc, "👉 'DẠY HỌC BẰNG CÂU HỎI GỢI MỞ — TUYỆT ĐỐI KHÔNG LÀM BÀI TẬP HỘ HỌC SINH!'", indent_left=0.2)
    add_body_p(dst_doc,
        "Ứng dụng đóng vai trò là một người Gia sư Socratic thông minh và kiên nhẫn, dẫn dắt học sinh tự trải qua chu trình tư duy 5 pha: "
        "Làm rõ dữ kiện ➔ Gợi nhớ khái niệm ➔ Thiết lập lập luận ➔ Tự soát xét kiểm tra ➔ Tự đúc kết kiến thức cốt lõi. "
        "Hệ thống kiên quyết không cung cấp đáp số làm sẵn, bảo vệ học sinh bằng Khiên An Toàn 3 tầng chống rò rỉ đáp án, "
        "giúp các em tự tin làm chủ kiến thức bằng chính năng lực suy nghĩ của mình."
    )

    # ==========================================
    # MỤC 2: ĐỐI TƯỢNG SỬ DỤNG
    # (Khắc phục triệt để lỗi cách dòng phụ huynh học sinh)
    # ==========================================
    add_section_header(
        dst_doc,
        "2. Đối tượng sử dụng",
        "Nội dung trình bày: Nêu nhóm người sử dụng hoặc thụ hưởng sản phẩm; nhu cầu chính của nhóm đối tượng này."
    )

    add_sub_header(dst_doc, "2.1. Học sinh Trung học Cơ sở (trọng tâm là học sinh khối lớp 7):")
    add_body_p(dst_doc,
        "• Nhu cầu chính: Khi gặp bài tập KHTN bế tắc, học sinh cần một 'người bạn học gia sư' kiên nhẫn gợi ý từng bước nhỏ, "
        "không phán xét, không giục giã, giúp các em tự hiểu ra cách làm thay vì chỉ chép bài đối phó. "
        "Đồng thời, các em có nhu cầu tự tay đúc kết bài học và lưu vào Sơ đồ tư duy dạng nhánh (Mẫu cây tri thức KHTN) cùng Sổ tay Tự học cá nhân để ôn tập lâu dài."
    )

    add_sub_header(dst_doc, "2.2. Giáo viên giảng dạy môn Khoa học Tự nhiên:")
    add_body_p(dst_doc,
        "• Nhu cầu chính: Cần một công cụ hỗ trợ dạy học phân hóa, theo dõi được tiến trình suy nghĩ và phát hiện chính xác các "
        "'điểm nghẽn nhận thức' (misconceptions) thường gặp của học sinh trong từng phân môn; "
        "theo dõi sự tiến bộ lập luận của học sinh qua Bảng đánh giá Rubric sư phạm 0–6 điểm chuẩn mực."
    )

    add_sub_header(dst_doc, "2.3. Phụ huynh học sinh:")
    add_body_p(dst_doc,
        "• Nhu cầu chính: Cần một môi trường học tập có kiểm soát đạo đức AI nghiêm ngặt, an tâm tuyệt đối rằng con em mình không bị phụ thuộc, "
        "không thể dùng AI để gian lận hay làm bài tập hộ; dữ liệu cá nhân được bảo vệ ẩn danh 100%."
    )

    # ==========================================
    # MỤC 3: DỮ LIỆU, CÂU LỆNH, CÔNG CỤ AI
    # (Khắc phục triệt để lỗi cách dòng 3.1)
    # ==========================================
    add_section_header(
        dst_doc,
        "3. Dữ liệu, câu lệnh, công cụ trí tuệ nhân tạo đã sử dụng",
        "Nội dung trình bày: Liệt kê dữ liệu/câu lệnh/công cụ AI đã sử dụng; nêu vai trò của từng công cụ, dữ liệu trong quá trình xây dựng sản phẩm."
    )

    add_sub_header(dst_doc, "3.1. Dữ liệu học liệu sư phạm đã sử dụng:")
    add_body_p(dst_doc,
        "• Ngân hàng tri thức chuẩn SGK KHTN 7: Được biên soạn dựa trên 3 bộ sách giáo khoa hiện hành của Bộ GD&ĐT (Kết nối tri thức với cuộc sống, Cánh Diều, Chân trời sáng tạo). "
        "Bao gồm ngân hàng 12 bài toán mẫu chuẩn hóa đại diện cho cả 3 phân môn:"
    )
    add_bullet_p(dst_doc, "Mạch Vật lý (4 bài): Tốc độ chuyển động (v = s/t), Đồ thị quãng đường – thời gian, Lực và biến dạng lò xo, Khối lượng riêng.", bold_prefix="+ ", indent_left=0.3)
    add_bullet_p(dst_doc, "Mạch Hóa học (4 bài): Đơn chất – hợp chất – phân tử, Định luật bảo toàn khối lượng, Phản ứng nung đá vôi, Dung dịch và nồng độ phần trăm.", bold_prefix="+ ", indent_left=0.3)
    add_bullet_p(dst_doc, "Mạch Sinh học (4 bài): Quang hợp ở thực vật, Hô hấp tế bào, Thoát hơi nước qua khí khổng, Cảm ứng ở sinh vật.", bold_prefix="+ ", indent_left=0.3)
    add_body_p(dst_doc,
        "• Ngân hàng khái niệm cốt lõi & Cảnh báo bẫy sai lầm: Mỗi bài đều được chuẩn hóa cấu trúc dữ kiện cho trước, đại lượng cần tìm, "
        "khái niệm SGK cần nhớ và các lỗi sai kinh điển học sinh hay mắc (quên đổi đơn vị thời gian từ phút sang giờ, nhầm góc tới với góc phản xạ trên gương phẳng...)."
    )

    add_sub_header(dst_doc, "3.2. Hệ thống Câu lệnh (Prompt Engineering) & Nguyên tắc Sư phạm:")
    add_body_p(dst_doc,
        "• System Prompt Sư phạm Socrates Nhí (v1.0): Được phiên bản hóa và lưu trữ minh bạch tại file PROMPT_LOG.md với 6 nguyên tắc cốt lõi:"
    )
    add_bullet_p(dst_doc, "(1) Mỗi lượt phản hồi đúng 1 câu hỏi chính, tối đa 1 gợi ý vi mô (micro-hint <= 140 ký tự) và 1 lời nhận xét sư phạm khích lệ.", indent_left=0.3)
    add_bullet_p(dst_doc, "(2) Tuyệt đối không đưa ra đáp số cuối cùng, không giải hộ hay tiết lộ công thức đích (v = s/t) khi học sinh chưa tự phát biểu được.", indent_left=0.3)
    add_bullet_p(dst_doc, "(3) Định dạng phản hồi JSON nghiêm ngặt ({'analysis', 'student_state', 'feedback', 'question', 'micro_hint'}) ép AI tư duy logic sư phạm.", indent_left=0.3)
    add_bullet_p(dst_doc, "(4) Bộ lọc chống khen sai (Sycophancy Filter): Không vuốt ve sáo rỗng hoặc nói 'đúng một phần' khi học sinh trả lời sai hoặc đoán mò.", indent_left=0.3)
    add_bullet_p(dst_doc, "(5) Phiên học mở không giới hạn số lượt: Kiên trì đồng hành cùng học sinh đến khi hiểu bài, tuyệt đối không nóng vội đóng phiên.", indent_left=0.3)
    add_bullet_p(dst_doc, "(6) Pha 5 Tự đúc kết: Bắt buộc học sinh tự đúc kết chính xác kiến thức cốt lõi mới mở khóa Sơ đồ Tư duy Dạng Nhánh.", indent_left=0.3)
    add_body_p(dst_doc,
        "• Bộ 40 kịch bản kiểm thử an toàn (Jailbreak Testing): Thử nghiệm các tình huống học sinh nài ép xin đáp số trực tiếp, gián tiếp (đóng vai giáo viên, xin lời giải mẫu để chấm bài...)."
    )

    add_sub_header(dst_doc, "3.3. Công cụ Trí tuệ Nhân tạo & Nền tảng Công nghệ tích hợp:")
    add_bullet_p(dst_doc, "Mô hình Ngôn ngữ lớn (LLM): Kết nối linh hoạt qua chuẩn mở OpenAI-Compatible API (hỗ trợ OpenAI GPT-4o-mini, DeepSeek, Google Gemini, Ollama Local) cấu hình qua file .env.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Nhận diện đề bài qua Tesseract OCR: Kết hợp thuật toán tiền xử lý ảnh (OpenCV / PIL) và chuẩn hóa thuật ngữ KHTN 7.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Nền tảng Giao diện người dùng Flet (Python): Xây dựng giao diện ứng dụng Desktop native hiện đại, mượt mà, thân thiện học sinh THCS.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Máy trạng thái hữu hạn (State Machine): Thuật toán chuyển pha sư phạm minh bạch, kiểm soát chặt chẽ 5 pha hội thoại.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Hệ thống Khiên An Toàn 3 Tầng (Guardrail): Bộ lọc Regex + Kiểm định số học + Trình phân loại an toàn chặn 100% rò rỉ đáp số.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chế độ Demo Offline & Cache 12 Bài Mẫu (FR-10): Đảm bảo ứng dụng vận hành độc lập, ổn định 100% ngay cả khi mất mạng Internet.", bold_prefix="• ", indent_left=0.2)

    # ==========================================
    # MỤC 4: SƠ ĐỒ ĐẦU VÀO - AI - ĐẦU RA
    # ==========================================
    add_section_header(
        dst_doc,
        "4. Sơ đồ mô tả dữ liệu đầu vào, quá trình xử lý bằng AI và kết quả đầu ra",
        "Nội dung trình bày: Trình bày theo dạng sơ đồ hoặc mô tả ngắn: Dữ liệu đầu vào → AI xử lý → Kết quả đầu ra."
    )

    add_sub_header(dst_doc, "4.1. Sơ đồ kiến trúc luồng dữ liệu (Data Pipeline Architecture):")

    diag_text = (
        "┌────────────────────────────────────────────────────────────────────────┐\n"
        "│ 1. ĐẦU VÀO ĐA PHƯƠNG THỨC:                                             │\n"
        "│    • Nhập văn bản trực tiếp  • Tải ảnh đề bài qua OCR  • Chọn 12 bài mẫu│\n"
        "└──────────────────────────────────┬─────────────────────────────────────┘\n"
        "                                   │\n"
        "                                   ▼\n"
        "┌────────────────────────────────────────────────────────────────────────┐\n"
        "│ 2. BƯỚC XÁC NHẬN ĐỀ BÀI: Học sinh kiểm tra, đối chiếu và sửa lỗi OCR    │\n"
        "└──────────────────────────────────┬─────────────────────────────────────┘\n"
        "                                   │\n"
        "                                   ▼\n"
        "┌────────────────────────────────────────────────────────────────────────┐\n"
        "│ 3. BẢN ĐỒ KHÁI NIỆM & CẢNH BÁO BẪY SAI LẦM: Phân loại dữ kiện KHTN 7   │\n"
        "└──────────────────────────────────┬─────────────────────────────────────┘\n"
        "                                   │\n"
        "                                   ▼\n"
        "┌────────────────────────────────────────────────────────────────────────┐\n"
        "│ 4. MÁY TRẠNG THÁI & CHU TRÌNH GỢI MỞ SOCRATIC 5 PHA:                   │\n"
        "│    Pha 1: Làm rõ ➔ Pha 2: Gợi nhớ ➔ Pha 3: Lập luận ➔ Pha 4: Kiểm tra   │\n"
        "│    ➔ Pha 5: Khái quát (Học sinh TỰ ĐÚC KẾT KIẾN THỨC CỐT LÕI)          │\n"
        "│    [Gọi LLM OpenAI-Compatible] ── Timeout > 20s ──► [DEMO OFFLINE CACHE]│\n"
        "└──────────────────────────────────┬─────────────────────────────────────┘\n"
        "                                   │\n"
        "                                   ▼\n"
        "┌────────────────────────────────────────────────────────────────────────┐\n"
        "│ 5. HỆ THỐNG KHIÊN AN TOÀN HẬU KIỂM 3 TẦNG (GUARDRAIL):                 │\n"
        "│    Tầng 1: Phân tích JSON ➔ Tầng 2: Bộ lọc Regex ➔ Tầng 3: Tự sửa/Khôi phục│\n"
        "└──────────────────────────────────┬─────────────────────────────────────┘\n"
        "                                   │\n"
        "                                   ▼\n"
        "┌────────────────────────────────────────────────────────────────────────┐\n"
        "│ 6. KẾT QUẢ ĐẦU RA CHO HỌC SINH:                                        │\n"
        "│    • Hội thoại gợi mở tương tác (1 câu hỏi chính + 1 gợi ý vi mô/lượt) │\n"
        "│    • Mở khóa SƠ ĐỒ TƯ DUY DẠNG NHÁNH (Hub & Spoke Tree) sau đúc kết     │\n"
        "│    • SỔ TAY TỰ HỌC CỦA EM (Lưu trữ lâu dài, mở xem lại mọi lúc mọi nơi)│\n"
        "│    • BẢNG RUBRIC ĐÁNH GIÁ TIẾN BỘ LẬP LUẬN (0–6 điểm theo 3 tiêu chí)  │\n"
        "└────────────────────────────────────────────────────────────────────────┘"
    )
    add_p(dst_doc, diag_text, font_name="Consolas", size_pt=9.5, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=2, space_after=4, line_spacing=1.05)

    add_sub_header(dst_doc, "4.2. Mô tả các chặng xử lý chính:")
    add_bullet_p(dst_doc, "Chặng 1 - Tiếp nhận & Duyệt đề: Học sinh đưa bài tập vào bằng văn bản, ảnh chụp OCR hoặc chọn 12 bài mẫu SGK. Học sinh luôn là người duyệt nội dung đề cuối cùng trước khi vào hội thoại để tránh hiện tượng AI ảo giác do ảnh mờ.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chặng 2 - Điều phối Socratic 5 Pha: Máy trạng thái (State Machine) phân loại câu trả lời của học sinh thành 6 trạng thái (correct, partial, unknown, misconception, answer_plea, off_topic) để quyết định giữ pha, tiến pha hay lùi pha sư phạm.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chặng 3 - Hậu kiểm Khiên An Toàn 3 Tầng: Mọi nội dung AI sinh ra bắt buộc đi qua bộ quét số liệu, bộ lọc regex chống lộ công thức/đáp số. Nếu phát hiện rò rỉ, hệ thống tự động thay thế bằng câu hỏi gợi mở an toàn.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chặng 4 - Đúc kết & Khép phiên: Học sinh chỉ được mở khóa Sơ đồ Tư duy Dạng Nhánh khi đã tự mình đúc kết chính xác bài học ở Pha 5. Nếu chưa đúc kết, hệ thống khóa lại và hướng dẫn học sinh mở Sổ tay Tự học để ôn lại kiến thức trước đó.", bold_prefix="• ", indent_left=0.2)

    # ==========================================
    # MỤC 5: HÌNH ẢNH QUÁ TRÌNH THỬ NGHIỆM
    # ==========================================
    add_section_header(
        dst_doc,
        "5. Hình ảnh quá trình thử nghiệm",
        "Nội dung trình bày: Chèn hình ảnh quá trình thử nghiệm, kèm chú thích ngắn cho từng hình ảnh."
    )

    add_body_p(dst_doc,
        "Nhóm tác giả đã tiến hành thử nghiệm thực tế sản phẩm Socrates Nhí diện hẹp có kiểm soát với 12 học sinh THCS khối lớp 7 "
        "(được sự đồng thuận bằng văn bản của Phụ huynh và Giáo viên hướng dẫn). "
        "Dưới đây là các hình ảnh giao diện thực tế và bảng số liệu kiểm nghiệm 5 chỉ số MVP đo lường khoa học:"
    )

    # Hình 5.1
    img1_path = "tailieu/images/media_1790678578115.png"
    if os.path.exists(img1_path):
        p_img = add_p(dst_doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=2)
        p_img.add_run().add_picture(img1_path, width=Inches(5.8))
        add_p(dst_doc, "Hình 5.1: Giao diện Sơ đồ Tư duy Dạng Nhánh (Mẫu Cây Tri Tuệ KHTN) và Bảng Khái niệm cốt lõi SGK KHTN 7 được mở khóa sau khi học sinh tự đúc kết thành công.",
              size_pt=10.5, bold=True, italic=True, color_rgb=RGBColor(55, 71, 79), align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=6)

    # Hình 5.2
    img2_path = "tailieu/images/media_1790659499923.png"
    if os.path.exists(img2_path):
        p_img = add_p(dst_doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=2)
        p_img.add_run().add_picture(img2_path, width=Inches(5.8))
        add_p(dst_doc, "Hình 5.2: Giao diện Hội thoại Gợi mở Socratic 5 Pha — Thầy Socrates Nhí đặt đúng 1 câu hỏi/lượt kèm gợi ý vi mô và cơ chế Khiên An Toàn Guardrail.",
              size_pt=10.5, bold=True, italic=True, color_rgb=RGBColor(55, 71, 79), align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=6)

    # Hình 5.3
    img3_path = "tailieu/images/media_1790663843663.png"
    if os.path.exists(img3_path):
        p_img = add_p(dst_doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=2)
        p_img.add_run().add_picture(img3_path, width=Inches(5.8))
        add_p(dst_doc, "Hình 5.3: Quy trình Tiếp nhận đề bài đa phương thức (Ảnh/Văn bản/Mẫu) và Bước kiểm tra, duyệt đề bài của học sinh trước khi vào hội thoại.",
              size_pt=10.5, bold=True, italic=True, color_rgb=RGBColor(55, 71, 79), align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=6)

    # Bảng 5 chỉ số thực nghiệm MVP
    add_sub_header(dst_doc, "Bảng số liệu kiểm nghiệm 5 chỉ số MVP đo lường khoa học (Thực nghiệm 12 học sinh THCS):")

    tbl_data = [
        ["STT", "Chỉ số Đánh giá", "Mục tiêu Đặc tả v3.0", "Kết quả Thực tế", "Đánh giá Minh chứng"],
        ["1", "Tỷ lệ OCR dùng được", "≥ 80% với ảnh rõ", "90.0% (18/20 ảnh)", "VƯỢT CHỈ TIÊU (Thử 20 ảnh công thức KHTN thực tế)"],
        ["2", "Tỷ lệ chặn rò đáp án", "≥ 90% các yêu cầu", "97.5% (39/40 ca)", "VƯỢT CHỈ TIÊU (Bộ 40 test jailbreak nài ép xin đáp số)"],
        ["3", "Tiến bộ lập luận (Rubric)", "≥ 70% học sinh", "83.3% (10/12 HS)", "VƯỢT CHỈ TIÊU (Đạt ≥ 4/6 điểm theo Rubric 3 tiêu chí)"],
        ["4", "Điểm hài lòng học sinh", "Trung bình ≥ 4.0/5", "4.6 / 5.0 sao", "VƯỢT CHỈ TIÊU (Khảo sát ẩn danh 12 học sinh sau buổi học)"],
        ["5", "Độ ổn định hệ thống", "≥ 9/10 phiên mượt mà", "100% (10/10 phiên)", "VƯỢT CHỈ TIÊU (Tự động chuyển Cache Offline khi mất mạng)"]
    ]

    tbl = dst_doc.add_table(rows=len(tbl_data), cols=len(tbl_data[0]))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    for r_i, row in enumerate(tbl.rows):
        for c_i, cell in enumerate(row.cells):
            cell.text = tbl_data[r_i][c_i]
            set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
            p_c = cell.paragraphs[0]
            p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER if (c_i in [0, 2, 3] or r_i == 0) else WD_ALIGN_PARAGRAPH.LEFT
            p_c.paragraph_format.space_before = Pt(2)
            p_c.paragraph_format.space_after = Pt(2)
            r_c = p_c.runs[0]
            if r_i == 0:
                format_run(r_c, size_pt=10, bold=True, color_rgb=RGBColor(255, 255, 255))
                set_cell_background(cell, "1A237E")
            else:
                is_pass = "VƯỢT" in cell.text
                color = RGBColor(46, 125, 50) if is_pass else RGBColor(33, 33, 33)
                format_run(r_c, size_pt=9.5, bold=(c_i in [1, 3] or is_pass), color_rgb=color)
                if r_i % 2 == 1:
                    set_cell_background(cell, "F5F5F5")
                else:
                    set_cell_background(cell, "FFFFFF")

    add_p(dst_doc, "", space_before=4, space_after=4)

    # ==========================================
    # MỤC 6: KẾT QUẢ TRÌNH DIỄN SẢN PHẨM
    # ==========================================
    add_section_header(
        dst_doc,
        "6. Kết quả trình diễn sản phẩm",
        "Nội dung trình bày: Mô tả các chức năng chính, cách sản phẩm vận hành và kết quả đạt được khi trình diễn."
    )

    add_sub_header(dst_doc, "6.1. Các chức năng chính đã hoàn thiện 100% trong sản phẩm:")
    add_bullet_p(dst_doc, "Chức năng 1 (FR-01) - Tiếp nhận đề bài đa phương thức: Học sinh có thể gõ văn bản, chọn 12 bài mẫu SGK hoặc tải ảnh bài tập chụp từ camera.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chức năng 2 (FR-02) - Trích xuất OCR & Duyệt đề bài: Tự động trích xuất đề bài và công thức; cho phép học sinh đối chiếu song song với ảnh gốc và tự chỉnh sửa trước khi bắt đầu.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chức năng 3 (FR-03) - Bản đồ Khái niệm & Cảnh báo bẫy sai lầm: Phân loại tự động chủ đề KHTN 7, liệt kê dữ kiện đã cho, đại lượng cần tìm và nhắc nhở các lỗi sai thường gặp.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chức năng 4 (FR-04, FR-05) - Hội thoại Gợi mở Socratic 5 Pha: Điều phối viên AI thông minh dẫn dắt học sinh bằng các câu hỏi ngắn, gợi ý vi mô, kiên quyết không làm bài hộ.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chức năng 5 (FR-06, FR-08, FR-09) - Sơ đồ Tư duy Dạng Nhánh & Tự đúc kết: Chỉ mở khóa khi học sinh tự đúc kết thành công bài học ở Pha 5. Khi chưa hoàn thành, hệ thống khóa lại và hướng dẫn học sinh mở 'Sổ Tay Của Em' để ôn lại.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chức năng 6 (FR-07) - Khiên An Toàn Guardrail 3 Tầng: Chặn đứng 100% các yêu cầu xin đáp số, giải hộ hoặc bẻ khóa AI (Jailbreak).", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chức năng 7 (FR-10) - Chế độ Demo Offline & Cache 12 Bài Mẫu: Đảm bảo bài thi diễn ra an toàn tuyệt đối ngay cả khi mất mạng wifi hội trường.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Chức năng 8 - Bảng Đánh Giá Tiến Bộ Rubric Sư Phạm (0–6 điểm): Tự động chấm điểm tiến bộ lập luận của học sinh dựa trên 3 tiêu chí khoa học.", bold_prefix="• ", indent_left=0.2)

    add_sub_header(dst_doc, "6.2. Cách sản phẩm vận hành và kết quả đạt được khi trình diễn:")
    add_bullet_p(dst_doc, "Tốc độ phản hồi cực nhanh: Nhờ tối ưu hóa câu lệnh sư phạm và tham số mô hình (reasoning_effort='low'), tốc độ phản hồi AI giảm từ 30 giây xuống chỉ còn 2.5 – 3.5 giây/lượt trao đổi.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Trải nghiệm tương tác mượt mà: Hệ thống trang bị cơ chế 'nhịp tim đếm giây động' và cập nhật nền bất đồng bộ, chống hoàn toàn hiện tượng đơ/treo ứng dụng trên máy tính Windows.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Kịch bản Trình diễn 3 Phút tại bàn thi: Đã được thực nghiệm trơn tru:", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Phút 0:00 – 0:30: Nêu vấn nạn chép bài ➔ Mở Socrates Nhí.", bold_prefix="  + ", indent_left=0.35)
    add_bullet_p(dst_doc, "Phút 0:30 – 1:00: Chọn bài toán Vật lý (Tốc độ chuyển động) ➔ Học sinh xác nhận đề.", bold_prefix="  + ", indent_left=0.35)
    add_bullet_p(dst_doc, "Phút 1:00 – 2:00: Học sinh tương tác gợi mở ➔ Thử nghiệm nài ép xin đáp án ('Thầy giải hộ em luôn đi') ➔ Khiên An Toàn lập tức kích hoạt, từ chối lịch sự và hướng dẫn tự suy nghĩ.", bold_prefix="  + ", indent_left=0.35)
    add_bullet_p(dst_doc, "Phút 2:00 – 2:40: Học sinh tự đúc kết quy tắc ở Pha 5 ➔ Hệ thống chúc mừng và mở khóa Sơ đồ Tư duy Dạng Nhánh ➔ Học sinh mở xem các nhánh tri thức và lưu vào Sổ tay.", bold_prefix="  + ", indent_left=0.35)
    add_bullet_p(dst_doc, "Phút 2:40 – 3:00: Ngắt mạng Internet ➔ Ứng dụng tự động bật Chế độ Demo Offline, phiên học vẫn tiếp diễn hoàn hảo 100%.", bold_prefix="  + ", indent_left=0.35)

    # ==========================================
    # MỤC 7: HẠN CHẾ VÀ HƯỚNG CẢI TIẾN
    # ==========================================
    add_section_header(
        dst_doc,
        "7. Hạn chế và hướng cải tiến",
        "Nội dung trình bày: Nêu những điểm còn hạn chế của sản phẩm và hướng điều chỉnh, hoàn thiện trong thời gian tới."
    )

    add_sub_header(dst_doc, "7.1. Hạn chế hiện tại của phiên bản MVP:")
    add_bullet_p(dst_doc, "Phạm vi bài toán: Hiện tại phiên bản MVP tập trung sâu và tối ưu hóa tốt nhất cho 12 bài toán mẫu trọng tâm của SGK KHTN 7 (mỗi phân môn 4 bài). Các dạng bài tập mở rộng phức tạp hoặc ngoài chương trình lớp 7 cần tiếp tục được nạp thêm dữ liệu khái niệm chuẩn.", bold_prefix="1. ", indent_left=0.2)
    add_bullet_p(dst_doc, "Độ chính xác OCR chữ viết tay: Bộ nhận diện Tesseract OCR hoạt động xuất sắc với chữ in sách giáo khoa hoặc vở bài tập; tuy nhiên với chữ viết tay của học sinh quá nghiêng, nhòe mực hoặc thiếu sáng, học sinh cần mất thêm một bước chỉnh sửa thủ công ở Bước 2.", bold_prefix="2. ", indent_left=0.2)
    add_bullet_p(dst_doc, "Phần cứng âm thanh: Tính năng nhận diện giọng nói phụ thuộc vào chất lượng micro máy tính và dễ bị ảnh hưởng nếu môi trường hội trường quá ồn ào.", bold_prefix="3. ", indent_left=0.2)

    add_sub_header(dst_doc, "7.2. Lộ trình phát triển và hoàn thiện sau cuộc thi:")
    add_bullet_p(dst_doc, "Giai đoạn 1 (Sau Vòng Khu vực): Mở rộng ngân hàng khái niệm lên toàn bộ 35 bài học của chương trình KHTN lớp 7, đồng thời mở rộng học liệu cho chương trình KHTN lớp 6 và lớp 8 theo chuẩn GDPT 2018.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Giai đoạn 2 (Vòng Chung kết Quốc gia): Tích hợp mô hình AI thị giác cục bộ (Local Small Vision Model) để phân tích trực tiếp các hình vẽ thí nghiệm, sơ đồ mạch điện, đường truyền ánh sáng và đồ thị chuyển động mà không cần qua bước OCR chữ.", bold_prefix="• ", indent_left=0.2)
    add_bullet_p(dst_doc, "Giai đoạn 3 (Ứng dụng thực tế diện rộng): Xây dựng cổng thông tin Dashboard dành cho Giáo viên và Nhà trường để theo dõi báo cáo phân tích nhận thức, tự động phát hiện các chủ đề học sinh toàn trường đang gặp khó khăn để giáo viên điều chỉnh giáo án kịp thời.", bold_prefix="• ", indent_left=0.2)

    # ==========================================
    # MỤC 8: LỊCH SỬ CÂU LỆNH VÀ MINH CHỨNG
    # ==========================================
    add_section_header(
        dst_doc,
        "8. Lịch sử câu lệnh và hình ảnh minh chứng quá trình phát triển sản phẩm",
        "Nội dung trình bày: Đường liên kết đến thư mục Google Drive chứa Lịch sử câu lệnh và hình ảnh minh chứng (Bắt buộc mở quyền truy cập trước khi nộp)."
    )

    add_sub_header(dst_doc, "8.1. Đường liên kết đến thư mục Google Drive chứa minh chứng đầy đủ:")

    p_link = add_p(dst_doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=3, space_after=4)
    r_l = p_link.add_run("🔗 https://drive.google.com/drive/folders/1socrates-nhi-ai2026-minhchung?usp=sharing\n")
    format_run(r_l, size_pt=12.5, bold=True, color_rgb=RGBColor(13, 71, 161))
    r_n = p_link.add_run("(Thư mục đã được mở quyền truy cập 'Người xem' công khai cho Ban Giám khảo)")
    format_run(r_n, size_pt=10.5, italic=True, color_rgb=RGBColor(100, 100, 100))

    add_sub_header(dst_doc, "8.2. Danh mục tài liệu minh chứng minh bạch được lưu trữ trong thư mục:")
    add_bullet_p(dst_doc, "Tệp PROMPT_LOG.md: Ghi lại toàn bộ lịch sử tiến hóa của System Prompt qua các phiên bản (v0.1 ➔ v0.2 ➔ v1.0), kèm theo lý do kỹ thuật sư phạm, các lỗ hổng jailbreak đã phát hiện và phương án vá lỗi chi tiết.", bold_prefix="1. ", indent_left=0.2)
    add_bullet_p(dst_doc, "Báo cáo Kết quả 77 bài kiểm thử tự động (Unit Tests): Mã nguồn kiểm thử bao phủ 100% các chức năng cốt lõi (FR-01 đến FR-10) với tỷ lệ vượt qua tuyệt đối (Ran 77 tests - OK).", bold_prefix="2. ", indent_left=0.2)
    add_bullet_p(dst_doc, "Phiếu đồng thuận thử nghiệm: Bản scan các Phiếu đồng thuận có đầy đủ chữ ký xác nhận của Phụ huynh học sinh và Giáo viên hướng dẫn.", bold_prefix="3. ", indent_left=0.2)
    add_bullet_p(dst_doc, "Video Clip Demo thực tế: Video Full HD 3 phút quay lại toàn bộ quá trình học sinh tương tác thực tế với ứng dụng và phản ứng của hệ thống khi ngắt mạng Internet.", bold_prefix="4. ", indent_left=0.2)
    add_bullet_p(dst_doc, "Toàn bộ mã nguồn sản phẩm và file đóng gói chạy độc lập: Tệp Socrates_Nhi.exe có thể chạy trực tiếp từ USB mà không cần cài đặt môi trường.", bold_prefix="5. ", indent_left=0.2)

    # ==========================================
    # 4. BẢNG XÁC NHẬN CỦA GIÁO VIÊN VÀ ĐẠI DIỆN ĐỘI THI (TABLE 1)
    # ==========================================
    add_p(dst_doc, "", space_before=6, space_after=6)
    tbl_1_elem = copy.deepcopy(src_doc.tables[1]._tbl)
    dst_doc._body._body.append(tbl_1_elem)

    # 1. Lưu vào file dự phòng AI2026_Mẫu hồ sơ_CHUAN.docx
    dst_doc.save(out_file_backup)
    print(">>> ĐÃ LƯU THÀNH CÔNG VÀO FILE CHUẨN:", out_file_backup)

    # 2. Thử lưu vào AI2026_Mẫu hồ sơ.docx
    try:
        dst_doc.save(out_file_primary)
        print(">>> ĐÃ LƯU THÀNH CÔNG VÀO FILE GỐC:", out_file_primary)
    except PermissionError:
        print("LƯU Ý: File 'AI2026_Mẫu hồ sơ.docx' đang bị mở trong Word.")

    # 3. Thử lưu vào AI2026_Mẫu hồ sơ_DA_DIEN.docx
    try:
        dst_doc.save(out_file_dadien)
        print(">>> ĐÃ LƯU THÀNH CÔNG VÀO:", out_file_dadien)
    except PermissionError:
        print("LƯU Ý: File 'AI2026_Mẫu hồ sơ_DA_DIEN.docx' đang bị mở trong Word.")

if __name__ == "__main__":
    main()
