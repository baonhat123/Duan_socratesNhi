"""
Module: guardrail_engine.py
Chức năng 6: Bộ Hậu kiểm An toàn Chống Rò rỉ Đáp án 3 Tầng (FR-07)
Đặc tả dự án: Socrates Nhí v3.0 (Mục 10)

Kiến trúc 3 Tầng Hậu kiểm:
1. TẦNG 1: Ép Schema & So đối chiếu số liệu đáp án bị khóa.
2. TẦNG 2: Answer-leak classifier (Thẩm định ngữ nghĩa / LLM độc lập).
3. TẦNG 3: Pattern filter (Bộ lọc mẫu regex phát hiện câu giải hộ).
"""

import os
import re
import json
from typing import List, Optional, Tuple

from .guardrail_model import (
    TierVerdict,
    TierCheckResult,
    GuardrailAudit,
    LOCKED_SAMPLE_ANSWERS
)

# 3 Mẫu Fallback xoay vòng an toàn theo mục 10.3
FALLBACK_TEMPLATES = [
    "Mình chưa thể đưa lời giải sẵn. Em hãy thử chỉ ra dữ kiện quan trọng nhất trong đề trước nhé.",
    "Câu này mình sẽ cùng em tìm ra từng bước. Theo em, dữ kiện nào cho trước là quan trọng nhất?",
    "Mình không chấm đúng/sai con số giúp em được. Em thử nêu cách kiểm tra lại kết quả của mình nhé."
]

# Bảng từ ngữ thay thế gián tiếp các tác chất / sản phẩm đáp án (FR-07 Sư phạm)
# Tuyệt đối không tự ý gọi tên trực tiếp nếu học sinh chưa tự tìm ra và viết trong chat
SENSITIVE_SUBSTANCES_MAP = {
    "chất khí duy trì sự cháy có trong không khí": "không khí",
    "chất khí duy trì sự cháy": "không khí",
    "chất duy trì sự cháy": "không khí",
    "gỉ sắt": "lớp đổi màu nâu đỏ",
    "rỉ sắt": "lớp đổi màu nâu đỏ",
    "oxit sắt": "lớp màu nâu đỏ",
    "fe2o3": "lớp màu nâu đỏ",
    "khí oxygen": "không khí",
    "khí oxy": "không khí",
    "khí oxi": "không khí",
    "oxygen": "không khí",
    "oxy": "không khí",
    "o2": "không khí",
    "thanh kim loại": "thanh sắt",
    "kim loại": "thanh sắt",
    "fe": "thanh sắt",
    "phản ứng hóa học": "sự biến đổi",
    "phản ứng": "sự biến đổi",
    "than củi": "nhiên liệu màu đen",
    "than": "nhiên liệu màu đen",
    "cacbon": "nhiên liệu màu đen",
    "carbon": "nhiên liệu màu đen",
    "đá vôi": "quặng đá khoáng sản màu trắng xám",
    "caco3": "chất rắn khoáng sản màu trắng xám",
    "vôi sống": "chất bột trắng hút ẩm mạnh",
    "cao": "chất bột trắng hút ẩm mạnh"
}


