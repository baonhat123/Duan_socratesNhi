# -*- coding: utf-8 -*-
"""
Module: test_quiz_service.py
Bộ kiểm thử tự động cho QuizService và QuizModalDialog (Trắc nghiệm & Tự luận KHTN 7).
"""

import unittest
from app_tich_hop_socrates.quiz_service import QuizService, QuizQuestion, QuizRecord
from app_tich_hop_socrates.quiz_view import QuizModalDialog


class TestQuizService(unittest.TestCase):
    """Kiểm thử tính năng bài kiểm tra củng cố và ôn tập ngắt quãng."""

    def setUp(self):
        """Dọn dẹp bản ghi của test_student_unit trước mỗi test."""
        self._cleanup_test_user()

    def tearDown(self):
        """Dọn dẹp bản ghi sau mỗi test."""
        self._cleanup_test_user()

    def _cleanup_test_user(self):
        records = QuizService.load_quiz_history()
        filtered = [r for r in records if r.username != "test_student_unit"]
        if len(filtered) != len(records):
            import json
            from app_tich_hop_socrates.quiz_service import QUIZ_HISTORY_FILE
            with open(QUIZ_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([r.to_dict() for r in filtered], f, ensure_ascii=False, indent=2)

    def test_detect_topic_key(self):
        """Kiểm tra phân tích từ khóa để nhận diện chủ đề kiểm tra chuẩn KHTN 7."""
        self.assertEqual(QuizService.detect_topic_key("Tốc độ chuyển động của xe đạp"), "chuyen_dong_toc_do")
        self.assertEqual(QuizService.detect_topic_key("Lực ma sát cản trở chuyển động kéo bàn"), "luc_ma_sat")
        self.assertEqual(QuizService.detect_topic_key("Phân biệt Khối lượng và Trọng lượng"), "khoi_luong_trong_luong")
        self.assertEqual(QuizService.detect_topic_key("Quãng đường đoàn tàu chuyển động thẳng đều"), "quang_duong_chuyen_dong")
        self.assertEqual(QuizService.detect_topic_key("Hiện tượng phản xạ ánh sáng gương phẳng"), "anh_sang_guong_phang")
        self.assertEqual(QuizService.detect_topic_key("Quá trình quang hợp ở lá cây xanh"), "quang_hop_thuc_vat")
        self.assertEqual(QuizService.detect_topic_key("Định luật bảo toàn khối lượng khi than cháy"), "bao_toan_khoi_luong")
        self.assertEqual(QuizService.detect_topic_key("Nung đá vôi tạo vôi sống và khí carbon dioxide"), "nung_da_voi")
        self.assertEqual(QuizService.detect_topic_key("Pha chế dung dịch muối ăn và Nồng độ phần trăm"), "dung_dich_nong_do")

    def test_friction_quiz_not_velocity(self):
        """Đảm bảo đề tài lực ma sát kéo bàn KHÔNG BAO GIỜ bị nhầm sang bài toán vận tốc v=s/t."""
        problem = "Một học sinh kéo một chiếc bàn trên sàn phòng học. Hãy giải thích tại sao khi mới bắt đầu kéo thì thấy rất nặng..."
        questions = QuizService.get_quiz_for_problem(problem_text=problem, topic="Lực ma sát và Chuyển động", quiz_type="pre_test", use_ai=False)
        self.assertEqual(len(questions), 3)
        for q in questions:
            # Câu hỏi phải về ma sát, không được về km/h hay v = s / t
            self.assertNotIn("km/h", q.prompt)
            self.assertNotIn("v = s / t", q.prompt)
            self.assertIn("ma sát", (q.prompt + q.explanation).lower())

    def test_get_quiz_for_topic(self):
        """Kiểm tra ngân hàng học liệu trả về đủ 3 câu trắc nghiệm + 1 câu tự luận."""
        questions = QuizService.get_quiz_for_topic("Tốc độ xe đạp")
        self.assertEqual(len(questions), 4)

        mcq_count = sum(1 for q in questions if q.q_type == "mcq")
        essay_count = sum(1 for q in questions if q.q_type == "essay")
        self.assertEqual(mcq_count, 3)
        self.assertEqual(essay_count, 1)

    def test_grade_full_quiz_calculation(self):
        """Kiểm tra tính điểm trắc nghiệm tức thì và chấm tự luận theo tiêu chí khoa học."""
        questions = QuizService.get_quiz_for_topic("Tốc độ xe đạp")
        # Đúng cả 3 câu trắc nghiệm bằng cách chọn đúng q.correct_index
        mcq_answers = {
            q.question_id: q.correct_index
            for q in questions
            if q.q_type == "mcq"
        }
        essay_answer = (
            "Khu vực cổng trường học có đông học sinh qua lại bất ngờ. "
            "Giới hạn tốc độ 30 km/h giúp giảm quãng đường phanh an toàn và tài xế có đủ thời gian phản xạ để dừng xe kịp thời."
        )

        total_score, correct_mcq, essay_score, essay_feedback, details = QuizService.grade_full_quiz(
            questions=questions,
            mcq_answers=mcq_answers,
            student_essay=essay_answer
        )

        self.assertEqual(correct_mcq, 3)
        self.assertGreaterEqual(essay_score, 2.5)
        self.assertGreaterEqual(total_score, 8.5)
        self.assertEqual(len(details), 4)
        self.assertTrue(len(essay_feedback) > 0)

    def test_save_and_retrieve_quiz_record(self):
        """Kiểm tra lưu trữ và truy xuất lịch sử kiểm tra của học sinh."""
        record = QuizRecord(
            quiz_id="TEST_QUIZ_001",
            username="test_student_unit",
            student_name="Em Nam",
            topic="Tốc độ chuyển động",
            strand="Vật lý",
            quiz_type="post_lesson",
            created_at="2026-10-14T20:00:00",
            score=9.0,
            total_mcq=3,
            correct_mcq=3,
            essay_score=3.0,
            essay_feedback="Tư duy rất tốt",
            student_essay_answer="Câu trả lời mẫu của học sinh",
            badge_earned="Xuất Sắc ⭐",
            details=[]
        )

        ok = QuizService.save_quiz_record(record)
        self.assertTrue(ok)

        records = QuizService.get_student_records("test_student_unit")
        self.assertTrue(len(records) > 0)
        self.assertEqual(records[0].score, 9.0)

        stats = QuizService.get_student_quiz_stats("test_student_unit")
        self.assertGreaterEqual(stats["total_quizzes"], 1)
        self.assertEqual(stats["last_score"], 9.0)
        self.assertEqual(stats["excellent_count"], 1)

    def test_daily_review_pending(self):
        """Kiểm tra logic gợi ý bài ôn tập ngắt quãng ngày hôm sau."""
        review_info = QuizService.get_pending_daily_review("test_student_unit")
        self.assertIsNotNone(review_info)
        self.assertIn("topic", review_info)

    def test_quiz_modal_view_render(self):
        """Kiểm tra QuizModalDialog khởi tạo và render giao diện làm bài."""
        class MockPage:
            def __init__(self):
                self.overlay = []
            def update(self):
                pass
            def open(self, dlg):
                pass

        mock_page = MockPage()
        modal = QuizModalDialog(
            page=mock_page,
            topic="Tốc độ chuyển động",
            strand="Vật lý",
            quiz_type="post_lesson"
        )
        modal.show()
        self.assertIsNotNone(modal.dialog)
        self.assertEqual(modal.current_state, "taking")


if __name__ == "__main__":
    unittest.main()
