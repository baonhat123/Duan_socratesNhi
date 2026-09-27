# CHỨC NĂNG 4: HỘI THOẠI GỢI MỞ THEO STATE MACHINE SOCRATIC 5 PHA (FR-04 & FR-05)
> **Dự án:** Socrates Nhí v3.0 — Trợ lý AI gợi mở tư duy và hướng dẫn tự học KHTN THCS  
> **Cuộc thi:** Sáng tạo trẻ Quốc gia trong lĩnh vực Trí tuệ nhân tạo năm 2026 — Bảng A (THCS)  
> **Trạng thái:** ✅ Đã hoàn thành & Kiểm thử đạt 100% tiêu chí chấp nhận  

---

## 1. Mục tiêu và Tiêu chí chấp nhận (FR-04, FR-05, FR-07)
Theo mục 4, mục 5 và mục 6 của tài liệu đặc tả `Spec-Socrates-Nhi-v3.docx`:
- **Chu trình Socratic 5 pha**:
  1. `clarify` (Làm rõ): Yêu cầu đọc kỹ đề, chỉ ra dữ kiện, đại lượng hoặc đơn vị đã cho.
  2. `recall` (Gợi nhớ): Kích hoạt công thức, định luật, hiện tượng đã học (không nhắc đáp số).
  3. `reason` (Lập luận): Buộc học sinh kết nối dữ kiện với công thức, giải thích vì sao chọn bước này.
  4. `check` (Kiểm tra): Tự đối chiếu đơn vị đo, dấu, điều kiện và tính hợp lý của kết quả.
  5. `generalize` (Khái quát): Chốt phương pháp học, yêu cầu tự tóm tắt quy tắc & lỗi cần tránh.
- **Phân loại 6 kiểu câu trả lời (`student_state`)**:
  - `correct` (Đúng), `partial` (Đúng 1 phần), `unknown` (Không biết/Bí), `misconception` (Nhầm khái niệm), `answer_plea` (Xin đáp án), `off_topic` (Lạc đề).
- **Quy tắc sư phạm cốt lõi (Luật sắt)**:
  - Đúng **1 câu hỏi chính** mỗi lượt (`next_question`), không bao giờ dồn 2 câu hỏi.
  - Tối đa **1 gợi ý vi mô** (`micro_hint` $\le 140$ ký tự).
  - 1 câu phản hồi tích cực/cụ thể (`feedback`).
  - **Chặn nài ép đáp án (`answer_plea`)**: Giữ nguyên pha, tuyệt đối không đưa đáp số, kéo học sinh về câu hỏi nhỏ nhất.
  - **Bộ đếm `unknown` liên tiếp**: Tối đa 2 lần, lần thứ 3 hạ độ khó (lùi 1 pha hoặc chia nhỏ bước) và đặt lại bộ đếm về 0.
  - **Ngưỡng 7 lượt**: Đến lượt thứ 7, hệ thống chuyển thẳng sang pha 5 (`generalize`) để khép phiên.
  - **Kẹt ở pha 3 sau 5 lượt**: Khép sớm bằng tự tóm tắt, không lộ đáp số để "chạy cho xong".
  - **Hậu kiểm Guardrail chống rò đáp án (FR-07)**: Kiểm duyệt và thay bằng câu Fallback an toàn nếu có dấu hiệu rò đáp số.

---

## 2. Cấu trúc thư mục `chuc_nang_4_hoi_thoai_socratic`
```
chuc_nang_4_hoi_thoai_socratic/
│
├── __init__.py           # Xuất khẩu các lớp và enum chính
├── socratic_model.py     # Định nghĩa 5 Pha Socratic, 6 Kiểu câu trả lời, ChatMessage, TurnResponse
├── state_machine.py      # Bộ điều phối ma trận chuyển pha 5x6 và các quy tắc ngưỡng lượt
├── socratic_engine.py    # Bộ máy phân loại câu trả lời, sinh câu hỏi sư phạm, Guardrail
├── socratic_view.py      # Giao diện Chat Flet hiện đại (Pha badge, Turn progress, Micro-hint card)
├── test_chuc_nang_4.py   # Bộ 11 Unit Tests tự động kiểm thử toàn diện
├── run_chuc_nang_4.py    # Script chạy ứng dụng Chat Socratic độc lập
└── README.md             # Tài liệu thuyết minh chi tiết chức năng
```

---

## 3. Hướng dẫn chạy và nghiệm thu

### A. Chạy kiểm thử tự động (Unit Tests)
Chạy lệnh sau tại thư mục gốc workspace:
```bash
python -m unittest chuc_nang_4_hoi_thoai_socratic/test_chuc_nang_4.py
```
**Kết quả kiểm thử:**
- `Ran 11 tests in 0.001s - OK`
- Bao phủ: Ma trận chuyển pha 5 pha, từ chối nài ép đáp án, quy tắc 3 lần unknown hạ độ khó, ngưỡng 7 lượt khép phiên, ngưỡng kẹt pha 3 sau 5 lượt, cấu trúc 1 câu hỏi chính + micro-hint $\le 140$ ký tự, hậu kiểm Guardrail.

### B. Chạy ứng dụng giao diện Flet Desktop (Standalone Runner)
Chạy lệnh sau để mở giao diện kiểm thử trực tiếp:
```powershell
python chuc_nang_4_hoi_thoai_socratic/run_chuc_nang_4.py
```

---

## 4. Tích hợp trong Ứng dụng Toàn diện
Chức năng này được kết nối trực tiếp trong thư mục `app_tich_hop_socrates/`:
- Tiếp nhận đề bài đã chốt từ **Chức năng 2 (FR-02)**.
- Khởi động chu trình gợi mở 5 pha không phát đáp án sẵn.
