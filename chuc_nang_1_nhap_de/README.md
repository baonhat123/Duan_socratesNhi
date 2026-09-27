# CHỨC NĂNG 1: TIẾP NHẬN ĐỀ BÀI (FR-01)
> **Dự án:** Socrates Nhí v3.0 — Trợ lý AI gợi mở tư duy và hướng dẫn tự học KHTN THCS  
> **Cuộc thi:** Sáng tạo trẻ Quốc gia trong lĩnh vực Trí tuệ nhân tạo năm 2026 — Bảng A (THCS)  
> **Trạng thái:** ✅ Đã hoàn thành & Kiểm thử đạt 100% tiêu chí chấp nhận  

---

## 1. Mục tiêu và Tiêu chí chấp nhận (FR-01)
Theo mục 6 của tài liệu đặc tả `Spec-Socrates-Nhi-v3.docx`:
- **Đa dạng hình thức nhập**: Cho phép học sinh gõ đề bài văn bản trực tiếp, chọn nhanh từ ngân hàng đề mẫu KHTN 7 hoặc tải ảnh bài tập chụp từ sách/vở (JPG/PNG).
- **Kiểm soát dung lượng**: Giới hạn tệp ảnh $\le 5\text{ MB}$; hiển thị thông báo lỗi rõ ràng nếu tệp vượt quá 5MB.
- **Kiểm soát định dạng**: Chỉ chấp nhận ảnh `.jpg`, `.jpeg`, `.png` hợp lệ; từ chối và báo lỗi với các định dạng khác hoặc tệp bị hỏng.
- **Bảo vệ riêng tư (PII)**: Tự động cảnh báo học sinh che tên, trường, lớp, số điện thoại trước khi tải lên (theo mục 17.1).
- **Quy tắc sư phạm cốt lõi (Luật sắt)**: **Tuyệt đối KHÔNG gửi ảnh hoặc văn bản sang AI trước khi học sinh chủ động bấm nút "Xác nhận đề bài"** (`is_confirmed = False` cho đến khi xác nhận).

---

## 2. Cấu trúc thư mục `chuc_nang_1_nhap_de`
```
chuc_nang_1_nhap_de/
│
├── __init__.py           # Xuất khẩu các lớp và hàm chính của package
├── input_model.py        # Model ProblemInput và Enum InputType (TEXT, IMAGE, SAMPLE)
├── validator.py          # Bộ kiểm tra kích thước <=5MB, định dạng ảnh, PII và staging file tạm
├── sample_bank.py        # Ngân hàng đề mẫu KHTN 7 chuẩn 3 mạch kiến thức (Cơ học, Hóa học, Sinh học)
├── ui_component.py       # Giao diện Flet UI hoàn chỉnh cho Chức năng 1 (Header, SegmentedButton, Preview, Alert)
├── test_chuc_nang_1.py   # Bộ 10 Unit Tests tự động kiểm thử toàn bộ điều kiện biên
├── run_chuc_nang_1.py    # Script chạy ứng dụng Flet Desktop độc lập để demo/kiểm thử UI
└── README.md             # Tài liệu thuyết minh chi tiết chức năng
```

---

## 3. Hướng dẫn chạy và nghiệm thu

### A. Chạy kiểm thử tự động (Unit Tests)
Chạy lệnh sau tại thư mục gốc workspace:
```bash
python -m unittest chuc_nang_1_nhap_de/test_chuc_nang_1.py
```
**Kết quả kiểm thử:**
- `Ran 10 tests in 0.055s - OK`
- Bao phủ: Kiểm tra văn bản hợp lệ, từ chối văn bản rỗng, kiểm tra ảnh PNG/JPG, từ chối file > 5MB, từ chối file sai đuôi, từ chối file ảnh giả mạo/hỏng, kiểm tra ngân hàng đề mẫu, kiểm tra cờ an toàn `is_confirmed`.

### B. Chạy ứng dụng giao diện Flet Desktop (Standalone Runner)
Chạy lệnh sau để mở giao diện kiểm thử trực tiếp:
```bash
python chuc_nang_1_nhap_de/run_chuc_nang_1.py
```

---

## 4. Chuyển giao sang Chức năng 2 (FR-02)
Khi học sinh nhấn nút **"Xác nhận đề bài này"**, đối tượng `ProblemInput` được hoàn thiện và trả về:
```python
{
    "input_type": "image",                 # hoặc "text" / "sample"
    "file_path": ".../socrates_nhi_uploads/upload_abc_de_bai.png",
    "file_name": "de_bai.png",
    "file_size_bytes": 1302540,
    "file_size_mb": 1.24,
    "is_confirmed": True,                  # Đã xác nhận -> Cho phép chuyển sang OCR & AI
    "safety_warnings": [...],
    "created_at": "2026-09-27T10:10:00"
}
```
Đối tượng này được chuyển giao trực tiếp cho **Chức năng 2 (FR-02: Trích xuất OCR & Xác nhận nội dung công thức KHTN)**.
