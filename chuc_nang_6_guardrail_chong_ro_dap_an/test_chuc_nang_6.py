"""
Unit Tests: test_chuc_nang_6.py
Kiểm thử Chức năng 6 (FR-07: Hệ thống Hậu kiểm Chống Rò rỉ Đáp án 3 Tầng)
Đặc tả dự án: Socrates Nhí v3.0 (Mục 10)

Tiêu chí chấp nhận:
1. Tầng 1: Chặn số liệu trùng khớp đáp số bị khóa và chặn xác nhận con số đoán.
2. Tầng 2: Chặn chuỗi tính toán hoàn chỉnh (ví dụ: 12 / 0.5 = 24).
3. Tầng 3: Chặn các mẫu regex cố ý giải hộ ("đáp án là", "kết quả bằng").
4. Phát ngôn sư phạm hợp lệ không bị chặn nhầm (False Positive = 0).
5. Kích hoạt fallback an toàn xoay vòng và gắn safety_flags = ["answer_leak"].
"""

import unittest
from chuc_nang_6_guardrail_chong_ro_dap_an.guardrail_model import (
    TierVerdict,
    LOCKED_SAMPLE_ANSWERS
)
from chuc_nang_6_guardrail_chong_ro_dap_an.guardrail_engine import (
    ThreeTierGuardrail,
    FALLBACK_TEMPLATES
)


class TestChucNang6(unittest.TestCase):

    def setUp(self):
        self.guard = ThreeTierGuardrail(locked_answers=LOCKED_SAMPLE_ANSWERS)

    # --- 1. KIỂM THỬ TẦNG 1: ÉP SCHEMA & KHÓA SỐ LIỆU ---
    def test_tier_1_blocks_locked_number(self):
        """Tầng 1: Chặn phát ngôn chứa trực tiếp số đáp án bị khóa."""
        text = "Vận tốc của người đó là 24 km/h nhé em."
        audit = self.guard.inspect_response(text)
        self.assertFalse(audit.is_safe)
        self.assertTrue(audit.fallback_used)
        self.assertIn("answer_leak", audit.safety_flags)
        self.assertEqual(audit.tier_results[0].verdict, TierVerdict.BLOCKED)

    def test_tier_1_blocks_number_confirmation(self):
        """Tầng 1: Chặn AI xác nhận đúng/sai con số học sinh đoán."""
        text = "Đúng rồi, kết quả của em tính ra 24 là hoàn toàn chính xác!"
        audit = self.guard.inspect_response(text)
        self.assertFalse(audit.is_safe)
        self.assertEqual(audit.tier_results[0].verdict, TierVerdict.BLOCKED)

    # --- 2. KIỂM THỬ TẦNG 2: CHUỖI TÍNH TOÁN HOÀN CHỈNH ---
    def test_tier_2_blocks_calculation_chain(self):
        """Tầng 2: Chặn chuỗi tính toán toán học hoàn chỉnh thay học sinh."""
        text = "Em lấy 12 / 0.5 = 24 là ra nhé."
        audit = self.guard.inspect_response(text)
        self.assertFalse(audit.is_safe)
        self.assertEqual(audit.tier_results[1].verdict, TierVerdict.BLOCKED)

    # --- 3. KIỂM THỬ TẦNG 3: BỘ LỌC MẪU REGEX (PATTERN FILTER) ---
    def test_tier_3_blocks_forbidden_patterns(self):
        """Tầng 3: Chặn các mẫu câu 'đáp án là', 'kết quả bằng'."""
        patterns = [
            "Đáp án của bài là xem ở đây...",
            "Kết quả cuối cùng bằng giá trị sau...",
            "Đáp số: giá trị cụ thể..."
        ]
        for p in patterns:
            audit = self.guard.inspect_response(p)
            self.assertFalse(audit.is_safe, f"Mẫu '{p}' phải bị chặn")
            self.assertEqual(audit.tier_results[2].verdict, TierVerdict.BLOCKED)

    # --- 4. KIỂM THỬ PHÁT NGÔN SƯ PHẠM HỢP LỆ (PASS) ---
    def test_pedagogical_guiding_question_passes(self):
        """Câu hỏi gợi mở hợp lệ tuyệt đối không bị chặn nhầm."""
        valid_questions = [
            "Theo em, đề bài cho quãng đường s = 12 km và thời gian t = 30 phút thì cần đổi đơn vị nào trước?",
            "Em có nhớ công thức liên hệ giữa quãng đường, thời gian và tốc độ không?",
            "Em hãy kiểm tra xem đơn vị km/h và m/s khác nhau như thế nào nhé."
        ]
        for q in valid_questions:
            audit = self.guard.inspect_response(q)
            self.assertTrue(audit.is_safe, f"Câu hợp lệ '{q}' bị chặn oan!")
            self.assertEqual(audit.sanitized_text, q)
            self.assertEqual(len(audit.safety_flags), 0)

    # --- 5. KIỂM THỬ XOAY VÒNG FALLBACK AN TOÀN ---
    def test_fallback_rotation(self):
        """Khi bị chặn, thay thế bằng 1 trong các câu fallback xoay vòng."""
        fb1 = self.guard.inspect_response("Đáp án là 24 km/h").sanitized_text
        fb2 = self.guard.inspect_response("Kết quả bằng 450 N").sanitized_text
        self.assertIn(fb1, FALLBACK_TEMPLATES)
        self.assertIn(fb2, FALLBACK_TEMPLATES)
        self.assertNotEqual(fb1, fb2, "Fallback phải xoay vòng để tránh lặp")


if __name__ == "__main__":
    unittest.main(verbosity=2)
