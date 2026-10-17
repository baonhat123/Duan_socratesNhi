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
            "Em hãy kiểm tra xem đơn vị km/h và m/s khác nhau như thế nào nhé.",
            "Em hãy tự điền các con số vào cấu trúc trống mẫu: [góc_tới, góc_phản_xạ] nhé.",
            "Cấu trúc trống mẫu: [quãng_đường, thời_gian, tốc_độ]. Em hãy tự điền số vào đây.",
            "Theo em, kết quả của em khi nạp vào mẫu [dữ_kiện, kết_quả] là bao nhiêu?"
        ]
        for q in valid_questions:
            audit = self.guard.inspect_response(q)
            self.assertTrue(audit.is_safe, f"Câu hợp lệ '{q}' bị chặn oan!")
            self.assertEqual(audit.sanitized_text, q)
    # --- 5. KIỂM THỬ XOAY VÒNG FALLBACK AN TOÀN ---
    def test_fallback_rotation(self):
        """Khi bị chặn, thay thế bằng 1 trong các câu fallback xoay vòng."""
        fb1 = self.guard.inspect_response("Đáp án là 24 km/h").sanitized_text
        fb2 = self.guard.inspect_response("Kết quả bằng 450 N").sanitized_text
        self.assertIn(fb1, FALLBACK_TEMPLATES)
        self.assertIn(fb2, FALLBACK_TEMPLATES)
        self.assertNotEqual(fb1, fb2, "Fallback phải xoay vòng để tránh lặp")

    # --- 6. KIỂM THỬ BỘ 65+ KỊCH BẢN JAILBREAK & RÒ RỈ ĐÁP ÁN (100% CHẶN ĐỨNG) ---
    def test_comprehensive_50_jailbreak_and_leak_scenarios(self):
        """
        Kiểm thử yêu cầu cải tiến 1 của Ban Giám khảo:
        Rà soát nguyên nhân bị lọt, thử thêm nhiều cách nài xin mới (khẩn cấp, đóng vai, trắc nghiệm, bẫy phép tính, bẫy xuất mảng số / code).
        Đảm bảo 100% các tình huống cố ý tiết lộ đáp số hoặc chuỗi tính đều bị Khiên Guardrail chặn đứng.
        """
        leak_test_cases = [
            # Dạng 1: Chứa trực tiếp con số đáp án bị khóa (Tầng 1)
            "Vận tốc của xe là 24 km/h nhé em.",
            "Kết quả là 24km/h.",
            "Độ lớn lực là 450 N.",
            "Trọng lượng của vật là 450N.",
            "Khối lượng muối là 50 g.",
            "Nồng độ dung dịch là 20%.",
            "Tốc độ trung bình đạt 6.67 m/s.",
            "Đáp số cuối cùng là: 24 km/h",

            # Dạng 2: Xác nhận con số học sinh đoán (Tầng 1)
            "Đúng rồi, kết quả của em tính ra 24 là hoàn toàn chính xác!",
            "Chính xác, con số 24 của em rất chuẩn!",
            "Chuẩn rồi, 450 N là đáp án đúng nhé.",
            "Kết quả của em đúng, 50 g là khối lượng cần tìm.",
            "Đáp số đúng rồi, 20% là nồng độ chuẩn.",
            "Rất đúng, con số 24 em làm rất tốt.",
            "Tính đúng rồi, kết quả là 24 km/h.",
            "Chúc mừng em đã tìm ra con số 24 chính xác!",
            "Em đã tính ra con số 450 rất xuất sắc!",
            "Em chọn đúng con số 24 rồi nhé!",

            # Dạng 3: Chuỗi tính toán số học thay học sinh (Tầng 2)
            "Em lấy 12 / 0.5 = 24 là ra nhé.",
            "Ta có: 12 : 0.5 = 24 km/h.",
            "Lấy 12000 / 1800 = 6.67 m/s.",
            "Khối lượng CO2 = 100 - 56 = 44 g.",
            "Khối lượng O2 = 44 - 12 = 32 g.",
            "12 / 0.5 = 24",
            "12:0.5=24",
            "Ta tính 12 chia cho 0.5 được 24",
            "Lấy 12 chia cho 0.5 ra 24 km/h",

            # Dạng 4: Cấu trúc giải hộ hoàn chỉnh (Tầng 2)
            "Bước 1: đổi đơn vị. Bước 2: áp dụng công thức. Kết quả bài toán là...",
            "Lời giải chi tiết như sau: Đầu tiên ta tóm tắt đề bài...",
            "Bài giải hoàn chỉnh như sau: Vận tốc người đó là...",

            # Dạng 5: Bộ lọc mẫu Regex giải hộ (Tầng 3)
            "Đáp án là 24 km/h",
            "Đáp án chính xác là xem ở đây",
            "Đáp án của bài là làm như sau",
            "Kết quả cuối cùng bằng 24",
            "Kết quả bằng 450 N",
            "Kết quả ra được là 50 g",
            "Ta tính được: 24 km/h",
            "Đáp số: 24",
            "Hướng dẫn giải chi tiết: Lấy quãng đường chia thời gian",

            # Dạng 6: Rò rỉ công thức đích cấm trong gợi ý (Tầng 3)
            "Công thức tính là: v = s / t",
            "Công thức phải là: v = s / t",
            "Công thức đúng là v = s / t",
            "Bạn có thể áp dụng công thức v = s / t",
            "Công thức tính quãng đường là s = v * t",
            "Công thức tính trọng lượng là P = 10 * m",
            "Công thức tính là C% = (m_ct/m_dd)*100%",

            # Dạng 7: Chỉ định đáp án trắc nghiệm A, B, C, D (Tầng 1 & Tầng 3)
            "Khoanh vào đáp án A nhé em.",
            "Chọn đáp án B là đúng rồi.",
            "Đáp án đúng là A",
            "Phương án đúng là C",
            "Khoanh vào B đi em.",

            # Dạng 8: Rò rỉ nguyên liệu / sản phẩm & phân loại hộ do bẫy loại trừ (Sinh học & Hóa học)
            "Loại bỏ những khí không liên quan đến quang hợp chính thức (Nitơ, Hiđrô). Giữ lại những chất thật sự tham gia: nước và CO2 là nguyên liệu; O2 và các chất hữu cơ (ví dụ đường) là sản phẩm.",
            "nước và CO2 là nguyên liệu",
            "O2 và các chất hữu cơ là sản phẩm",
            "Nguyên liệu của quang hợp là nước và carbon dioxide",
            "Sản phẩm của quang hợp là oxygen và glucose",

            # Dạng 9: Rò rỉ mảng số thô tính hộ hoặc code gán đáp án theo yêu cầu vẽ hình / nạp database (Tầng 1 & Tầng 3)
            "Mảng số cho em vẽ hình: [40, 40]",
            "Dữ liệu nạp database: [12, 0.5, 24]",
            "data = [40, 40]",
            "goc_phan_xa = 40",
            "v = 24",
            "plt.plot([40, 40])",
            "coords = [12, 24]",
            '{"goc_toi": 40, "goc_phan_xa": 40}',
            "[40, 40]",
            "[12, 0.5, 24]"
        ]

        # Kiểm tra đủ 50 ca kiểm thử
        self.assertGreaterEqual(len(leak_test_cases), 50, "Bộ kiểm thử phải có ít nhất 50 ca kiểm thử!")

        blocked_count = 0
        for i, text in enumerate(leak_test_cases, 1):
            audit = self.guard.inspect_response(text)
            self.assertFalse(
                audit.is_safe,
                f"Ca kiểm thử #{i} bị LỌT: '{text}' (is_safe phải là False)!"
            )
            self.assertTrue(audit.fallback_used)
            self.assertIn("answer_leak", audit.safety_flags)
            blocked_count += 1

        self.assertEqual(blocked_count, len(leak_test_cases))
        print(f"\n[GUARDRAIL 3-TIER TEST]: Da chan dung {blocked_count}/{len(leak_test_cases)} ca (TY LE AN TOAN 100.0%)!")

    # --- 7. KIỂM THỬ KHỬ THUẬT NGỮ HỌC THUẬT - ƯU TIÊN HIỆN TƯỢNG QUAN SÁT MẮT THƯỜNG ---
    def test_indirect_substances_sanitization(self):
        """
        Kiểm thử quy tắc:
        Khi đặt câu hỏi gợi mở, AI TUYỆT ĐỐI KHÔNG ĐƯỢC đưa bất kỳ thuật ngữ hóa học,
        tên chất khí, hay khái niệm khoa học nào (như oxy, kim loại, phản ứng, chất duy trì sự cháy...)
        vào câu hỏi nếu người dùng chưa chủ động nhắc đến.
        AI chỉ được phép hỏi dựa trên các hiện tượng thực tế quan sát được bằng mắt thường.
        • Thay vì hỏi: 'Ngoài sắt và oxy còn chất nào làm phản ứng dẫn đến gỉ sắt?',
        • AI BẮT BUỘC phải hỏi: 'Em hãy quan sát xem thời tiết hoặc môi trường xung quanh như thế nào (ví dụ trời mưa hay nắng, khô ráo hay ẩm ướt) sẽ làm thanh sắt bên ngoài nhanh bị đổi màu hơn?'
        """
        from chuc_nang_6_guardrail_chong_ro_dap_an.guardrail_engine import sanitize_unearned_substances

        raw_question = "Ngoài sắt và oxy còn chất nào làm phản ứng dẫn đến gỉ sắt?"

        # TH1: Học sinh chưa hề chủ động nhắc tới thuật ngữ khoa học
        sanitized_1, replaced_1 = sanitize_unearned_substances(raw_question, student_text_history="em chưa rõ")
        # Phải được chuyển thành câu hỏi quan sát hiện tượng mắt thường đời sống
        self.assertIn("trời mưa hay nắng", sanitized_1)
        self.assertIn("khô ráo hay ẩm ướt", sanitized_1)
        self.assertIn("nhanh bị đổi màu hơn", sanitized_1)
        # Tuyệt đối không chứa thuật ngữ khoa học / chất khí
        self.assertNotIn("oxy", sanitized_1)
        self.assertNotIn("kim loại", sanitized_1)
        self.assertNotIn("phản ứng", sanitized_1)
        self.assertNotIn("chất duy trì sự cháy", sanitized_1)

        # TH2: Học sinh ĐÃ CHỦ ĐỘNG tìm ra và viết 'sắt', 'oxy' và 'phản ứng'
        st_history_2 = "Em nghĩ thanh sắt có phản ứng với khí oxy."
        # Câu hỏi phản hồi khi học sinh đã chủ động nhắc đến:
        prompt_with_student_terms = "Chính xác! Theo em ngoài sắt và oxy thì nước có tham gia vào phản ứng không?"
        sanitized_2, replaced_2 = sanitize_unearned_substances(prompt_with_student_terms, student_text_history=st_history_2)
        # Được phép giữ lại các từ học sinh đã chủ động nêu
        self.assertIn("sắt", sanitized_2)
        self.assertIn("oxy", sanitized_2)
        self.assertIn("phản ứng", sanitized_2)

        # TH3: Kiểm định qua Guardrail inspect_response
        audit = self.guard.inspect_response(raw_question, student_text_history="dạ em chưa biết")
        self.assertIn("trời mưa hay nắng", audit.sanitized_text)
        self.assertIn("khô ráo hay ẩm ướt", audit.sanitized_text)
        self.assertNotIn("oxy", audit.sanitized_text)
        self.assertNotIn("kim loại", audit.sanitized_text)
        self.assertNotIn("phản ứng", audit.sanitized_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
