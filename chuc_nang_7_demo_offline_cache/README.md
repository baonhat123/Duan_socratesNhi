# CHỨC NĂNG 7: CHẾ ĐỘ DEMO OFFLINE & CACHE 12 BÀI MẪU KHTN 7 ĐỦ 5 PHA SOCRATIC (FR-10)
**Dự án:** Socrates Nhí v3.0 — Trợ lý AI Tự học Khoa học Tự nhiên THCS  
**Hội thi Tin học Trẻ Toàn quốc 2026 — Bảng A**  
**Quy chuẩn đặc tả kỹ thuật:** Mục 18 (Vận hành lúc thi & Ma trận rủi ro) & FR-10

---

## 1. Mục tiêu & Ý nghĩa Vận hành khi đi Thi
Trong các cuộc thi thực tế (Hội đồng Giám khảo chấm trực tiếp), các sự cố mạng thường gặp bao gồm:
- Wifi hội trường nghẽn, mất kết nối Internet đột ngột.
- API OpenAI-compatible bị timeout (> 20 giây) hoặc cạn hạn mức (quota) giữa buổi thuyết trình.
- Học sinh hoặc khách tham quan thao tác bất ngờ làm gián đoạn kịch bản.

**Chức năng 7 (FR-10)** cung cấp giải pháp kỹ thuật kiên cố:
1. **Ngân hàng 12 Bài Mẫu KHTN 7 Chuẩn SGK:**
   - 4 bài Mạch 1: Vật lý THCS (`VL01` Tốc độ xe đạp, `VL02` Quãng đường tàu hỏa, `VL03` Trọng lượng & Khối lượng, `VL04` Lực ma sát).
   - 4 bài Mạch 2: Hóa học THCS (`HH01` Bảo toàn khối lượng đốt than, `HH02` Nung đá vôi, `HH03` Nồng độ phần trăm, `HH04` Hiện tượng vật lý/hóa học).
   - 4 bài Mạch 3: Sinh học THCS (`SH01` Quang hợp ở lá cây, `SH02` Hô hấp tế bào hạt nảy mầm, `SH03` Thoát hơi nước qua khí khổng, `SH04` Cảm ứng hướng sáng).
2. **Bộ Lời Thoại Cache Đủ 5 Pha Socratic (Mục 18.1):**
   - Đủ 5 pha: `Clarify` ➜ `Recall` ➜ `Reason` ➜ `Check` ➜ `Generalize`.
   - Mỗi pha gồm: 1 câu phản hồi khích lệ + đúng 1 câu hỏi dẫn dắt + 1 gợi ý vi mô ($\le 140$ ký tự) + các gợi ý phản hồi nhanh (quick replies).
   - Đã được kiểm duyệt sư phạm và qua kiểm thử Guardrail 3 Tầng: **Tuyệt đối không rò rỉ đáp số**.
3. **Cơ Chế Chuyển Đổi Tự Động (Auto-Failover):**
   - Tự động chuyển cache khi phát hiện cuộc gọi API kéo dài quá 20 giây (`TIMEOUT_THRESHOLD_SECONDS = 20.0`).
   - Hiển thị huy hiệu minh bạch, trung thực với Ban Giám Khảo: `⚡ Đang ở chế độ demo offline`.

---

## 2. Cấu trúc Thư mục

```
chuc_nang_7_demo_offline_cache/
├── __init__.py                # Package exports
├── offline_model.py           # Dataclasses: NetworkMode, KnowledgeStrand, SocraticPhaseDialogue, OfflineSampleProblem
├── offline_bank.py            # Ngân hàng 12 bài mẫu KHTN 7 đủ 5 pha Socratic chuẩn sư phạm
├── offline_engine.py          # Bộ điều phối chuyển đổi mạng, phát hiện timeout > 20s, so khớp đề mẫu
├── offline_view.py            # Bảng điều khiển giao diện Flet (Bộ lọc 3 mạch, xem chi tiết 5 pha, chuyển chế độ)
├── run_chuc_nang_7.py         # File chạy độc lập cho Ban Giám Khảo kiểm thử
├── test_chuc_nang_7.py        # 6 bài kiểm thử toàn diện
└── README.md                  # Tài liệu hướng dẫn
```

---

## 3. Hướng dẫn Chạy Kiểm thử

### 3.1. Chạy Unit Tests
```bash
python -m unittest chuc_nang_7_demo_offline_cache/test_chuc_nang_7.py
```
*(Kết quả: 6/6 tests passed 100%)*

### 3.2. Chạy Giao diện Độc lập
```bash
python chuc_nang_7_demo_offline_cache/run_chuc_nang_7.py
```
