# CHỨC NĂNG 3: PHÂN LOẠI KIẾN THỨC BÀI TOÁN & BẢN ĐỒ KHÁI NIỆM (FR-03)
> **Dự án:** Socrates Nhí v3.0 — Trợ lý AI gợi mở tư duy và hướng dẫn tự học KHTN THCS  
> **Cuộc thi:** Sáng tạo trẻ Quốc gia trong lĩnh vực Trí tuệ nhân tạo năm 2026 — Bảng A (THCS)  
> **Trạng thái:** ✅ Đã hoàn thành & Kiểm thử đạt 100% tiêu chí chấp nhận  

---

## 1. Mục tiêu và Tiêu chí chấp nhận (FR-03)
Theo mục 6 và mục 9 của tài liệu đặc tả `Spec-Socrates-Nhi-v3.docx`:
- **Phân loại 3 Mạch kiến thức KHTN 7**:
  1. *Cơ học / Đại lượng vật lý* (Tốc độ, lực, khối lượng, trọng lượng, đơn vị đo).
  2. *Biến đổi chất / Phản ứng hóa học* (Hiện tượng vật lý - hóa học, bảo toàn khối lượng, phương trình chữ).
  3. *Cơ thể sống / Môi trường* (Quang hợp, hô hấp tế bào, trao đổi chất).
- **Ràng buộc sư phạm cốt lõi**:
  - AI chỉ được lựa chọn **TỐI ĐA 3 khái niệm cốt lõi** (`core_concepts`).
  - Toàn bộ khái niệm **bắt buộc chọn từ Bản đồ khái niệm do đội biên soạn (`concept_bank.py`), tuyệt đối không tự bịa**.
- **Khai phá dữ kiện bài toán**:
  - Tự động bóc tách các dữ kiện đã cho (`given_facts`: ví dụ $s = 12\text{ km}$, $t = 30\text{ phút}$).
  - Xác định đại lượng mục tiêu cần tìm (`target_variable`: ví dụ $v = ?\text{ km/h}$).
- **Ước lượng cấp độ nhận thức**: Cơ bản, Thông hiểu, Vận dụng.
- **Tuân thủ JSON Schema**: Đúng schema chuẩn tại mục 9 của đặc tả.

---

## 2. Cấu trúc thư mục `chuc_nang_3_phan_loai_kien_thuc`
```
chuc_nang_3_phan_loai_kien_thuc/
│
├── __init__.py               # Xuất khẩu các lớp và enum chính
├── classifier_model.py       # Data model (ClassificationResult, KnowledgeStrand, DifficultyLevel)
├── concept_bank.py           # Bản đồ khái niệm chính thức chuẩn SGK KHTN 7 do đội biên soạn
├── classifier_engine.py      # Bộ máy phân loại kiến thức (OpenAI JSON hoặc Bản đồ nội bộ)
├── classifier_view.py        # Giao diện trực quan hóa Bản đồ khái niệm & Thẻ lỗi thường gặp
├── test_chuc_nang_3.py       # Bộ 8 Unit Tests tự động kiểm thử toàn diện
├── run_chuc_nang_3.py        # Script chạy ứng dụng Phân loại kiến thức độc lập
└── README.md                 # Tài liệu thuyết minh chi tiết chức năng
```

---

## 3. Hướng dẫn chạy và nghiệm thu

### A. Chạy kiểm thử tự động (Unit Tests)
Chạy lệnh sau tại thư mục gốc workspace:
```bash
python -m unittest chuc_nang_3_phan_loai_kien_thuc/test_chuc_nang_3.py
```
**Kết quả kiểm thử:**
- `Ran 8 tests in 0.001s - OK`
- Bao phủ: Phân loại 3 mạch kiến thức, ràng buộc tối đa 3 khái niệm, chọn từ bản đồ chuẩn, bóc tách dữ kiện, ước lượng cấp độ, chuẩn hóa JSON schema.

### B. Chạy ứng dụng giao diện Flet Desktop (Standalone Runner)
Chạy lệnh sau để mở giao diện kiểm thử trực tiếp:
```powershell
python chuc_nang_3_phan_loai_kien_thuc/run_chuc_nang_3.py
```
