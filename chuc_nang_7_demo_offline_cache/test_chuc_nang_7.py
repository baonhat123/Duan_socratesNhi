"""
Unit Tests: test_chuc_nang_7.py
Kiểm thử Chức năng 7 (FR-10: Chế Độ Demo Offline & Cache 12 Bài Mẫu 5 Pha Socratic)
Đặc tả dự án: Socrates Nhí v3.0 (Mục 18 - Vận hành lúc thi)

Tiêu chí chấp nhận:
1. Đúng chuẩn 12 bài mẫu chia đều 3 mạch KHTN 7 (4 bài Vật lý, 4 bài Hóa học, 4 bài Sinh học).
2. Mỗi bài mẫu có đủ 5 pha Socratic (clarify, recall, reason, check, generalize).
3. Độ dài gợi ý vi mô (micro_hint) của mọi lượt bắt buộc <= 140 ký tự.
4. Toàn bộ lời thoại cache (câu hỏi, gợi ý, phản hồi) phải vượt qua Guardrail 3 Tầng: Tuyệt đối không rò rỉ đáp số.
5. Bộ điều phối timeout hoạt động chính xác khi phản hồi > 20s (chuyển sang TIMEOUT_FALLBACK).
6. Tự động so khớp đúng đề mẫu từ văn bản học sinh nhập.
"""

import unittest
from chuc_nang_7_demo_offline_cache.offline_model import (
    NetworkMode,
    KnowledgeStrand
)
from chuc_nang_7_demo_offline_cache.offline_bank import (
    OFFLINE_SAMPLE_PROBLEMS,
    get_all_offline_problems,
    get_offline_problems_by_strand
)
from chuc_nang_7_demo_offline_cache.offline_engine import OfflineDemoEngine
from chuc_nang_6_guardrail_chong_ro_dap_an.guardrail_engine import ThreeTierGuardrail


