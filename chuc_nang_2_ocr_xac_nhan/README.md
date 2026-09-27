# CHỨC NĂNG 2: TRÍCH XUẤT OCR & XÁC NHẬN / BIÊN TẬP ĐỀ BÀI (FR-02)
> **Dự án:** Socrates Nhí v3.0 — Trợ lý AI gợi mở tư duy và hướng dẫn tự học KHTN THCS  
> **Cuộc thi:** Sáng tạo trẻ Quốc gia trong lĩnh vực Trí tuệ nhân tạo năm 2026 — Bảng A (THCS)  
> **Trạng thái:** ✅ Đã hoàn thành & Kiểm thử đạt 100% tiêu chí chấp nhận  

---

## 1. Mục tiêu và Tiêu chí chấp nhận (FR-02)
Theo mục 6 và mục 12 của tài liệu đặc tả `Spec-Socrates-Nhi-v3.docx`:
- **Đánh giá độ sắc nét của ảnh (Blur Detection)**: Tính toán phương sai cạnh (Edge Variance). Nếu ảnh quá mờ/nhòe $\rightarrow$ **từ chối lịch sự và yêu cầu học sinh chụp lại ảnh rõ nét, tuyệt đối không đoán mò đề bài**.
- **Chuẩn hóa công thức KHTN theo quy ước mục 12**:
  - Công thức Hóa học giữ chỉ số dưới Unicode ($H_2O \rightarrow H₂O, CO_2 \rightarrow CO₂, C_6H_{12}O_6 \rightarrow C₆H₁₂O₆, Fe_2O_3 \rightarrow Fe₂O₃$).
  - Mũi tên phản ứng hóa học chuẩn `→`.
  - Lũy thừa Vật lý: $v^2 \rightarrow v², cm^3 \rightarrow cm³, m^2 \rightarrow m²$.
  - Đơn vị đo luôn đi kèm số, cách 1 khoảng trắng ($500\text{ g}, 12\text{ N}, 15\text{ km/h}$).
  - Đơn vị nhiệt độ: $37^\circ\text{C}$.
- **Giao diện đối chiếu trực quan cao cấp (Dual-pane UI)**:
  - Cột trái: Ảnh đề bài gốc kèm huy hiệu đo độ nét ($0 - 100\%$).
  - Cột phải: Ô biên tập trực tiếp từng chỗ sai + Thanh công cụ ký hiệu KHTN nhanh ($H₂O, CO₂, v², km/h, m/s, N, \rightarrow, ^\circ C$) + Khung xem trước công thức trực quan (Live Formula Preview).
- **Nguyên tắc sư phạm**: Bước xác nhận là phao cứu sinh bắt buộc để tránh AI nhận diện sai đề dẫn đến gợi mở sai hướng. Chỉ khi học sinh bấm **"Xác nhận đề bài này"** thì dữ liệu `ConfirmedProblem` mới được chuyển giao cho Chức năng 3 & 4.

---

## 2. Cấu trúc thư mục `chuc_nang_2_ocr_xac_nhan`
```
chuc_nang_2_ocr_xac_nhan/
│
├── __init__.py               # Xuất khẩu các lớp và hàm chính của package
├── ocr_model.py              # Schema dữ liệu OcrResult và ConfirmedProblem
├── formula_normalizer.py     # Bộ xử lý chuẩn hóa ký hiệu công thức KHTN theo quy ước Unicode
├── ocr_engine.py             # Bộ máy OCR (đo độ nét ảnh, Vision API hoặc Offline Fallback)
├── sample_images.py          # Bộ sinh 4 ảnh mẫu theo checklist mục 12 (Vật lý, Hóa học, Ảnh mờ)
├── sample_assets/            # Thư mục chứa các file ảnh bài tập mẫu KHTN
├── ocr_view.py               # Giao diện Flet UI 2 cột cao cấp (Ảnh gốc, Tool ký hiệu, Live Preview)
├── test_chuc_nang_2.py       # Bộ 11 Unit Tests tự động kiểm thử toàn diện
├── run_chuc_nang_2.py        # Script chạy ứng dụng Flet Desktop độc lập
└── README.md                 # Tài liệu thuyết minh chi tiết chức năng
```

---

## 3. Hướng dẫn chạy và nghiệm thu

### A. Chạy kiểm thử tự động (Unit Tests)
Chạy lệnh sau tại thư mục gốc workspace:
```bash
python -m unittest chuc_nang_2_ocr_xac_nhan/test_chuc_nang_2.py
```
**Kết quả kiểm thử:**
- `Ran 11 tests in 0.019s - OK`
- Bao phủ: Chuẩn hóa công thức hóa học, oxit/muối phức tạp, lũy thừa vật lý, quy cách khoảng trắng đơn vị đo, phát hiện ảnh rõ nét vs ảnh mờ, từ chối ảnh mờ không đoán mò, đóng gói `ConfirmedProblem`.

### B. Chạy ứng dụng giao diện Flet Desktop (Standalone Runner)
Chạy lệnh sau để mở giao diện kiểm thử trực tiếp:
```powershell
python chuc_nang_2_ocr_xac_nhan/run_chuc_nang_2.py
```

---

## 4. Chuyển giao sang Chức năng 3 & 4 (FR-03 & FR-04)
Khi học sinh nhấn nút **"Xác nhận đề bài này để bắt đầu học"**, đối tượng `ConfirmedProblem` được tạo ra:
```python
{
    "original_text": "Mot nguoi di xe dap chuyen dong deu tren quang duong s = 12 km trong t = 30 phut...",
    "confirmed_text": "Một người đi xe đạp chuyển động đều trên quãng đường thẳng s = 12 km trong thời gian t = 30 phút. Hãy xác định tốc độ v của người đó theo đơn vị km/h và m/s.",
    "was_edited": True,
    "formulas": ["v = s/t"],
    "units": ["km", "km/h", "m/s", "phút"],
    "source_type": "image",
    "image_path": ".../sample_assets/ocr_co_hoc_toc_do.png",
    "confirmed_at": "2026-09-27T10:35:00"
}
```
Dữ liệu này được chuyển giao trực tiếp cho **Chức năng 3 (FR-03: Phân loại kiến thức bài toán)** và **Chức năng 4 (FR-04: Điều phối hội thoại gợi mở State Machine 5 pha)**.
