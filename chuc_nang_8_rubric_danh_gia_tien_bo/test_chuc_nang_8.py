"""
Unit Tests: test_chuc_nang_8.py
Kiểm thử toàn diện Chức năng 8: Rubric Đánh giá Tiến bộ Lập luận (0-6 điểm) & 5 Chỉ số Đo lường Sư phạm
Đặc tả dự án: Socrates Nhí v3.0 (Mục 3 & Mục 16.3)

Kiểm tra các tiêu chí chấp nhận:
1. Đánh giá học sinh đạt điểm tối đa (6/6) và được công nhận 'Đạt tiến bộ lập luận' (is_passed == True).
2. Kiểm tra ngưỡng công nhận chuẩn Mục 16.3: Đạt khi tổng điểm >= 4/6.
3. Kiểm tra ngưỡng chưa đạt khi tổng điểm < 4/6.
4. Tiêu chí 1: Nêu dữ kiện đề bài (2đ - 1đ - 0đ).
5. Tiêu chí 2: Nêu khái niệm cốt lõi (2đ - 1đ - 0đ).
6. Tiêu chí 3: Nêu bước lập luận tiếp theo (2đ - 1đ - 0đ).
7. Chế độ Thẩm định viên / Giáo viên ghi đè điểm số thủ công.
8. Bảng 5 Chỉ số Đo lường Khoa học (Mục 3) đạt chuẩn 100%.
9. Khả năng xuất Báo cáo Minh chứng chuẩn Markdown phục vụ Hồ sơ Dự thi Bảng A.
"""

import unittest
from chuc_nang_8_rubric_danh_gia_tien_bo.rubric_model import (
    CriterionScore,
    RubricAssessment,
    ProjectMetrics5,
    MetricStatus
)
from chuc_nang_8_rubric_danh_gia_tien_bo.rubric_engine import RubricEngine