def sanitize_unearned_substances(
    text: str,
    student_text_history: str = ""
) -> Tuple[str, List[str]]:
    """
    Quy tắc Sư phạm Observational Phenomenon-First:
    Khi đặt câu hỏi gợi mở, TUYỆT ĐỐI KHÔNG ĐƯỢC đưa bất kỳ thuật ngữ hóa học,
    tên chất khí, hay khái niệm khoa học nào (như oxy, kim loại, phản ứng, chất duy trì sự cháy...)
    vào câu hỏi nếu người dùng chưa chủ động nhắc đến.
    AI chỉ được phép hỏi dựa trên các hiện tượng thực tế quan sát được bằng mắt thường.
    • Thay vì hỏi: 'Ngoài sắt và oxy còn chất nào làm phản ứng dẫn đến gỉ sắt?',
    • AI BẮT BUỘC phải hỏi: 'Em hãy quan sát xem thời tiết hoặc môi trường xung quanh như thế nào (ví dụ trời mưa hay nắng, khô ráo hay ẩm ướt) sẽ làm thanh sắt bên ngoài nhanh bị đổi màu hơn?'
    """
    if not text:
        return text, []

    st_history_lower = (student_text_history or "").lower()
    text_lower = text.lower()

    # Nhận diện câu hỏi liên quan đến nguyên nhân / phản ứng gỉ sắt
    rust_lead_patterns = [
        r"ngoài\s+(?:sắt|thanh\s+kim\s+loại).*?(?:oxy|chất\s+khí).*?(?:gỉ\s+sắt|màu\s+nâu\s+đỏ)",
        r"ngoài\s+sắt\s+và\s+oxy",
        r"(?:phản\s+ứng|biến\s+đổi).*?(?:dẫn\s+đến|tạo\s+thành)\s+gỉ\s+sắt",
        r"sắt\s+tác\s+dụng\s+với\s+oxy"
    ]
    is_rust_lead = any(re.search(p, text_lower) for p in rust_lead_patterns)
    has_unprompted_rust = any(
        term in text_lower and term not in st_history_lower
        for term in ["oxy", "kim loại", "phản ứng", "chất duy trì sự cháy", "gỉ sắt"]
    )

    if is_rust_lead and has_unprompted_rust:
        replaced = [
            t for t in ["oxy", "kim loại", "phản ứng", "chất duy trì sự cháy", "gỉ sắt"]
            if t in text_lower and t not in st_history_lower
        ]
        phenomenon_question = (
            "Em hãy quan sát xem thời tiết hoặc môi trường xung quanh như thế nào "
            "(ví dụ trời mưa hay nắng, khô ráo hay ẩm ướt) sẽ làm thanh sắt bên ngoài nhanh bị đổi màu hơn?"
        )
        return phenomenon_question, replaced

    sanitized = text
    replaced_substances = []

    # Sắp xếp theo độ dài giảm dần để ưu tiên cụm từ dài trước
    sorted_keys = sorted(SENSITIVE_SUBSTANCES_MAP.keys(), key=len, reverse=True)

    for sub in sorted_keys:
        pattern = rf"(?<![a-zA-ZÀ-ỹ0-9_]){re.escape(sub)}(?![a-zA-ZÀ-ỹ0-9_])"
        if re.search(pattern, sanitized, re.IGNORECASE):
            st_pattern = rf"(?<![a-zA-ZÀ-ỹ0-9_]){re.escape(sub)}(?![a-zA-ZÀ-ỹ0-9_])"
            if not re.search(st_pattern, st_history_lower):
                replacement = SENSITIVE_SUBSTANCES_MAP[sub]
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
                if sub not in replaced_substances:
                    replaced_substances.append(sub)

    return sanitized, replaced_substances


