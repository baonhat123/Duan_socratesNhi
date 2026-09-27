"""
Unit Tests: test_chuc_nang_4.py
Kiểm thử toàn diện Chức năng 4 (FR-04: Hội thoại State Machine Socratic 5 pha)
Đặc tả dự án: Socrates Nhí v3.0

Kiểm tra các tiêu chí chấp nhận:
1. Chuyển pha tuần tự theo ma trận: clarify -> recall -> reason -> check -> generalize.
2. Từ chối nài ép xin đáp án (answer_plea): giữ nguyên pha, không bao giờ lộ đáp số.
3. Quy tắc xử lý khi nói 'không biết' (unknown): đếm liên tiếp, lần thứ 3 hạ độ khó và reset.
4. Ngưỡng tối đa 7 lượt hội thoại: chuyển thẳng sang pha generalize để khép phiên.
5. Ngưỡng kẹt ở pha 3 sau 5 lượt: khép sớm bằng tự tóm tắt.
6. Cấu trúc mỗi lượt: ĐÚNG 1 câu hỏi chính, tối đa 1 gợi ý vi mô (<= 140 ký tự), 1 câu nhận xét.
7. Hậu kiểm Guardrail chống rò đáp số.
"""

import unittest
from chuc_nang_4_hoi_thoai_socratic.socratic_model import SocraticPhase, StudentState, TurnResponse
from chuc_nang_4_hoi_thoai_socratic.state_machine import SocraticStateMachine
from chuc_nang_4_hoi_thoai_socratic.socratic_engine import SocraticEngine