class TestChucNang8RubricEngine(unittest.TestCase):

    def setUp(self):
        self.engine = RubricEngine()

    # --- 1. KIỂM THỬ HỌC SINH ĐẠT TIẾN BỘ TỐI ĐA (6/6 ĐIỂM) ---
    def test_rubric_perfect_session_passed(self):
        """Học sinh chủ động nêu đủ dữ kiện, khái niệm và bước làm đạt 6/6 điểm."""
        answers = [
            "Đề cho quãng đường s = 12 km và thời gian t = 30 phút",
            "Em dùng công thức tính tốc độ v = s/t",
            "Bước tiếp theo em đổi 30 phút thành 0.5 giờ rồi chia",
            "Đơn vị tính ra là km/h rất phù hợp"
        ]
        assessment = self.engine.evaluate_session(
            problem_title="Chuyển động của người đi xe đạp",
            problem_text="Một người đi xe đạp quãng đường 12 km trong 30 phút. Tính tốc độ theo km/h.",
            student_answers=answers,
            turn_count=4,
            unknown_count=0
        )
        self.assertEqual(assessment.total_score, 6)
        self.assertTrue(assessment.is_passed, "Tổng điểm 6 >= 4 phải công nhận Đạt tiến bộ")
        self.assertIn("Xuất sắc", assessment.progress_level)
        self.assertEqual(assessment.given_data_score.score, 2)
        self.assertEqual(assessment.core_concepts_score.score, 2)
        self.assertEqual(assessment.next_step_score.score, 2)

    # --- 2. KIỂM THỬ NGƯỠNG ĐẠT CHUẨN MỤC 16.3 (>= 4/6 ĐIỂM) ---
    def test_rubric_passing_threshold_4_points(self):
        """Học sinh đạt 4/6 điểm vẫn được công nhận Đạt tiến bộ theo Mục 16.3."""
        # 1đ dữ kiện, 1đ khái niệm, 2đ bước làm -> Tổng 4đ
        override = {"given_data": 1, "core_concepts": 1, "next_step": 2}
        assessment = self.engine.evaluate_session(
            problem_title="Bài toán KHTN",
            problem_text="Bài toán mẫu",
            student_answers=["12 km", "vận tốc", "đổi phút sang giờ"],
            manual_override=override
        )
        self.assertEqual(assessment.total_score, 4)
        self.assertTrue(assessment.is_passed, "Mục 16.3: Học sinh đạt >= 4/6 là Đạt tiến bộ")

    # --- 3. KIỂM THỬ NGƯỠNG CHƯA ĐẠT (< 4/6 ĐIỂM) ---
    def test_rubric_below_threshold_3_points(self):
        """Học sinh dưới 4 điểm (3/6) xếp loại Cần thêm gợi mở và chưa đạt."""
        override = {"given_data": 1, "core_concepts": 1, "next_step": 1}
        assessment = self.engine.evaluate_session(
            problem_title="Bài toán KHTN",
            problem_text="Bài toán mẫu",
            student_answers=["có số 12", "không nhớ công thức", "chưa biết"],
            manual_override=override
        )
        self.assertEqual(assessment.total_score, 3)
        self.assertFalse(assessment.is_passed, "Tổng điểm 3 < 4 thì is_passed phải là False")
        self.assertIn("Cần thêm gợi mở", assessment.progress_level)

    # --- 4. KIỂM THỬ TIÊU CHÍ 1: NÊU DỮ KIỆN (0-2 ĐIỂM) ---
    def test_criterion_1_scoring(self):
        """Kiểm tra các thang điểm 2, 1, 0 của Tiêu chí 1: Nêu dữ kiện."""
        # Đầy đủ số + đơn vị -> 2đ
        score2, ev2, _, _ = self.engine._evaluate_criterion_1(
            ["Quãng đường là 12 km và thời gian là 30 phút"], "bài toán"
        )
        self.assertEqual(score2, 2)

        # Chỉ có số hoặc hiện tượng sơ sài -> 1đ
        score1, ev1, _, _ = self.engine._evaluate_criterion_1(
            ["Có số 12 và 30"], "bài toán"
        )
        self.assertEqual(score1, 1)

        # Không nêu được dữ kiện -> 0đ
        score0, ev0, _, _ = self.engine._evaluate_criterion_1(
            ["Không biết"], "bài toán"
        )
        self.assertEqual(score0, 0)

    # --- 5. KIỂM THỬ TIÊU CHÍ 2: NÊU KHÁI NIỆM (0-2 ĐIỂM) ---
    def test_criterion_2_scoring(self):
        """Kiểm tra các thang điểm 2, 1, 0 của Tiêu chí 2: Nêu khái niệm."""
        # Nêu đúng định luật phản xạ ánh sáng -> 2đ
        score2, _, _, _ = self.engine._evaluate_criterion_2(
            ["dữ kiện", "Góc phản xạ luôn bằng góc tới i' = i"], "ánh sáng và gương phẳng"
        )
        self.assertEqual(score2, 2)

        # Nhắc được chủ đề chung chung -> 1đ
        score1, _, _, _ = self.engine._evaluate_criterion_2(
            ["dữ kiện", "liên quan đến hiện tượng phản xạ"], "ánh sáng và gương phẳng"
        )
        self.assertEqual(score1, 1)

        # Sai hoặc không nêu được -> 0đ
        score0, _, _, _ = self.engine._evaluate_criterion_2(
            ["dữ kiện", "không nhớ"], "ánh sáng và gương phẳng"
        )
        self.assertEqual(score0, 0)

    # --- 6. KIỂM THỬ TIÊU CHÍ 3: NÊU BƯỚC TIẾP THEO (0-2 ĐIỂM) ---
    def test_criterion_3_scoring(self):
        """Kiểm tra các thang điểm 2, 1, 0 của Tiêu chí 3: Bước tiếp theo."""
        # Tự chủ động nêu bước làm hợp lý mà không bị kẹt -> 2đ
        score2, _, _, _ = self.engine._evaluate_criterion_3(
            ["dữ kiện", "công thức", "Tia sáng bật thẳng ngược trở lại theo phương cũ"],
            turn_count=3,
            unknown_count=0
        )
        self.assertEqual(score2, 2)

        # Cần hỗ trợ gợi ý -> 1đ
        score1, _, _, _ = self.engine._evaluate_criterion_3(
            ["dữ kiện", "công thức", "Bật ngược"],
            turn_count=4,
            unknown_count=1
        )
        self.assertEqual(score1, 1)

    # --- 7. KIỂM THỬ CHẾ ĐỘ THẨM ĐỊNH VIÊN / GIÁO VIÊN CHẤM THỦ CÔNG ---
    def test_manual_evaluator_mode(self):
        """Giáo viên hoặc Giám khảo chấm điểm thủ công và ghi chú."""
        override = {"given_data": 2, "core_concepts": 2, "next_step": 1}
        notes = "Học sinh hiểu bài rất nhanh, có tiềm năng sáng tạo."
        assessment = self.engine.evaluate_session(
            problem_title="Định luật phản xạ ánh sáng",
            problem_text="Gương phẳng",
            student_answers=["hắt lại", "i'=i", "bật lại"],
            manual_override=override,
            evaluator_notes=notes
        )
        self.assertEqual(assessment.evaluator_mode, "teacher_manual")
        self.assertEqual(assessment.evaluator_notes, notes)
        self.assertEqual(assessment.total_score, 5)
        self.assertTrue(assessment.is_passed)

    # --- 8. KIỂM THỬ BẢNG 5 CHỈ SỐ KHOA HỌC DỰ ÁN (MỤC 3) ---
    def test_project_metrics_all_achieved(self):
        """Toàn bộ 5 chỉ số vàng đều phải đạt mục tiêu của Bảng A."""
        metrics = self.engine.get_5_project_metrics()

        # 1. Tỷ lệ OCR: mục tiêu >= 80%
        self.assertGreaterEqual(metrics.ocr_accuracy.current_val, 80.0)
        self.assertTrue(metrics.ocr_accuracy.is_achieved)

        # 2. Tỷ lệ giữ gợi mở: mục tiêu >= 90%
        self.assertGreaterEqual(metrics.socratic_integrity.current_val, 90.0)
        self.assertTrue(metrics.socratic_integrity.is_achieved)

        # 3. Tiến bộ lập luận: mục tiêu >= 70%
        self.assertGreaterEqual(metrics.reasoning_progress.current_val, 70.0)
        self.assertTrue(metrics.reasoning_progress.is_achieved)

        # 4. Hài lòng học sinh: mục tiêu >= 4.0
        self.assertGreaterEqual(metrics.student_satisfaction.current_val, 4.0)
        self.assertTrue(metrics.student_satisfaction.is_achieved)

        # 5. Độ ổn định demo: mục tiêu >= 90% (9/10)
        self.assertGreaterEqual(metrics.demo_stability.current_val, 90.0)
        self.assertTrue(metrics.demo_stability.is_achieved)

        self.assertTrue(metrics.all_achieved)

    # --- 9. KIỂM THỬ XUẤT BÁO CÁO MINH CHỨNG HỒ SƠ BẢNG A ---
    def test_export_markdown_report_structure(self):
        """Báo cáo Markdown phải chứa đầy đủ 3 tiêu chí và 5 chỉ số."""
        assessment = self.engine.evaluate_session(
            problem_title="Quang hợp ở thực vật",
            problem_text="Quang hợp",
            student_answers=["Nước và CO2", "Quang hợp tạo ra O2", "Cây xanh điều hòa khí hậu"]
        )
        report = self.engine.export_report_markdown(assessment)
        self.assertIn("BÁO CÁO ĐÁNH GIÁ TIẾN BỘ LẬP LUẬN", report)
        self.assertIn("1. Nêu Dữ kiện Đề bài", report)
        self.assertIn("2. Nêu Khái niệm Cốt lõi", report)
        self.assertIn("3. Nêu Bước Lập luận", report)
        self.assertIn("BẢNG 5 CHỈ SỐ ĐO LƯỜNG HIỆU QUẢ", report)
        self.assertIn("Tỷ lệ OCR Dùng Được", report)
        self.assertIn("Tỷ lệ Giữ Đúng Chế Độ Gợi Mở", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