class ThreeTierGuardrail:
    """
    Hệ thống Guardrail 3 Tầng bảo vệ nguyên tắc sư phạm Socrates Nhí.
    """
    def __init__(self, locked_answers: Optional[List[str]] = None):
        self.locked_answers = locked_answers or LOCKED_SAMPLE_ANSWERS
        self.fallback_index = 0

    def get_next_fallback(self) -> str:
        """Xoay vòng mẫu fallback để tránh lặp câu trả lời."""
        res = FALLBACK_TEMPLATES[self.fallback_index % len(FALLBACK_TEMPLATES)]
        self.fallback_index += 1
        return res

    def inspect_response(self, text: str, student_text_history: str = "") -> GuardrailAudit:
        """
        Thẩm định toàn diện một phát ngôn AI qua cả 3 tầng.
        Đảm bảo không rò rỉ số liệu, công thức và không tự ý gọi tên tác chất/sản phẩm đáp án.
        """
        tier_results: List[TierCheckResult] = []
        is_blocked = False
        reasons = []

        # --- TẦNG 1: ÉP SCHEMA & ĐỐI CHIẾU SỐ LIỆU ĐÁP ÁN BỊ KHÓA ---
        t1_result = self._check_tier_1_numerical_leak(text)
        tier_results.append(t1_result)
        if t1_result.verdict == TierVerdict.BLOCKED:
            is_blocked = True
            reasons.append(t1_result.reason)

        # --- TẦNG 2: ANSWER-LEAK CLASSIFIER (NGỮ NGHĨA / CHUỖI TÍNH TOÁN) ---
        t2_result = self._check_tier_2_classifier(text, t1_flagged=(t1_result.verdict == TierVerdict.FLAGGED))
        tier_results.append(t2_result)
        if t2_result.verdict == TierVerdict.BLOCKED:
            is_blocked = True
            reasons.append(t2_result.reason)

        # --- TẦNG 3: PATTERN FILTER (REGEX NHẬN DIỆN CÂU GIẢI HỘ) ---
        t3_result = self._check_tier_3_patterns(text)
        tier_results.append(t3_result)
        if t3_result.verdict == TierVerdict.BLOCKED:
            is_blocked = True
            reasons.append(t3_result.reason)

        # Khử và kiểm tra gọi tên tác chất / sản phẩm chưa được học sinh nhắc tới
        clean_text, replaced_subs = sanitize_unearned_substances(text, student_text_history=student_text_history)

        # Quyết định cuối cùng
        safety_flags = []
        if replaced_subs:
            safety_flags.append("indirect_substance_applied")

        if is_blocked:
            safety_flags.append("answer_leak")
            # Nếu vi phạm về mảng số / code / raw data, trả về đúng thông điệp cấu trúc trống mẫu
            is_code_or_array_issue = any(
                any(k in str(clue) for k in ["mảng_số", "mã_code", "json_chứa_đáp_số", "raw data"])
                for tr in tier_results for clue in tr.matched_clues
            )
            if is_code_or_array_issue:
                sanitized = (
                    "Thầy Socrates Nhí tuyệt đối không xuất mảng số, mã code hay dữ liệu thô chứa kết quả tính toán hộ đâu nhé! "
                    "Nếu em cần định dạng dữ liệu để vẽ hình hoặc nạp database, em hãy tự điền các con số đó vào cấu trúc trống mẫu, "
                    "ví dụ: [góc_tới, góc_phản_xạ] hoặc [quãng_đường, thời_gian, tốc_độ]. Thầy không tính toán hộ con số đâu nè!"
                )
            else:
                sanitized = self.get_next_fallback()
            return GuardrailAudit(
                original_text=text,
                sanitized_text=sanitized,
                tier_results=tier_results,
                is_safe=False,
                fallback_used=True,
                safety_flags=safety_flags
            )

        if replaced_subs:
            tier_results.append(
                TierCheckResult(
                    tier_number=3,
                    tier_name="Tầng 3: Khử Tác chất & Sản phẩm Đáp án (Mô tả Gián tiếp)",
                    verdict=TierVerdict.PASS,
                    reason=f"Đã tự động chuyển đổi các chất [{', '.join(replaced_subs)}] sang mô tả gián tiếp vì học sinh chưa tự tìm ra.",
                    matched_clues=replaced_subs
                )
            )

        return GuardrailAudit(
            original_text=text,
            sanitized_text=clean_text,
            tier_results=tier_results,
            is_safe=True,
            fallback_used=False,
            safety_flags=safety_flags
        )

    def _check_tier_1_numerical_leak(self, text: str) -> TierCheckResult:
        """
        Tầng 1: Trích xuất mọi số kèm đơn vị và đối chiếu với đáp số bị khóa.
        Cũng kiểm tra xem AI có xác nhận đúng/sai con số học sinh đoán không.
        Chặn xuất mảng số hoặc mã code gán biến kết quả tính toán thay học sinh.
        """
        matched = []
        text_lower = text.lower()

        # 1. Đối chiếu trực tiếp với các đáp số bị khóa
        for ans in self.locked_answers:
            escaped = re.sub(r'\\ ', r'\\s*', re.escape(ans.lower()))
            escaped = re.sub(r'(\d)([a-zA-Z%])', r'\1\\s*\2', escaped)
            pattern = r"(?<![a-zA-Z0-9])" + escaped + r"(?![a-zA-Z0-9])"
            if re.search(pattern, text_lower):
                matched.append(ans)

        # 2. Kiểm tra mẫu xác nhận đúng/sai các con số thuộc danh sách đáp số bị khóa của đề bài
        locked_nums = set()
        for ans in self.locked_answers:
            nums = re.findall(r"\b\d+(?:[\.,]\d+)?\b", ans)
            locked_nums.update(nums)

        for num in locked_nums:
            confirm_pattern = re.compile(
                rf"(?:(đúng rồi|chính xác|chuẩn rồi|kết quả của em đúng|đáp số đúng|rất đúng|tính đúng|chúc mừng|xuất sắc|rất tốt|tìm ra|tính ra|chọn đúng|con số).{{0,40}}\b{re.escape(num)}\b|\b{re.escape(num)}\b.{{0,40}}(đúng rồi|chính xác|chuẩn rồi|kết quả của em đúng|đáp số đúng|rất đúng|tính đúng|chúc mừng|xuất sắc|rất tốt|tìm ra|tính ra|chọn đúng))",
                re.IGNORECASE
            )
            if confirm_pattern.search(text_lower):
                matched.append(f"xác_nhận_con_số_đáp_án_{num}")
                break

        # 3. Chặn xuất mảng số (array) chứa kết quả tính toán hoặc đáp số bị khóa
        # Ví dụ: [40, 40], [12, 0.5, 24], [24], data = [40, 40]
        # Lưu ý: Cấu trúc trống mẫu chứa chữ như [góc_tới, góc_phản_xạ] hoặc [quãng_đường, thời_gian, tốc_độ] thì PASS
        array_matches = re.findall(r"\[([\s\d\.,\-]+)\]", text)
        for arr_content in array_matches:
            arr_nums = re.findall(r"\b\d+(?:[\.,]\d+)?\b", arr_content)
            if any(num in locked_nums for num in arr_nums):
                matched.append(f"xuất_mảng_số_chứa_đáp_án_[{arr_content.strip()}]")
                break
            elif len(arr_nums) >= 2 and any(num in ["12", "0.5", "0,5", "40", "50", "24", "450"] for num in arr_nums):
                matched.append(f"xuất_mảng_số_tính_hộ_[{arr_content.strip()}]")
                break

        # 4. Chặn mã code hoặc gán biến kết quả tính toán / đáp số bị khóa
        # Ví dụ: goc_phan_xa = 40, v = 24, toc_do = 24, data = [40, 40]
        if locked_nums:
            escaped_locked_nums = '|'.join(re.escape(n) for n in locked_nums)
            code_patterns = [
                rf"\b(?:v|toc_do|van_toc|goc_phan_xa|goc_toi|dap_so|ket_qua|i_prime)\s*=\s*(?:{escaped_locked_nums})\b",
                r"\b(?:data|array|coords|points|result)\s*=\s*\[[\s\d\.,]+\]",
                r"(?:plt\.plot|draw|create_graph)\s*\(\s*\[[\s\d\.,]+\]"
            ]
            for cp in code_patterns:
                if re.search(cp, text_lower):
                    matched.append("mã_code_gán_đáp_số_hoặc_mảng_số_tính_hộ")
                    break

        # 5. Chặn JSON/Dictionary điền sẵn đáp án bị khóa
        for num in locked_nums:
            json_pattern = rf"[\{{\,]\s*[\"'][a-zA-Z0-9_\s]+[\"']\s*:\s*{re.escape(num)}\b"
            if re.search(json_pattern, text):
                matched.append(f"json_chứa_đáp_số_{num}")
                break

        # Chặn mẫu tuyên bố đáp án cuối cùng của cả bài toán
        final_ans_pattern = re.compile(
            r"(?:đáp số (?:cuối cùng )?(?:của bài )?là|kết quả (?:cuối cùng )?(?:của bài )?là)\s*[:=]?\s*\b\d+(?:[\.,]\d+)?\b",
            re.IGNORECASE
        )
        if final_ans_pattern.search(text_lower):
            matched.append("tuyên_bố_đáp_số_cuối_cùng")

        # Chặn khẳng định đáp án trắc nghiệm A, B, C, D
        mcq_leak_pattern = re.compile(
            r"(?:khoanh vào|chọn ngay|đáp án đúng là|đáp án chính xác là)\s+(?:đáp án\s+)?([ABCD])\b",
            re.IGNORECASE
        )
        if mcq_leak_pattern.search(text_lower):
            matched.append("chỉ_định_đáp_án_trắc_nghiệm")

        if matched:
            return TierCheckResult(
                tier_number=1,
                tier_name="Tầng 1: Ép Schema & Khóa Số Liệu Bài Toán",
                verdict=TierVerdict.BLOCKED,
                reason="Phát hiện trùng khớp với đáp số bị khóa hoặc xác nhận trực tiếp con số đáp án.",
                matched_clues=matched
            )

        # Nếu có số kèm đơn vị bất kỳ nhưng không nằm trong danh sách khóa -> Flagged để Tầng 2 soi kỹ
        general_num = re.findall(r"\b\d+(?:[\.,]\d+)?\s*(?:km/h|m/s|N|g|kg)\b", text, re.IGNORECASE)
        if general_num:
            return TierCheckResult(
                tier_number=1,
                tier_name="Tầng 1: Ép Schema & Khóa Số Liệu Bài Toán",
                verdict=TierVerdict.FLAGGED,
                reason="Có số kèm đơn vị KHTN, chuyển Tầng 2 thẩm định ngữ nghĩa.",
                matched_clues=general_num
            )

        return TierCheckResult(
            tier_number=1,
            tier_name="Tầng 1: Ép Schema & Khóa Số Liệu Bài Toán",
            verdict=TierVerdict.PASS,
            reason="Không chứa số liệu đáp án bị khóa.",
            matched_clues=[]
        )

    def _check_tier_2_classifier(self, text: str, t1_flagged: bool) -> TierCheckResult:
        """
        Tầng 2: Answer-leak classifier.
        Phát hiện chuỗi tính toán hoàn chỉnh của bài toán chính (ví dụ: 12 / 0.5 = 24) hoặc giải hộ từng bước.
        """
        clues = []

        # 1. Phát hiện phép tính số học hoàn chỉnh có kết quả là đáp số bị khóa hoặc chuỗi giải hộ bài chính
        locked_nums = set()
        for ans in self.locked_answers:
            nums = re.findall(r"\b\d+(?:[\.,]\d+)?\b", ans)
            locked_nums.update(nums)

        calc_leak = re.search(r"\b\d+(?:[\.,]\d+)?\s*[\+\-\*\/:]\s*\d+(?:[\.,]\d+)?\s*=\s*(\d+(?:[\.,]\d+)?)", text)
        if calc_leak:
            res_val = calc_leak.group(1)
            # Chỉ chặn nếu phép tính cho ra số thuộc đáp án bị khóa hoặc chứa phép chia đề bài chính
            if res_val in locked_nums or any(ans.lower() in text.lower() for ans in self.locked_answers):
                clues.append(calc_leak.group(0))
            elif re.search(r"(?:12\s*[\/:]\s*0[\.,]5|12000\s*[\/:]\s*1800|44\s*-\s*12|100\s*-\s*56)", text):
                clues.append(calc_leak.group(0))

        # Phép tính diễn đạt bằng lời dẫn thẳng tới đáp số
        word_calc = re.search(
            r"(?:lấy|tính)\s+\d+(?:[\.,]\d+)?\s*(?:chia cho|nhân với|trừ cho|cộng với)\s*\d+(?:[\.,]\d+)?\s*(?:được|=|\s*bằng\s*|\s*ra\s*)\s*(\d+(?:[\.,]\d+)?)",
            text,
            re.IGNORECASE
        )
        if word_calc and (word_calc.group(1) in locked_nums or any(ans.lower() in text.lower() for ans in self.locked_answers)):
            clues.append(word_calc.group(0))

        # 2. Phát hiện cấu trúc lời giải hoàn chỉnh
        step_leak = re.search(r"(bước 1:.+bước 2:.+kết quả|lời giải chi tiết như sau:|bài giải hoàn chỉnh như sau:)", text, re.IGNORECASE | re.DOTALL)
        if step_leak:
            clues.append("chuỗi_lời_giải_hoàn_chỉnh")

        # 3. Phán quyết OpenAI độc lập nếu có API Key và tầng 1 nghi ngờ và không ở unit test
        import sys
        is_testing = "unittest" in sys.modules or any("test" in arg.lower() for arg in sys.argv)
        if t1_flagged and os.getenv("OPENAI_API_KEY") and not is_testing:
            try:
                from app_tich_hop_socrates.ai_service import call_ai_chat_completion
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "Bạn là bộ kiểm tra answer-leak chuyên biệt của Socrates Nhí. "
                            "Thẩm định xem câu sau có tiết lộ đáp số, thực hiện phép tính thay học sinh "
                            "hay giải bài hoàn chỉnh không? Trả về JSON: {'is_leak': bool, 'reason': str}"
                        )
                    },
                    {"role": "user", "content": text}
                ]
                ok, _, data, _ = call_ai_chat_completion(messages, json_mode=True, timeout=10.0)
                if ok and data and data.get("is_leak"):
                    clues.append(f"AI_Classifier: {data.get('reason', 'Tiết lộ đáp số')}")
            except Exception:
                pass

        if clues:
            return TierCheckResult(
                tier_number=2,
                tier_name="Tầng 2: Answer-Leak Classifier (Ngữ nghĩa & Chuỗi tính)",
                verdict=TierVerdict.BLOCKED,
                reason="Phát hiện chuỗi tính toán thay học sinh hoặc cấu trúc giải trọn gói.",
                matched_clues=clues
            )

        return TierCheckResult(
            tier_number=2,
            tier_name="Tầng 2: Answer-Leak Classifier (Ngữ nghĩa & Chuỗi tính)",
            verdict=TierVerdict.PASS,
            reason="Không có chuỗi tính toán hay lời giải làm hộ.",
            matched_clues=[]
        )

    def _check_tier_3_patterns(self, text: str) -> TierCheckResult:
        """
        Tầng 3: Pattern filter (Bộ lọc nhanh regex chặn các mẫu làm hộ và rò rỉ đáp án).
        """
        forbidden_regexes = [
            r"đáp án (?:là|chính xác là|của bài là)\s*[:=]?",
            r"kết quả (?:cuối cùng|bằng|ra được là)\s*[:=]?",
            r"ta tính được\s*[:=]?\s*\d+",
            r"đáp số\s*[:=]",
            r"hướng dẫn giải chi tiết:",
            r"bài giải hoàn chỉnh:",
            r"(?:công\s+thức|áp\s+dụng)\s+.*?(?:v\s*=\s*s\s*/\s*t|s\s*=\s*v\s*[\*xX\.]\s*t|P\s*=\s*10\s*[\*xX\.]\s*m|C%\s*=)",
            r"khoanh\s+vào\s+(?:đáp\s+án\s+)?(?:A|B|C|D)\b",
            r"chọn\s+(?:đáp\s+án\s+)?(?:A|B|C|D)\s+(?:.*?\b)?(?:đúng|nhé|đi)",
            r"(?:đáp\s+án|phương\s+án)\s+đúng\s+là\s+([ABCD])\b",
            # Chặn rò rỉ nguyên liệu / sản phẩm & phân loại hộ chất trong Sinh học & Hóa học
            r"(?:nước|co2|carbon dioxide|h2o|khí cacbonic)\s+.*?\blà\s+nguyên\s+liệu\b",
            r"(?:oxygen|o2|khí oxi|glucose|glucozo|chất hữu cơ|đường)\s+.*?\blà\s+sản\s+phẩm\b",
            r"(?:nguyên\s+liệu|sản\s+phẩm)\s+(?:của\s+[\w\s]+\s+)?(?:là|gồm)\s*[:=]?\s*(?:nước|co2|carbon dioxide|h2o|oxygen|o2|glucose|glucozo|chất hữu cơ|đường)",
            r"loại\s+bỏ\s+.*?(?:giữ\s+lại|những\s+chất\s+thật\s+sự|không\s+liên\s+quan)",
            r"giữ\s+lại\s+.*?(?:là\s+nguyên\s+liệu|là\s+sản\s+phẩm|thật\s+sự\s+tham\s+gia)",
            r"(?:là|thuộc)\s+nguyên\s+liệu.*?(?:là|thuộc)\s+sản\s+phẩm",
            r"(?:chất\s+tham\s+gia|chất\s+sản\s+phẩm)\s+(?:của\s+[\w\s]+\s+)?(?:là|gồm)\s*[:=]?\s*(?:carbon|than|đá\s*vôi|caco3|nước|oxygen|co2|o2)",
            r"(?:chất\s+khí\s+sinh\s+ra|khí\s+thoát\s+ra)\s+(?:chính\s+)?là\s*[:=]?\s*(?:co2|o2|oxygen|carbon dioxide)",
            # Chặn xuất mảng số chứa kết quả tính toán hoặc gán code tính toán hộ
            r"(?:mảng\s+số|dữ\s+liệu\s+thô|raw\s+data|tọa\s+độ)\s*(?:đã\s+tính|kết\s+quả|cần\s+tìm|cho\s+em|là|gồm)?\s*[:=]?\s*\[[\s\d\.,]+\]",
            r"(?:viết|cho)\s+code\s+(?:tính\s+sẵn|vẽ\s+hình\s+hộ)",
            r"\[\s*\d+(?:[\.,]\d+)?\s*,\s*\d+(?:[\.,]\d+)?\s*\]"
        ]

        matched = []
        for rgx in forbidden_regexes:
            match = re.search(rgx, text, re.IGNORECASE)
            if match:
                matched.append(match.group(0))

        if matched:
            return TierCheckResult(
                tier_number=3,
                tier_name="Tầng 3: Pattern Filter (Lớp chặn mẫu Regex nhanh)",
                verdict=TierVerdict.BLOCKED,
                reason="Trùng khớp với các mẫu câu tiết lộ đáp án trực tiếp.",
                matched_clues=matched
            )

        return TierCheckResult(
            tier_number=3,
            tier_name="Tầng 3: Pattern Filter (Lớp chặn mẫu Regex nhanh)",
            verdict=TierVerdict.PASS,
            reason="Vượt qua bộ lọc mẫu regex an toàn.",
            matched_clues=[]
        )


def audit_and_sanitize_response(
    text: str,
    locked_answers: Optional[List[str]] = None,
    student_text_history: str = ""
) -> GuardrailAudit:
    """Hàm tiện ích một chạm để thẩm định và khử rò rỉ đáp số & tác chất."""
    guard = ThreeTierGuardrail(locked_answers=locked_answers)
    return guard.inspect_response(text, student_text_history=student_text_history)
