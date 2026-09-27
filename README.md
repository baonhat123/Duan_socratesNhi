# SOCRATES NHÍ 💡 (v3.0)
**Trợ lý AI Tự học Khoa học Tự nhiên THCS — Phương pháp Gợi mở Socratic**  
*Dự án tham dự Hội thi Sáng tạo trẻ Quốc gia AI 2026 — Bảng A*

---

## 🌟 Tổng Quan Hệ Thống
Socrates Nhí được xây dựng trên nguyên tắc sư phạm cốt lõi: **Tuyệt đối không giải bài hộ hay cung cấp đáp án sẵn**, mà đồng hành dẫn dắt học sinh tự tư duy và làm chủ kiến thức Khoa học Tự nhiên lớp 7 (3 Mạch: Vật lý, Hóa học, Sinh học) qua phương pháp gợi mở 5 pha Socratic và hệ thống hậu kiểm chống rò đáp số 3 tầng.

---

## 📂 Kiến Trúc Dự Án (8 Module Độc Lập & App Tích Hợp)

1. **[Chức năng 1: Nhập đề bài (FR-01)](file:///c:/Users/hienp/Desktop/Socrates/chuc_nang_1_nhap_de/)**
   - 4 Chế độ tiếp nhận: Gõ văn bản trực tiếp, Tải ảnh bài tập (JPG/PNG $\le$ 5MB), Chọn đề mẫu KHTN 7 (đủ 12 bài chuẩn SGK chia đều 3 mạch kiến thức), Đọc đề qua Giọng nói (Speech-to-Text với bộ chuẩn hóa phát âm thuật ngữ KHTN tiếng Việt sang ký hiệu SGK quốc tế).
   - Runner độc lập: `python chuc_nang_1_nhap_de/run_chuc_nang_1.py`

2. **[Chức năng 2: Trích xuất & Soát công thức OCR (FR-02)](file:///c:/Users/hienp/Desktop/Socrates/chuc_nang_2_ocr_xac_nhan/)**
   - Đo độ nét ảnh (phát hiện ảnh mờ), bảng so sánh đối chiếu hai cột, bộ chuẩn hóa ký hiệu công thức KHTN Unicode ($H_2O, CO_2, km/h, cm^3$).
   - Runner độc lập: `python chuc_nang_2_ocr_xac_nhan/run_chuc_nang_2.py`

3. **[Chức năng 3: Phân loại kiến thức & Bản đồ khái niệm (FR-03)](file:///c:/Users/hienp/Desktop/Socrates/chuc_nang_3_phan_loai_kien_thuc/)**
   - Nhận diện 3 mạch kiến thức KHTN 7 (Vật lý, Hóa học, Sinh học), thẻ Dữ kiện đã cho vs Đại lượng cần tìm, Bản đồ $\le 3$ khái niệm cốt lõi, Khiên cảnh báo lỗi tư duy thường gặp.
   - Runner độc lập: `python chuc_nang_3_phan_loai_kien_thuc/run_chuc_nang_3.py`

4. **[Chức năng 4: Hội thoại Socratic gợi mở 5 pha & State Machine (FR-04, FR-05)](file:///c:/Users/hienp/Desktop/Socrates/chuc_nang_4_hoi_thoai_socratic/)**
   - Máy trạng thái 5 pha (`Clarify` ➜ `Recall` ➜ `Reason` ➜ `Check` ➜ `Generalize`), phân loại 6 trạng thái học sinh, tối đa 7 lượt, đếm số lần bối rối liên tiếp, chip phản hồi nhanh.
   - Runner độc lập: `python chuc_nang_4_hoi_thoai_socratic/run_chuc_nang_4.py`

5. **[Chức năng 5: Sơ đồ Tư duy & Tổng kết Buổi học (FR-06, FR-08, FR-09)](file:///c:/Users/hienp/Desktop/Socrates/chuc_nang_5_so_do_tong_ket/)**
   - Sơ đồ tư duy liên kết logic 3–6 nút (không chứa đáp số), Khung học sinh tự đúc kết 3 dòng, Khảo sát 1–5 sao, Nhật ký tối thiểu ẩn danh (không lưu PII), Dọn dẹp tệp ảnh tạm.
   - Runner độc lập: `python chuc_nang_5_so_do_tong_ket/run_chuc_nang_5.py`

6. **[Chức năng 6: Hậu kiểm Chống rò đáp án 3 tầng & Bảng điều khiển An toàn (FR-07)](file:///c:/Users/hienp/Desktop/Socrates/chuc_nang_6_guardrail_chong_ro_dap_an/)**
   - Tầng 1: Ép schema & Khóa đối chiếu số liệu bài toán.
   - Tầng 2: Answer-leak classifier (nhận diện chuỗi tính toán làm hộ).
   - Tầng 3: Pattern filter (bộ lọc regex câu giải hộ).
   - Fallback an toàn xoay vòng 3 mẫu và gắn nhãn `safety_flags = ["answer_leak"]`.
   - Runner độc lập: `python chuc_nang_6_guardrail_chong_ro_dap_an/run_chuc_nang_6.py`

7. **[Chức năng 7: Chế độ Demo Offline & Cache 12 Bài Mẫu KHTN 7 Đủ 5 Pha (FR-10)](file:///c:/Users/hienp/Desktop/Socrates/chuc_nang_7_demo_offline_cache/)**
   - Ngân hàng 12 bài mẫu KHTN 7 chuẩn SGK chia đều 3 mạch (4 Vật lý, 4 Hóa học, 4 Sinh học) có sẵn lời thoại 5 pha chuẩn sư phạm.
   - Tự động chuyển đổi khi API timeout (> 20s), mất mạng, hoặc bật cưỡng chế khi thi.
   - Runner độc lập: `python chuc_nang_7_demo_offline_cache/run_chuc_nang_7.py`

8. **[Chức năng 8: Rubric Đánh giá Tiến bộ Lập luận (0-6 điểm) & 5 Chỉ số Đo lường Sư phạm (Mục 16.3 & Mục 3)](file:///c:/Users/hienp/Desktop/Socrates/chuc_nang_8_rubric_danh_gia_tien_bo/)**
   - Phiếu chấm Rubric 3 tiêu chí Mục 16.3: Nêu dữ kiện (0-2đ), Nêu khái niệm (0-2đ), Nêu bước tiếp theo (0-2đ). Đạt chuẩn khi $\ge 4/6$ điểm.
   - Bảng 5 Chỉ số Đo lường Khoa học thành công MVP chính thức (Mục 3).
   - Xuất Báo cáo Minh chứng phục vụ Hồ sơ Dự thi Bảng A.
   - Runner độc lập: `python chuc_nang_8_rubric_danh_gia_tien_bo/run_chuc_nang_8.py`

9. **[App Tích Hợp Toàn Diện (Socrates Nhí App)](file:///c:/Users/hienp/Desktop/Socrates/app_tich_hop_socrates/)**
   - Lộ trình 3 bước trực quan: `Bước 1: Đặt câu hỏi` ➜ `Bước 2: Gia sư Socratic` ➜ `Bước 3: Sơ đồ & Đúc kết`.
   - Tích hợp 3 bảng điều khiển chuyên sâu cho Giám khảo: `Khiên An Toàn 3 Tầng 🛡️`, `⚡ Demo Offline (12 Bài) 📚`, và `Đánh Giá Sư Phạm 📊`.
   - Khởi chạy chính thức: `python main.py`

10. **Tài liệu & Hồ sơ Dự thi Bảng A chính thức:**
    - [HO_SO_DU_THI_BANG_A.md](file:///c:/Users/hienp/Desktop/Socrates/tailieu/HO_SO_DU_THI_BANG_A.md): Bản thuyết minh hoàn chỉnh 8 mục theo chuẩn Bảng A Hội thi Sáng tạo trẻ Quốc gia 2026.
    - [BO_CAU_HOI_PHAN_BIEN_VA_KE_HOACH_6_GIO.md](file:///c:/Users/hienp/Desktop/Socrates/tailieu/BO_CAU_HOI_PHAN_BIEN_VA_KE_HOACH_6_GIO.md): Bộ 12 câu hỏi phản biện của Ban Giám khảo, Kế hoạch tác chiến Vòng Khu vực 6 giờ và Checklist đi thi.
    - [PHIEU_DONG_THUAN_THU_NGHIEM.md](file:///c:/Users/hienp/Desktop/Socrates/tailieu/PHIEU_DONG_THUAN_THU_NGHIEM.md): Mẫu phiếu đồng thuận thử nghiệm có kiểm soát cho Phụ huynh và Giáo viên (Mục 17.3).
    - [PROMPT_LOG.md](file:///c:/Users/hienp/Desktop/Socrates/PROMPT_LOG.md): Nhật ký lệnh AI versioned (v0.1 ➜ v0.2 ➜ v1.0), báo cáo kiểm thử 40 test jailbreak, bảng 5 chỉ số đo lường thực nghiệm.
    - [.env.example](file:///c:/Users/hienp/Desktop/Socrates/.env.example): Tệp mẫu cấu hình OpenAI-compatible API an toàn phục vụ nộp hồ sơ.

11. **Công cụ Đóng gói Windows Desktop (.exe):**
    - Chạy tệp đóng gói tự động: `build_windows.bat` hoặc lệnh `python build_desktop.py`.
    - Tạo tệp `dist/Socrates_Nhi/Socrates_Nhi.exe` độc lập để Giám khảo chấm thi mà không cần cài đặt Python.

---

## 🚀 Hướng Dẫn Chạy & Kiểm Thử

### 1. Khởi chạy Ứng dụng Tích hợp Chính
```bash
python main.py
```

### 2. Chạy Toàn Bộ Bộ Test Suite (77/77 Tests Passed 100%)
```bash
python -m unittest discover -s . -p "test_*.py"
```

### 3. Đóng gói Ứng dụng Desktop (.exe)
```bash
build_windows.bat
```

