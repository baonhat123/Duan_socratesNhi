# Chức năng 5: Sơ đồ Tư duy & Tổng kết Khép phiên Học tập (FR-06, FR-08, FR-09)

## 1. Giới thiệu tổng quan
Chức năng 5 là trạm đích cuối cùng trong chu trình học tập của **Socrates Nhí v3.0** (Cuộc thi Sáng tạo trẻ Quốc gia AI 2026 - Bảng A). Module này đóng vai trò sư phạm cốt lõi: giúp học sinh THCS xâu chuỗi toàn bộ dữ kiện, khái niệm và phương pháp giải thành một **Sơ đồ Tư duy trực quan**, đồng thời kích hoạt năng lực tự phản tỉnh (metacognition) qua hoạt động **Tự đúc kết 3 dòng** và **Khảo sát đánh giá trải nghiệm 1–5 sao**.

---

## 2. Tiêu chí Chấp nhận Kỹ thuật (Theo Đặc tả v3.0)
1. **FR-06: Sơ đồ tư duy hiển thị (Mindmap Visualization)**:
   - Sơ đồ tư duy dạng đồ thị gồm **từ 3 đến 6 nút** (`3 <= len(nodes) <= 6`).
   - Bao gồm: *Nút Chủ đề* 🏷️ ➜ *Nút Dữ kiện đã cho* 📌 ➜ *Nút Mục tiêu cần tính* 🎯 ➜ *Nút Khái niệm & Công thức chuẩn* 📐 ➜ *Nút Phương pháp kiểm tra* ✅.
   - **Luật sắt**: Tuyệt đối không ghi đáp số cuối cùng, không vẽ chuỗi tính toán thay học sinh.
2. **FR-08: Nhật ký tối thiểu ẩn danh (Anonymous Session Logging)**:
   - Tự động lưu tóm tắt phiên học (`session_id`, `topic`, `total_turns`, `rating_stars`) ra file JSON cục bộ.
   - **Cam kết PII**: Không lưu tên, lớp, trường, số điện thoại hay khuôn mặt học sinh.
3. **FR-09: Khép phiên, Tự đúc kết & Khảo sát 1–5 sao**:
   - Khung tự đúc kết 3 dòng:
     1. Quy tắc / công thức em đã vận dụng.
     2. Bẫy sai lầm cần chú ý tránh.
     3. Bước giải tiếp theo của em.
   - Khảo sát 1–5 sao tương tác kèm nhãn cảm xúc trực quan.
   - Tự động dọn dẹp các tệp ảnh đề bài tạm thời sau khi kết thúc phiên.

---

## 3. Cấu trúc Tệp tin
- `mindmap_model.py`: Định nghĩa lớp `MindmapNode`, `MindmapGraph`, `StudentSummary`, `SessionSummary`.
- `mindmap_engine.py`: Bộ sinh sơ đồ tư duy, bộ lọc khử rò rỉ đáp số `sanitize_no_answer_leak`, lưu log ẩn danh và dọn dẹp ảnh tạm.
- `mindmap_view.py`: Giao diện Flet chuẩn Ed-Tech 2.0 thân thiện với học sinh THCS.
- `test_chuc_nang_5.py`: 7/7 unit test kiểm thử toàn diện các tiêu chí chấp nhận.
- `run_chuc_nang_5.py`: Trình chạy độc lập để demo và chụp minh chứng.

---

## 4. Hướng dẫn Chạy Kiểm thử
```bash
# Chạy bộ test unit tự động:
python -m unittest chuc_nang_5_so_do_tong_ket/test_chuc_nang_5.py

# Chạy giao diện độc lập để xem và chụp ảnh:
python chuc_nang_5_so_do_tong_ket/run_chuc_nang_5.py
```
