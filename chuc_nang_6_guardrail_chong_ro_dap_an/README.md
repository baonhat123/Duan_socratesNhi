# CHỨC NĂNG 6: HỆ THỐNG HẬU KIỂM CHỐNG RÒ ĐÁP ÁN 3 TẦNG & BẢNG ĐIỀU KHIỂN AN TOÀN (FR-07)
**Dự án:** Socrates Nhí v3.0 — Trợ lý AI Tự học Khoa học Tự nhiên THCS  
**Hội thi Tin học Trẻ Toàn quốc 2026 — Bảng A**  
**Quy chuẩn đặc tả kỹ thuật:** Mục 10 (Kiến trúc Hậu kiểm 3 Tầng)

---

## 1. Mục tiêu Sư phạm & Kỹ thuật
Theo tôn chỉ phương pháp Socratic, **Socrates Nhí tuyệt đối không bao giờ làm bài hộ hay tiết lộ đáp số**, bất kể học sinh có cố tình ép buộc hay gài bẫy AI (jailbreak).

Hệ thống hậu kiểm hoạt động hoàn toàn tự động sau khi AI sinh câu trả lời và trước khi hiển thị cho học sinh qua 3 tầng chốt chặn độc lập:

1. **TẦNG 1: Ép Schema & Khóa Đối chiếu Số liệu Bài toán (Numerical Match & Confirmation Guard):**
   - Rà soát toàn bộ con số và đơn vị trong phát ngôn AI, đối chiếu tức thời với danh mục đáp số bị khóa trong Ngân hàng đề KHTN 7.
   - Chặn đứng hành vi AI xác nhận đúng/sai con số học sinh đoán (ví dụ: *"Đúng rồi, em tính ra 24 là chính xác"*).
   - Nếu phát hiện số kèm đơn vị KHTN nhưng chưa xác định -> Gắn nhãn `FLAGGED` và kích hoạt Tầng 2 soi chiếu sâu.

2. **TẦNG 2: Answer-Leak Classifier (Ngữ nghĩa & Chuỗi tính toán):**
   - Nhận diện chuỗi phép tính hoàn chỉnh thay học sinh (ví dụ: `12 / 0.5 = 24`).
   - Nhận diện cấu trúc giải trọn gói (*"Bước 1... Bước 2... Kết quả"*).
   - Gọi LLM thẩm định độc lập thứ hai ở `temperature=0.0` để phán quyết ngữ nghĩa nếu phát hiện nghi vấn.

3. **TẦNG 3: Pattern Filter (Lớp chặn mẫu Regex nhanh):**
   - Bộ lọc biểu thức chính quy siêu tốc chặn đứng các mẫu cố ý giải hộ:
     - *"Đáp án là / của bài là..."*
     - *"Kết quả cuối cùng bằng..."*
     - *"Ta tính được = ..."*
     - *"Hướng dẫn giải chi tiết / bài giải hoàn chỉnh..."*

4. **Cơ chế Fallback An toàn (Mục 10.3):**
   - Khi bất kỳ tầng nào kích hoạt lệnh `BLOCKED`, phát ngôn bị rò rỉ sẽ bị huỷ bỏ ngay lập tức và thay thế bằng một trong 3 câu hỏi gợi mở sư phạm xoay vòng.
   - Gắn nhãn `safety_flags = ["answer_leak"]` vào hồ sơ phiên học.

---

## 2. Cấu trúc Thư mục

```
chuc_nang_6_guardrail_chong_ro_dap_an/
├── __init__.py                # Package exports
├── guardrail_model.py         # Data classes: TierVerdict, TierCheckResult, GuardrailAudit, LOCKED_SAMPLE_ANSWERS
├── guardrail_engine.py        # Logic 3 tầng hậu kiểm: ThreeTierGuardrail, audit_and_sanitize_response
├── guardrail_view.py          # Dashboard Flet thử nghiệm bẻ khóa AI (Jailbreak Sandbox)
├── run_chuc_nang_6.py         # File chạy độc lập cho Ban Giám Khảo kiểm thử
├── test_chuc_nang_6.py        # Bộ unit tests kiểm tra toàn diện 3 tầng & fallback
└── README.md                  # Hướng dẫn chi tiết
```

---

## 3. Hướng dẫn Chạy Kiểm thử

### 3.1. Chạy Unit Tests
```bash
python -m unittest chuc_nang_6_guardrail_chong_ro_dap_an/test_chuc_nang_6.py
```
*(Kết quả: 6/6 tests passed 100%)*

### 3.2. Chạy Giao diện Bảng Điều Khiển Độc Lập
```bash
python chuc_nang_6_guardrail_chong_ro_dap_an/run_chuc_nang_6.py
```
Giao diện bao gồm:
- **Jailbreak Sandbox:** Thử nghiệm gài bẫy AI với 5 mẫu kịch bản định sẵn (tiết lộ đáp án, xác nhận số, chuỗi tính toán, mẫu giải hộ, câu sư phạm chuẩn).
- **Visual 3-Tier Pipeline:** Hiển thị trạng thái chi tiết của từng tầng (VƯỢT QUA, NGHI NGỜ, ĐÃ CHẶN) kèm dấu hiệu vi phạm.
- **Sanitized Output Card:** Phát ngôn an toàn được chuyển cho học sinh sau khi khử rò rỉ.