class TestChucNang7(unittest.TestCase):

    def setUp(self):
        self.engine = OfflineDemoEngine(force_offline=True)
        self.guard = ThreeTierGuardrail()

    # --- 1. KIỂM THỬ SỐ LƯỢNG 12 BÀI MẪU & PHÂN BỔ 3 MẠCH (FR-10 & MỤC 18) ---
    def test_bank_contains_12_curated_problems(self):
        """FR-10: Ngân hàng cache phải có đúng 12 bài mẫu chia đều 3 mạch kiến thức."""
        all_probs = get_all_offline_problems()
        self.assertEqual(len(all_probs), 12, "Ngân hàng học liệu bắt buộc có đủ 12 bài mẫu!")

        physics = get_offline_problems_by_strand(KnowledgeStrand.PHYSICS)
        chemistry = get_offline_problems_by_strand(KnowledgeStrand.CHEMISTRY)
        biology = get_offline_problems_by_strand(KnowledgeStrand.BIOLOGY)

        self.assertEqual(len(physics), 4, "Mạch Vật lý phải có đúng 4 bài mẫu.")
        self.assertEqual(len(chemistry), 4, "Mạch Hóa học phải có đúng 4 bài mẫu.")
        self.assertEqual(len(biology), 4, "Mạch Sinh học phải có đúng 4 bài mẫu.")

    # --- 2. KIỂM THỬ ĐỦ 5 PHA SOCRATIC TRONG MỌI BÀI MẪU ---
    def test_every_problem_has_5_socratic_phases(self):
        """Mỗi bài mẫu bắt buộc phải có đầy đủ 5 pha Socratic."""
        required_phases = ["clarify", "recall", "reason", "check", "generalize"]
        for p in get_all_offline_problems():
            self.assertEqual(len(p.cached_phases), 5, f"Bài {p.problem_id} không đủ 5 pha!")
            for phase in required_phases:
                self.assertIn(phase, p.cached_phases, f"Bài {p.problem_id} thiếu pha '{phase}'!")
                dlg = p.cached_phases[phase]
                self.assertTrue(len(dlg.question.strip()) > 10, f"Câu hỏi pha '{phase}' bài {p.problem_id} quá ngắn!")
                self.assertTrue(len(dlg.feedback.strip()) > 5, f"Phản hồi pha '{phase}' bài {p.problem_id} bị rỗng!")

    # --- 3. KIỂM THỬ RÀNG BUỘC GỢI Ý VI MÔ (<= 140 KÝ TỰ) ---
    def test_micro_hints_length_within_140_chars(self):
        """Gợi ý vi mô của từng pha bắt buộc không vượt quá 140 ký tự."""
        for p in get_all_offline_problems():
            for phase_name, dlg in p.cached_phases.items():
                hint_len = len(dlg.micro_hint)
                self.assertLessEqual(
                    hint_len,
                    140,
                    f"Gợi ý vi mô bài {p.problem_id} ở pha {phase_name} dài {hint_len} ký tự (> 140 ký tự)!"
                )

    # --- 4. KIỂM THỬ TOÀN BỘ LỜI THOẠI CACHE KHÔNG RÒ ĐÁP ÁN (GUARDRAIL 3 TẦNG) ---
    def test_all_cached_dialogues_pass_three_tier_guardrail(self):
        """Toàn bộ câu hỏi và gợi ý trong 12 bài mẫu phải an toàn 100% qua Guardrail 3 Tầng."""
        for p in get_all_offline_problems():
            for phase_name, dlg in p.cached_phases.items():
                audit_q = self.guard.inspect_response(dlg.question)
                self.assertTrue(
                    audit_q.is_safe,
                    f"Câu hỏi bài {p.problem_id} ở pha {phase_name} vi phạm Guardrail: {audit_q.safety_flags}"
                )

                audit_h = self.guard.inspect_response(dlg.micro_hint)
                self.assertTrue(
                    audit_h.is_safe,
                    f"Gợi ý vi mô bài {p.problem_id} ở pha {phase_name} vi phạm Guardrail: {audit_h.safety_flags}"
                )

    # --- 5. KIỂM THỬ CƠ CHẾ TIMEOUT (> 20S) VÀ CHUYỂN CACHE ---
    def test_timeout_fallback_trigger(self):
        """Khi API mất quá 20s phản hồi, hệ thống phải tự động chuyển sang TIMEOUT_FALLBACK."""
        # Gọi mô phỏng 5 giây (Bình thường)
        is_fallback, msg = self.engine.simulate_api_call_with_timeout(5.0)
        self.assertFalse(is_fallback)

        # Gọi mô phỏng 21.5 giây (Vượt ngưỡng 20s)
        is_fallback, msg = self.engine.simulate_api_call_with_timeout(21.5)
        self.assertTrue(is_fallback)
        self.assertEqual(self.engine.mode, NetworkMode.TIMEOUT_FALLBACK)
        self.assertTrue(self.engine.is_offline())

    # --- 6. KIỂM THỬ TỰ ĐỘNG SO KHỚP ĐỀ MẪU TỪ VĂN BẢN HỌC SINH NHẬP ---
    def test_text_matching_to_sample_problems(self):
        """Bộ điều phối phải tự nhận diện được bài mẫu qua từ khóa."""
        p_vl = self.engine.match_problem_from_text("Cho quãng đường 12 km trong thời gian 30 phút")
        self.assertEqual(p_vl.problem_id, "VL01")

        p_hh = self.engine.match_problem_from_text("Đốt than 12 g carbon tạo thành CO2")
        self.assertEqual(p_hh.problem_id, "HH01")

        p_sh = self.engine.match_problem_from_text("Quang hợp ở lá cây cần ánh sáng mặt trời")
        self.assertEqual(p_sh.problem_id, "SH01")


if __name__ == "__main__":
    unittest.main(verbosity=2)