class TestChucNang4(unittest.TestCase):

    def setUp(self):
        self.sm = SocraticStateMachine(max_turns=7)
        self.engine = SocraticEngine(max_turns=7)

    # --- 1. KIỂM THỬ MA TRẬN CHUYỂN PHA (MỤC 5.2) ---
    def test_progression_clarify_to_recall(self):
        """Học sinh trả lời đúng dữ kiện ở clarify -> chuyển sang recall."""
        start_phase, next_phase, _ = self.sm.transition(StudentState.CORRECT)
        self.assertEqual(start_phase, SocraticPhase.CLARIFY)
        self.assertEqual(next_phase, SocraticPhase.RECALL)

    def test_progression_recall_to_reason(self):
        """Học sinh trả lời đúng công thức ở recall -> chuyển sang reason."""
        self.sm.current_phase = SocraticPhase.RECALL
        start_phase, next_phase, _ = self.sm.transition(StudentState.CORRECT)
        self.assertEqual(next_phase, SocraticPhase.REASON)

    def test_progression_reason_to_check(self):
        """Học sinh lập luận đúng ở reason -> chuyển sang check."""
        self.sm.current_phase = SocraticPhase.REASON
        start_phase, next_phase, _ = self.sm.transition(StudentState.CORRECT)
        self.assertEqual(next_phase, SocraticPhase.CHECK)

    def test_progression_check_to_generalize(self):
        """Học sinh kiểm tra đúng ở check -> chuyển sang generalize (khép phiên)."""
        self.sm.current_phase = SocraticPhase.CHECK
        start_phase, next_phase, _ = self.sm.transition(StudentState.CORRECT)
        self.assertEqual(next_phase, SocraticPhase.GENERALIZE)
        self.assertTrue(self.sm.is_session_closed)

    # --- 2. KIỂM THỬ TỪ CHỐI XIN ĐÁP ÁN (ANSWER PLEA) ---
    def test_answer_plea_maintains_phase(self):
        """Tiêu chí FR-04 & FR-05: Khi nài ép xin đáp án, luôn giữ nguyên pha."""
        self.sm.current_phase = SocraticPhase.REASON
        start_phase, next_phase, strategy = self.sm.transition(StudentState.ANSWER_PLEA)
        self.assertEqual(next_phase, SocraticPhase.REASON, "Answer plea tuyệt đối không được tăng pha")

    def test_engine_classifies_answer_plea(self):
        """Kiểm tra nhận diện câu xin đáp án từ văn bản của học sinh."""
        user_input = "Thầy cho em xin kết quả cuối cùng luôn đi"
        state = self.engine.classify_student_answer(user_input, SocraticPhase.CLARIFY)
        self.assertEqual(state, StudentState.ANSWER_PLEA)

        response = self.engine.generate_turn_response("Bài toán chuyển động", user_input)
        self.assertIn("không đưa đáp số", response.feedback.lower())

    # --- 3. KIỂM THỬ QUY TẮC UNKNOWN LIÊN TIẾP (MỤC 5.3) ---
    def test_consecutive_unknown_threshold(self):
        """Tối đa 2 lần unknown, lần thứ 3 hạ độ khó và reset bộ đếm."""
        self.sm.current_phase = SocraticPhase.REASON

        # Lần 1: Giữ nguyên Pha reason
        _, next_1, _ = self.sm.transition(StudentState.UNKNOWN)
        self.assertEqual(next_1, SocraticPhase.REASON)
        self.assertEqual(self.sm.consecutive_unknown_count, 1)

        # Lần 2: Giữ nguyên Pha reason
        _, next_2, _ = self.sm.transition(StudentState.UNKNOWN)
        self.assertEqual(next_2, SocraticPhase.REASON)
        self.assertEqual(self.sm.consecutive_unknown_count, 2)

        # Lần 3: Lùi 1 pha về recall và reset bộ đếm về 0
        _, next_3, strategy = self.sm.transition(StudentState.UNKNOWN)
        self.assertEqual(next_3, SocraticPhase.RECALL)
        self.assertEqual(self.sm.consecutive_unknown_count, 0)
        self.assertIn("Hạ độ khó", strategy)

    # --- 4. KIỂM THỬ NGƯỠNG TỐI ĐA 7 LƯỢT (MỤC 5.3) ---
    def test_max_7_turns_closure(self):
        """Đến lượt thứ 7, hệ thống chuyển thẳng sang pha generalize bất kể đang ở pha nào."""
        self.sm.turn_count = 7
        self.sm.current_phase = SocraticPhase.CLARIFY
        _, next_phase, _ = self.sm.transition(StudentState.PARTIAL)
        self.assertEqual(next_phase, SocraticPhase.GENERALIZE)
        self.assertTrue(self.sm.is_session_closed)

    # --- 5. KIỂM THỬ KẸT Ở PHA 3 SAU 5 LƯỢT (MỤC 5.3) ---
    def test_stuck_at_phase_3_after_5_turns(self):
        """Sau 5 lượt chưa qua pha 3 -> Khép sớm bằng tự tóm tắt, không hé đáp án."""
        self.sm.turn_count = 5
        self.sm.current_phase = SocraticPhase.REASON
        _, next_phase, strategy = self.sm.transition(StudentState.PARTIAL)
        self.assertEqual(next_phase, SocraticPhase.GENERALIZE)
        self.assertTrue(self.sm.is_session_closed)
        self.assertIn("chưa vượt qua lập luận", strategy)

    # --- 6. KIỂM THỬ CẤU TRÚC PHẢN HỒI SƯ PHẠM (FR-04) ---
    def test_single_main_question_and_micro_hint_limit(self):
        """Mỗi lượt có đúng 1 câu hỏi chính, micro_hint <= 140 ký tự."""
        response = self.engine.generate_turn_response(
            problem_text="s = 12 km, t = 30 phút",
            student_message="Dữ kiện là quãng đường 12 km và thời gian 30 phút"
        )
        # 1. Có nhận xét
        self.assertTrue(bool(response.feedback.strip()))
        # 2. Đúng 1 câu hỏi chính (chỉ có 1 dấu hỏi)
        self.assertEqual(response.next_question.count("?"), 1)
        # 3. Gợi ý vi mô không vượt quá 140 ký tự
        if response.micro_hint:
            self.assertLessEqual(len(response.micro_hint), 140)

    # --- 7. KIỂM THỬ HẬU KIỂM GUARDRAIL (FR-07) ---
    def test_guardrail_leak_prevention(self):
        """Hậu kiểm phát hiện mẫu rò rỉ đáp số và thay thế bằng fallback."""
        text_with_leak = "Kết quả là 24 km/h nhé em."
        is_leak = self.engine._detect_answer_leak(text_with_leak)
        self.assertTrue(is_leak)


if __name__ == "__main__":
    unittest.main(verbosity=2)
