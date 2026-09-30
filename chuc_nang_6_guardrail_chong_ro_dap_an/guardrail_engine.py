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

    def inspect_response(self, text: str) -> GuardrailAudit:
        """
        Thẩm định toàn diện một phát ngôn AI qua cả 3 tầng.
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

        # Quyết định cuối cùng
        safety_flags = []
        if is_blocked:
            safety_flags.append("answer_leak")
            sanitized = self.get_next_fallback()
            return GuardrailAudit(
                original_text=text,
                sanitized_text=sanitized,
                tier_results=tier_results,
                is_safe=False,
                fallback_used=True,
                safety_flags=safety_flags
            )

        return GuardrailAudit(
            original_text=text,
            sanitized_text=text,
            tier_results=tier_results,
            is_safe=True,
            fallback_used=False,
            safety_flags=[]
        )

    def _check_tier_1_numerical_leak(self, text: str) -> TierCheckResult:
        """
        Tầng 1: Trích xuất mọi số kèm đơn vị và đối chiếu với đáp số bị khóa.
        Cũng kiểm tra xem AI có xác nhận đúng/sai con số học sinh đoán không.
        """
        matched = []
        text_lower = text.lower()

        # 1. Đối chiếu trực tiếp với các đáp số bị khóa
        for ans in self.locked_answers:
            pattern = r"(?:\b|[:=]\s*)" + re.escape(ans.lower()) + r"(?:\b|[!\.,])"
            if re.search(pattern, text_lower):
                matched.append(ans)

        # 2. Kiểm tra mẫu xác nhận đúng/sai các con số thuộc danh sách đáp số bị khóa của đề bài
        locked_nums = set()
        for ans in self.locked_answers:
            nums = re.findall(r"\b\d+(?:[\.,]\d+)?\b", ans)
            locked_nums.update(nums)

        for num in locked_nums:
            confirm_pattern = re.compile(
                rf"(?:(đúng rồi|chính xác|chuẩn rồi|kết quả của em đúng|đáp số đúng|rất đúng|tính đúng).{{0,40}}\b{re.escape(num)}\b|\b{re.escape(num)}\b.{{0,40}}(đúng rồi|chính xác|chuẩn rồi|kết quả của em đúng|đáp số đúng|rất đúng|tính đúng))",
                re.IGNORECASE
            )
            if confirm_pattern.search(text_lower):
                matched.append(f"xác_nhận_con_số_đáp_án_{num}")
                break

        # Chặn mẫu tuyên bố đáp án cuối cùng của cả bài toán
        final_ans_pattern = re.compile(
            r"(?:đáp số (?:cuối cùng )?(?:của bài )?là|kết quả (?:cuối cùng )?(?:của bài )?là)\s*[:=]?\s*\b\d+(?:[\.,]\d+)?\b",
            re.IGNORECASE
        )
        if final_ans_pattern.search(text_lower):
            matched.append("tuyên_bố_đáp_số_cuối_cùng")

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
            elif re.search(r"(?:12\s*[\/:]\s*0[\.,]5|12000\s*[\/:]\s*1800)", text):
                clues.append(calc_leak.group(0))

        # 2. Phát hiện cấu trúc lời giải hoàn chỉnh
        step_leak = re.search(r"(bước 1:.+bước 2:.+kết quả|lời giải chi tiết như sau:)", text, re.IGNORECASE | re.DOTALL)
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
        Tầng 3: Pattern filter (Bộ lọc nhanh regex chặn các mẫu làm hộ).
        """
        forbidden_regexes = [
            r"đáp án (?:là|chính xác là|của bài là)\s*[:=]?",
            r"kết quả (?:cuối cùng|bằng|ra được là)\s*[:=]?",
            r"ta tính được\s*[:=]?\s*\d+",
            r"đáp số\s*[:=]",
            r"hướng dẫn giải chi tiết:",
            r"bài giải hoàn chỉnh:",
            r"công\s+thức\s+(?:tính\s+[\w\s]+\s+)?(?:là|phải\s+là)\s*[:=]?\s*v\s*=\s*s\s*/\s*t",
            r"(?:bạn|em)?\s*(?:có\s+thể\s+)?(?:thử\s+)?áp\s+dụng\s+công\s+thức\s+v\s*=\s*s\s*/\s*t",
            r"công\s+thức\s+đúng\s+là\s*[:=]?\s*v\s*=\s*s\s*/\s*t"
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


def audit_and_sanitize_response(text: str, locked_answers: Optional[List[str]] = None) -> GuardrailAudit:
    """Hàm tiện ích một chạm để thẩm định và khử rò rỉ đáp số."""
    guard = ThreeTierGuardrail(locked_answers=locked_answers)
    return guard.inspect_response(text)
