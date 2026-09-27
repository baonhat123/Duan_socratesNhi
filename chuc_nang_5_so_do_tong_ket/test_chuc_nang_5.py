"""
Unit Tests: test_chuc_nang_5.py
Kiểm thử Chức năng 5 (FR-06, FR-08, FR-09: Sơ đồ Tư duy & Tổng kết Khép phiên)
Đặc tả dự án: Socrates Nhí v3.0

Tiêu chí kiểm thử:
1. FR-06: Sơ đồ tư duy bắt buộc có từ 3 đến 6 nút (3 <= len(nodes) <= 6).
2. FR-06: Tuyệt đối không chứa số đáp án cuối cùng, không vẽ chuỗi tính toán thay học sinh.
3. FR-08: Log tối thiểu ẩn danh, không chứa PII (tên, trường, lớp, SĐT).
4. FR-09: Khung tự đúc kết 3 dòng và đánh giá sao (1 đến 5 sao).
5. Dọn dẹp an toàn tệp ảnh tạm thời.
"""

import unittest
import os
import tempfile
import shutil

from chuc_nang_5_so_do_tong_ket.mindmap_model import (
    MindmapNodeType,
    MindmapNode,
    MindmapGraph,
    StudentSummary,
    SessionSummary
)
from chuc_nang_5_so_do_tong_ket.mindmap_engine import (
    MindmapBuilder,
    save_anonymous_session_log,
    clean_temp_files
)


class TestChucNang5(unittest.TestCase):

    def setUp(self):
        self.builder = MindmapBuilder()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    # --- 1. KIỂM THỬ SỐ LƯỢNG NÚT SƠ ĐỒ TƯ DUY (FR-06) ---
    def test_mindmap_node_count_between_3_and_6(self):
        """FR-06: Sơ đồ tư duy phải có từ 3 đến 6 nút."""
        graph = self.builder.build_mindmap(
            topic="Vật lý – Tốc độ chuyển động",
            strand_name="Vật lý THCS",
            given_facts=["s = 12 km", "t = 30 phút"],
            core_concepts=["Tốc độ chuyển động"],
            target_variable="Tốc độ v"
        )
        self.assertTrue(graph.is_valid_count, f"Số nút phải từ 3 đến 6, hiện có: {len(graph.nodes)}")
        self.assertGreaterEqual(len(graph.nodes), 3)
        self.assertLessEqual(len(graph.nodes), 6)

    # --- 2. KIỂM THỬ BẢO VỆ CHỐNG RÒ ĐÁP ÁN TRONG SƠ ĐỒ (FR-06) ---
    def test_no_answer_leak_in_mindmap(self):
        """FR-06: Sơ đồ tư duy tuyệt đối không chứa đáp số số học (ví dụ: = 24 km/h)."""
        graph = self.builder.build_mindmap(
            topic="Vật lý – Tốc độ chuyển động",
            strand_name="Vật lý THCS",
            given_facts=["s = 12 km", "t = 30 phút"],
            core_concepts=["Tốc độ chuyển động"],
            target_variable="v = 24 km/h"  # Giả sử có đáp số cố tình lọt vào
        )
        # Bộ sanitizer phải khử đáp số thành dấu hỏi chấm
        for node in graph.nodes:
            self.assertNotIn("= 24 km/h", node.subtitle)
            self.assertNotIn("= 24 km/h", node.title)

    # --- 3. KIỂM THỬ KHUNG TỰ ĐÚC KẾT HỌC SINH (FR-09) ---
    def test_student_self_summary(self):
        """FR-09: Khung học sinh tự đúc kết 3 dòng."""
        summary = StudentSummary(
            rule_learned="v = s / t",
            pitfall_avoided="quên đổi 30 phút = 0.5 h",
            next_step="thay s và t vào công thức để tính"
        )
        self.assertTrue(summary.is_filled)
        data = summary.to_dict()
        self.assertIn("rule_learned", data)
        self.assertIn("pitfall_avoided", data)
        self.assertIn("next_step", data)

    # --- 4. KIỂM THỬ KHẢO SÁT ĐÁNH GIÁ 1-5 SAO (FR-09) ---
    def test_survey_rating_bounds(self):
        """FR-09: Đánh giá phải nằm trong khoảng 1 đến 5 sao."""
        session = SessionSummary(rating_stars=5)
        self.assertGreaterEqual(session.rating_stars, 1)
        self.assertLessEqual(session.rating_stars, 5)

    # --- 5. KIỂM THỬ NHẬT KÝ ẨN DANH KHÔNG LƯU PII (FR-08) ---
    def test_anonymous_log_pii_safety(self):
        """FR-08: Nhật ký tối thiểu ẩn danh, không lưu bất kỳ thông tin cá nhân nào."""
        session = SessionSummary(
            problem_text="Một người đi xe đạp s = 12 km...",
            topic="Vật lý – Chuyển động",
            total_turns=5,
            rating_stars=5
        )
        log_data = session.to_anonymous_log()
        self.assertIn("session_id", log_data)
        self.assertIn("topic", log_data)
        self.assertIn("total_turns", log_data)
        self.assertIn("rating_stars", log_data)
        self.assertTrue(log_data.get("pii_protected"))

        # Kiểm tra không có trường PII
        for forbidden in ["student_name", "user_name", "school", "class", "phone", "email"]:
            self.assertNotIn(forbidden, log_data)

    def test_save_anonymous_log_file(self):
        """FR-08: Ghi nhật ký ẩn danh ra file JSON thành công."""
        session = SessionSummary(topic="Hóa học 7")
        saved_file = save_anonymous_session_log(session, log_dir=self.test_dir)
        self.assertTrue(os.path.exists(saved_file))
        self.assertTrue(saved_file.endswith(".json"))

    # --- 6. KIỂM THỬ DỌN DẸP ẢNH TẠM (FR-09 & Mục 17) ---
    def test_clean_temp_files(self):
        """Mục 17: Dọn dẹp tệp ảnh tạm thời an toàn."""
        temp_img = os.path.join(self.test_dir, "temp_problem_123.jpg")
        with open(temp_img, "w") as f:
            f.write("dummy image data")
        
        self.assertTrue(os.path.exists(temp_img))
        res = clean_temp_files(temp_img)
        self.assertTrue(res)
        self.assertFalse(os.path.exists(temp_img))


if __name__ == "__main__":
    unittest.main(verbosity=2)
