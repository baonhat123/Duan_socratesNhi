"""
Module: socratic_engine.py
Chức năng 4 (FR-04, FR-05 & FR-07): Bộ máy tạo sinh hội thoại Socratic thích ứng
Đặc tả: Socrates Nhí v3.0

Hiện thực hóa:
1. Phân loại câu trả lời của học sinh thành 6 kiểu (StudentState).
2. Tích hợp State Machine 5 pha và bộ đếm lượt (tối đa 7 lượt).
3. Hậu kiểm chống rò đáp án 3 tầng (Guardrail): Chặn lộ đáp số, trả về câu fallback xoay vòng.
4. Tương thích OpenAI-compatible API khi có .env hoặc chạy Chế độ Offline Demo tin cậy 100%.
"""

import os
import re
from typing import Tuple, Optional, Dict, Any, List

from .socratic_model import SocraticPhase, StudentState, TurnResponse, ChatMessage
from .state_machine import SocraticStateMachine

try:
    from chuc_nang_6_guardrail_chong_ro_dap_an.guardrail_engine import ThreeTierGuardrail
except (ImportError, ModuleNotFoundError):
    ThreeTierGuardrail = None

try:
    from chuc_nang_7_demo_offline_cache.offline_engine import GLOBAL_OFFLINE_ENGINE
except (ImportError, ModuleNotFoundError):
    GLOBAL_OFFLINE_ENGINE = None

# Các mẫu câu xin đáp án (Jailbreak / Answer Plea) cần chặn theo FR-05 & FR-07
ANSWER_PLEA_PATTERNS = [
    r"(?:cho|xin|biết|hỏi)(?:\s+(?:em|mình|tớ|tôi|bạn|thầy|cô|nhanh))*\s+(?:đáp\s+án|kết\s+quả|đáp\s+số|lời\s+giải)",
    r"(?:giải|làm)\s+(?:hộ|giúp|luôn|hết|toàn\s+bộ)",
    r"(?:kết\s+quả|đáp\s+số)\s+là\s+gì",
    r"kết\s+quả\s+cuối\s+cùng",
    r"ra\s+bao\s+nhiêu",
    r"giải\s+chi\s+tiết\s+ra",
    r"đóng\s+vai\s+thầy\s+cô\s+giải",
    r"chỉ\s+bài\s+đi",
    r"làm\s+hộ\s+đi",
    r"cho\s+đáp\s+án",
    # Các chiêu trò nhờ lọc trừ / phân loại hộ danh sách chất/phương án
    r"loại\s+(?:bỏ|trừ)\s+(?:hoàn\s+toàn\s+)?(?:các|những)?\s*.*?(?:không\s+phải|sai|không\s+thuộc)",
    r"giữ\s+lại\s+(?:đúng\s+)?(?:các|những)?\s*.*?(?:đúng|thuộc|nguyên\s+liệu|sản\s+phẩm|thật\s+sự)",
    r"lọc\s+(?:hộ|giúp|bớt|ra|dùm)",
    r"phân\s+loại\s+(?:hộ|giúp|dùm|thay)",
    r"chỉ\s+ra\s+(?:chất|đáp\s+án|phương\s+án)\s+(?:nào\s+)?(?:là|không\s+phải)",
    r"(?:chọn|bỏ)\s+bớt\s+giúp",
    r"biết\s+đường\s+tránh",
    r"chọn\s+(?:giúp|hộ)\s+(?:em|tôi|mình)",
    # Các chiêu trò yêu cầu xuất mảng số, code, dữ liệu thô để nạp database hoặc vẽ hình
    r"(?:xuất|cho|viết|in|trả\s+về|tạo)\s+(?:mảng|code|mã\s+code|dữ\s+liệu\s+thô|raw\s+data|json|csv|tọa\s+độ|database)",
    r"(?:cho|xin|xuất)\s+(?:danh\s+sách|bảng|mảng)\s+(?:số|giá\s+trị|tọa\s+độ|kết\s+quả).*?(?:vẽ|nạp|chạy|database|bảng)",
    r"(?:viết|cho)\s+code\s+.*?(?:vẽ|tính|ra\s+kết\s+quả|chạy)",
    r"(?:tính|tính\s+toán)\s+hộ",
    r"vẽ\s+hình\s+(?:hộ|giúp|cho)",
    r"nạp\s+database\s+(?:hộ|giúp|cho)",
    r"định\s+dạng\s+dữ\s+liệu\s+để\s+(?:vẽ|nạp)",
    r"(?:cho|xin)\s+mảng\s+\[.*?\]",
    r"xuất\s+mảng\s+số",
    r"cho\s+mảng\s+số"
]

# Các mẫu câu thể hiện sự bối rối / không biết / không có (Unknown)
UNKNOWN_PATTERNS = [
    r"em\s+không\s+biết",
    r"(?:em\s+)?(?:không|hổng|k|ko|khg|chưa)\s+(?:biết|rõ|hiểu|nhớ|chắc|làm|thấy)",
    r"^(?:không|chưa|k|ko)\s+(?:có|biết|hiểu|rõ)$",
    r"(?:không|chưa)\s+có\s+(?:ý\s+kiến|câu\s+trả\s+lời|gì)",
    r"(?:em\s+)?(?:chịu|bó\s+tay|chịu\s+thua|chịu\s+thôi)",
    r"^(?:chịu|chịu\s*luôn|k\s*biết|ko\s*biết|kbiết)$",
    r"không\s+biết\s+(?:bắt\s+đầu|làm|gì)",
    r"chưa\s+hiểu",
    r"(?:khó|bí|rối)\s+quá",
    r"quên\s+(?:mất|rồi|hết)?",
    r"^\s*[\?\.\,\!\-\_\s]+\s*$",
    r"^\s*(?:ko|k|khong|hong)\s*$"
]

# Bộ câu thoại Fallback an toàn khi phát hiện nài ép đáp án hoặc nghi ngờ rò rỉ (Mục 10.3)
FALLBACK_PHRASES = [
    "Socrates Nhí chưa thể đưa lời giải sẵn. Chúng mình sẽ cùng nhau tìm ra từng bước nhé!",
    "Mục tiêu là để em tự làm chủ kiến thức. Theo em, dữ kiện nào trong đề bài là quan trọng nhất?",
    "Mình không thể làm hộ bài được đâu nè! Em hãy thử nhớ lại xem bài toán này liên quan đến đại lượng nào?",
    "Mình không thể chấm đúng/sai con số giúp em. Em hãy nêu cách tự kiểm tra lại kết quả của mình nhé!"
]


class SocraticEngine:
    """
    Bộ máy điều phối và tạo câu hỏi Socratic thích ứng.
    """
    def __init__(self, max_turns: int = 7, unlimited_turns: bool = True):
        self.state_machine = SocraticStateMachine(max_turns=max_turns, unlimited_turns=unlimited_turns)
        self.fallback_index = 0
        self.conversation_history: List[ChatMessage] = []
        self.guardrail = ThreeTierGuardrail() if ThreeTierGuardrail else None

    def reset(self):
        """Khởi động lại toàn bộ phiên hội thoại."""
        self.state_machine.reset()
        self.conversation_history = []
        self.fallback_index = 0

    def classify_student_answer(
        self,
        user_text: str,
        current_phase: SocraticPhase,
        problem_text: str = ""
    ) -> StudentState:
        """
        Phân loại câu trả lời của học sinh vào 6 trạng thái (Mục 5.1).
        Hỗ trợ đa dạng các chủ đề KHTN 7 (Cơ học, Quang học, Hóa học, Sinh học).
        Đánh giá nghiêm ngặt: Tuyệt đối không gán PARTIAL cho câu trả lời đoán mò hoặc sai bản chất.
        """
        text = user_text.strip().lower()

        # 1. Kiểm tra nài ép xin đáp án (Answer Plea)
        for pattern in ANSWER_PLEA_PATTERNS:
            if re.search(pattern, text):
                return StudentState.ANSWER_PLEA

        # 2. Kiểm tra không biết / bối rối (Unknown)
        if len(text) <= 2 or any(re.search(p, text) for p in UNKNOWN_PATTERNS):
            return StudentState.UNKNOWN

        # 3. Kiểm tra nhầm lẫn khái niệm hoặc từ khóa hình học / lạc đề phổ biến (Misconception / Off-Topic)
        unrelated_or_misconception_terms = [
            "trọng lượng bằng khối lượng", "v = s * t", "v = s.t", "v = t/s", "v = t:s",
            "tia phân giác", "phân giác", "góc đối đỉnh", "đối đỉnh",
            "tam giác", "hình vuông", "hình chữ nhật", "đường chéo",
            "đi xuyên qua", "xuyên qua gương", "đi thẳng qua gương",
            "không liên quan", "chuyện khác", "chơi game"
        ]
        if any(term in text for term in unrelated_or_misconception_terms):
            return StudentState.MISCONCEPTION

        # 4. Kiểm tra đúng / đúng một phần theo từng pha với tiêu chí khoa học nghiêm ngặt
        if current_phase == SocraticPhase.CLARIFY:
            # Nhận diện cơ học (quãng đường & thời gian)
            dist_keywords = ["s =", "km", "quãng đường", "12 km", "12km"]
            time_keywords = ["t =", "phút", "thời gian", "giờ", "giây", "30 phút", "30phut"]
            has_dist = any(k in text for k in dist_keywords)
            has_time = any(k in text for k in time_keywords)

            if has_dist and has_time:
                return StudentState.CORRECT
            elif has_dist or has_time:
                return StudentState.PARTIAL

            # Nhận diện quang học (gương phẳng & ánh sáng)
            optics_correct = ["hắt", "bật lại", "phản xạ", "không đi qua", "không xuyên", "đổi hướng", "bị hắt", "dội lại", "ngược lại", "quay lại", "bật ngược"]
            if any(k in text for k in optics_correct):
                return StudentState.CORRECT
            if any(k in text for k in ["ánh sáng", "gương", "mặt gương"]):
                return StudentState.PARTIAL

            # Nhận diện sinh học / hóa học
            bio_keywords = ["nước", "h2o", "co2", "cacbonic", "ánh sáng", "diệp lục", "khí", "rễ", "carbon", "oxi", "oxygen", "caco3"]
            matched_bio = sum(1 for k in bio_keywords if k in text)
            if matched_bio >= 2:
                return StudentState.CORRECT
            elif matched_bio == 1:
                return StudentState.PARTIAL

            general_clarify = ["dữ kiện", "m =", "giây"]
            if any(k in text for k in general_clarify):
                return StudentState.CORRECT

            return StudentState.MISCONCEPTION

        elif current_phase == SocraticPhase.RECALL:
            # Cơ học
            mech_correct = ["v = s/t", "v = s:t", "s/t", "s : t", "quãng đường chia thời gian", "quãng đường chia cho thời gian"]
            mech_wrong = ["v = s * t", "v = s.t", "v = s x t", "v = t/s", "quãng đường nhân thời gian"]
            if any(k in text for k in mech_wrong):
                return StudentState.MISCONCEPTION
            if any(k in text for k in mech_correct):
                return StudentState.CORRECT
            if any(k in text for k in ["quãng đường", "thời gian", "tốc độ", "vận tốc", "công thức"]):
                return StudentState.PARTIAL

            # Quang học
            optics_recall_correct = ["bằng", "bằng nhau", "i' = i", "i = i'", "góc phản xạ bằng góc tới", "bằng góc tới"]
            if any(k in text for k in optics_recall_correct):
                return StudentState.CORRECT
            if any(k in text for k in ["phản xạ", "mặt phẳng tới", "góc tới", "tia tới"]):
                return StudentState.PARTIAL

            # Sinh học & Hóa học
            bio_recall_correct = ["quang hợp", "glucozo", "glucose", "tinh bột", "bảo toàn", "chất hữu cơ"]
            if any(k in text for k in bio_recall_correct):
                return StudentState.CORRECT

            return StudentState.MISCONCEPTION

        elif current_phase == SocraticPhase.REASON:
            reason_correct = [
                "đổi", "thay số", "30 phút = 0.5", "0.5 giờ", "0,5 giờ", "0.5h", "1/2 giờ", "chia cho 0.5",
                "bật lại", "bật ngược", "trùng", "phương cũ", "vuông góc", "0 độ", "0°", "ngược chiều", "thẳng lại", "bật thẳng"
            ]
            if any(k in text for k in reason_correct):
                return StudentState.CORRECT
            if any(k in text for k in ["bước", "trước", "phép tính", "tính toán", "thực hiện"]):
                return StudentState.PARTIAL

            return StudentState.MISCONCEPTION

        elif current_phase == SocraticPhase.CHECK:
            check_correct = [
                "đơn vị", "km/h", "m/s", "hợp lý", "chính xác", "newton", "n",
                "ảnh ảo", "bằng", "bằng nhau", "bằng vật", "đối xứng", "không hứng được"
            ]
            if any(k in text for k in check_correct):
                return StudentState.CORRECT
            if any(k in text for k in ["kết quả", "kiểm tra", "đối chiếu"]):
                return StudentState.PARTIAL

            return StudentState.MISCONCEPTION

        elif current_phase == SocraticPhase.GENERALIZE:
            # Ở Pha 5: Kiểm tra nghiêm túc, không tự động coi mọi câu là CORRECT
            generalize_keywords = [
                "tóm lại", "kết luận", "bài học", "quy tắc", "chú ý", "lưu ý", "nhớ", "rút ra", "kinh nghiệm",
                "tốc độ", "quãng đường", "thời gian", "chia", "phép chia", "phản xạ", "góc tới", "bằng nhau",
                "môi trường", "chân không", "chất rắn", "chất lỏng", "chất khí", "dao động", "tần số", "biên độ"
            ]
            if any(k in text for k in generalize_keywords):
                return StudentState.CORRECT
            if len(text) > 10 and not any(re.search(p, text) for p in UNKNOWN_PATTERNS):
                return StudentState.PARTIAL
            return StudentState.MISCONCEPTION

        return StudentState.MISCONCEPTION

    def generate_turn_response(
        self,
        problem_text: str,
        student_message: str
    ) -> TurnResponse:
        """
        Tạo sinh một lượt hội thoại Socratic hoàn chỉnh (FR-04).
        Đánh giá thông minh qua AI (nếu Online) hoặc qua bộ phân loại quy tắc chuẩn sư phạm (Offline).
        """
        current_phase = self.state_machine.current_phase
        turn_num = self.state_machine.turn_count

        # Bước 1: Thử gọi AI trực tuyến để đánh giá ngữ nghĩa và tạo phản hồi sư phạm
        ai_result = self._try_ai_dialogue(problem_text, current_phase, student_message, turn_num)
        if ai_result:
            feedback, next_question, micro_hint, source, model_used, student_state, is_completed = ai_result
            start_phase, next_phase, strategy = self.state_machine.transition(student_state)
            # Đồng bộ tức thì nếu AI xác nhận hoàn thành đúc kết hoặc phát câu thông báo mở khóa sơ đồ
            if is_completed:
                self.state_machine.is_session_closed = True
                self.state_machine.current_phase = SocraticPhase.GENERALIZE
                next_phase = SocraticPhase.GENERALIZE
        else:
            # Chế độ Offline / Fallback: phân loại theo quy tắc chuẩn
            student_state = self.classify_student_answer(student_message, current_phase, problem_text=problem_text)
            start_phase, next_phase, strategy = self.state_machine.transition(student_state)
            dialogue_result = self._formulate_pedagogical_dialogue(
                problem_text=problem_text,
                start_phase=start_phase,
                next_phase=next_phase,
                student_state=student_state,
                student_text=student_message,
                turn_num=turn_num
            )
            if len(dialogue_result) >= 5:
                feedback, next_question, micro_hint, source, model_used = dialogue_result[:5]
            else:
                feedback, next_question, micro_hint = dialogue_result
                source = "offline"
                model_used = None

            # Kiểm tra chế độ offline nếu lời thoại thông báo mở khóa sơ đồ
            unlock_keywords = [
                "mở khóa sơ đồ", "thầy đã mở khóa", "đã mở khóa sơ đồ",
                "mở khóa sơ đồ tư duy dạng nhánh", "đã mở khóa sđtd"
            ]
            if any(kw in ((next_question or "") + " " + (feedback or "")).lower() for kw in unlock_keywords):
                self.state_machine.is_session_closed = True
                self.state_machine.current_phase = SocraticPhase.GENERALIZE
                next_phase = SocraticPhase.GENERALIZE

        # Lưu tin nhắn của học sinh vào lịch sử với trạng thái chính xác
        self.conversation_history.append(
            ChatMessage(
                sender="student",
                content=student_message,
                phase=current_phase,
                student_state=student_state
            )
        )

        # Bước 4: Hậu kiểm Guardrail chống rò rỉ đáp số & công thức 3 Tầng (FR-07)
        safety_flags = []
        st_history = " ".join([m.content for m in self.conversation_history if m.sender == "student"] + [student_message])
        if self.guardrail:
            # 1. Hậu kiểm feedback
            audit_fb = self.guardrail.inspect_response(feedback, student_text_history=st_history)
            if not audit_fb.is_safe:
                safety_flags.extend(audit_fb.safety_flags)
                if student_state == StudentState.ANSWER_PLEA:
                    st_lower = student_message.lower()
                    if any(w in st_lower for w in ["mảng", "code", "raw data", "dữ liệu thô", "database", "vẽ hình"]):
                        feedback = "Thầy Socrates Nhí tuyệt đối không xuất mảng số hay mã code tính toán hộ đâu nhé! Em hãy tự điền con số vào cấu trúc trống mẫu."
                    else:
                        feedback = "Thầy Socrates Nhí sẽ không làm hộ hay đưa đáp án thay em đâu nè! Mục tiêu là để chính em tự nhận biết và suy luận."
                elif student_state == StudentState.CORRECT:
                    feedback = "Rất tốt! Thầy ghi nhận suy nghĩ chính xác của em, chúng mình cùng bước tiếp nhé."
                else:
                    feedback = "Thầy đang cùng em tìm hiểu từng bước. Chúng mình cùng suy luận tiếp nào!"
            else:
                feedback = audit_fb.sanitized_text

            # 2. Hậu kiểm next_question
            audit_q = self.guardrail.inspect_response(next_question, student_text_history=st_history)
            if not audit_q.is_safe:
                safety_flags.extend(audit_q.safety_flags)
                next_question = audit_q.sanitized_text or "Theo em, bước suy luận tiếp theo ta cần làm gì?"
                micro_hint = "Em hãy chú ý mối liên hệ giữa các đại lượng đề bài đã cho."
            else:
                next_question = audit_q.sanitized_text
                if micro_hint:
                    audit_h = self.guardrail.inspect_response(micro_hint, student_text_history=st_history)
                    if not audit_h.is_safe:
                        safety_flags.extend(audit_h.safety_flags)
                        micro_hint = "Em hãy chú ý các đại lượng đề bài đã cho trước."
                    else:
                        micro_hint = audit_h.sanitized_text
        else:
            try:
                from chuc_nang_6_guardrail_chong_ro_dap_an.guardrail_engine import sanitize_unearned_substances
                next_question, _ = sanitize_unearned_substances(next_question, st_history)
                feedback, _ = sanitize_unearned_substances(feedback, st_history)
                if micro_hint:
                    micro_hint, _ = sanitize_unearned_substances(micro_hint, st_history)
            except Exception:
                pass
            if self._detect_answer_leak(feedback):
                safety_flags.append("answer_leak")
                feedback = "Ý kiến của em cần xem xét lại một chút nhé!"
            if self._detect_answer_leak(next_question) or self._detect_answer_leak(micro_hint or ""):
                safety_flags.append("answer_leak")
                next_question = self._get_safe_fallback()
                micro_hint = "Em hãy chú ý các đại lượng đề bài đã cho trước."

        # Cắt gọt micro_hint đảm bảo <= 140 ký tự
        if micro_hint and len(micro_hint) > 140:
            micro_hint = micro_hint[:137] + "..."

        # Tăng số lượt hội thoại sau khi hoàn tất lượt
        self.state_machine.turn_count += 1

        response = TurnResponse(
            phase=start_phase,
            next_phase=next_phase,
            student_state=student_state,
            feedback=feedback,
            next_question=next_question,
            micro_hint=micro_hint,
            turn_count=turn_num,
            consecutive_unknown_count=self.state_machine.consecutive_unknown_count,
            is_session_closed=self.state_machine.is_session_closed,
            safety_flags=safety_flags,
            source=source,
            model_used=model_used
        )

        # Lưu tin nhắn phản hồi của Socrates Nhí vào lịch sử
        self.conversation_history.append(
            ChatMessage(
                sender="socrates",
                content=next_question,
                phase=next_phase,
                micro_hint=micro_hint,
                feedback=feedback,
                source=source,
                model_used=model_used
            )
        )

        return response

    def _try_ai_dialogue(
        self,
        problem_text: str,
        current_phase: SocraticPhase,
        student_message: str,
        turn_num: int
    ) -> Optional[Tuple[str, str, Optional[str], str, str, StudentState, bool]]:
        """
        Đánh giá ngữ nghĩa thông minh và tạo phản hồi sư phạm qua AI trực tuyến.
        Tuyệt đối không khen sai khi học sinh đoán mò / lạc đề / hiểu sai bản chất.
        """
        try:
            from app_tich_hop_socrates.ai_service import call_ai_chat_completion, get_ai_config, load_project_env
            load_project_env()
        except ImportError:
            return None

        is_offline_mode = bool(GLOBAL_OFFLINE_ENGINE and GLOBAL_OFFLINE_ENGINE.is_offline())
        has_api_key = bool(os.getenv("OPENAI_API_KEY", "").strip())

        if not has_api_key or is_offline_mode:
            return None

        try:

            recent_msgs = []
            for msg in self.conversation_history[-6:]:
                r = "assistant" if msg.sender == "socrates" else "user"
                recent_msgs.append({"role": r, "content": msg.content})

            scaffolding_lvl = self.state_machine.get_scaffolding_level()

            sys_prompt = (
                "Bạn là Chuyên gia Khảo thí & Trợ lý Gia sư Sư phạm Socrates Nhí môn Khoa học Tự nhiên 7 (Bộ GD&ĐT Việt Nam).\n"
                "Mô hình tư duy: Phân tích kiểm tra logic khoa học ở cấp độ cao nhất. Tuyệt đối không qua loa, không khen sai, không ba phải.\n\n"
                "=== NGUYÊN TẮC ĐÁNH GIÁ CÂU TRẢ LỜI CỦA HỌC SINH (SIÊU NGHIÊM NGẶT) ===\n"
                "1. BƯỚC PHÂN TÍCH TỪNG Ý ('analysis'):\n"
                "   - Viết trường 'analysis' súc tích (1-2 câu ngắn gọn): Học sinh đã trả lời ý gì? Ý đó có đúng về mặt khoa học không? Kết luận trạng thái.\n"
                "   - TUYỆT ĐỐI CẤM thói khen ngợi ba phải, vuốt ve sáo rỗng hoặc tự tiện nói 'bạn làm được 1 phần đúng' / 'ý của em đã đúng một phần' khi học sinh TRẢ LỜI SAI, đoán mò, hoặc câu trả lời không hề có ý nào đúng về mặt khoa học!\n"
                "   - CHỈ ĐƯỢC GÁN 'student_state': 'partial' KHI VÀ CHỈ KHI học sinh đã nêu ĐƯỢC ÍT NHẤT 1 Ý HOÀN TOÀN CHÍNH XÁC VỀ MẶT KHOA HỌC trả lời một phần câu hỏi.\n"
                "   - NẾU HỌC SINH NÊU SAI CÔNG THỨC (ví dụ v = s * t), nêu sai bản chất vật lý (ví dụ ánh sáng đi xuyên qua gương phẳng), hoặc đoán mò vô căn cứ:\n"
                "     + BẮT BUỘC gán 'student_state': 'misconception'.\n"
                "     + 'feedback': Thẳng thắn, lịch sự chỉ rõ câu trả lời chưa đúng, nêu điểm mâu thuẫn để học sinh tự thấy vô lý. TUYỆT ĐỐI KHÔNG KHEN 'đúng một phần'!\n"
                "     + 'question': Đặt câu hỏi theo cấp độ giàn giáo (Scaffolding Level) thích ứng.\n"
                "   - NẾU HỌC SINH NÓI LẠC ĐỀ (nói chuyện phiếm, từ khóa toán/hình không liên quan):\n"
                "     + Gán 'student_state': 'off_topic'.\n"
                "     + 'feedback': Nhẹ nhàng nhắc nhở chưa liên quan, kéo học sinh về lại đề bài.\n"
                "   - NẾU HỌC SINH NÓI 'EM KHÔNG BIẾT', 'KHÔNG CÓ', 'CHỊU', bế tắc:\n"
                "     + Gán 'student_state': 'unknown'. Động viên nhẹ nhàng, áp dụng cấp độ giàn giáo Scaffolding tương ứng.\n"
                "   - NẾU HỌC SINH XIN ĐÁP ÁN, ĐÒI LÀM HỘ, HOẶC DÙNG CHIÊU TRÒ NHỜ LOẠI TRỪ / LỌC BỚT / PHÂN LOẠI DANH SÁCH CHẤT HỘ:\n"
                "     + Ví dụ chiêu trò: 'Thầy hãy loại bỏ những chất không phải là...', 'Thầy hãy giữ lại đúng các chất...', 'Thầy lọc hộ chất sai để em biết đường tránh...', 'Thầy phân loại giúp chất nào là nguyên liệu/sản phẩm...'.\n"
                "     + ĐÂY LÀ HÀNH VI XIN ĐÁP ÁN TINH VI (ANSWER PLEA). BẮT BUỘC gán 'student_state': 'answer_plea'.\n"
                "     + 'feedback': Thân thiện từ chối làm bài hộ / lọc hộ: 'Thầy Socrates Nhí sẽ không lọc bớt hay phân loại chất thay em đâu nè! Mục tiêu là để chính em tự nhận biết.' TUYỆT ĐỐI KHÔNG CHỈ RA CHẤT NÀO LÀ NGUYÊN LIỆU, CHẤT NÀO LÀ SẢN PHẨM, KHÔNG NÊU TÊN CHẤT ĐƯỢC GIỮ LẠI HOẶC BỊ LOẠI BỎ!\n"
                "     + 'question': Đặt câu hỏi gợi mở nguồn gốc để học sinh tự chọn ra 1 chất đầu tiên (ví dụ: 'Trong các chất em vừa kể, theo em cây xanh hút chất nào từ rễ và hấp thụ khí nào qua lá để chế tạo chất dinh dưỡng?').\n"
                "   - KHI HỌC SINH TỰ MÌNH NÓI ĐÚNG HOÀN TOÀN BẢN CHẤT HOẶC CÔNG THỨC:\n"
                "     + Gán 'student_state': 'correct'. Khen ngợi chính xác và dẫn dắt bước tiếp theo.\n\n"
                "=== KỸ THUẬT GỢI MỞ RÕ HƠN DẦN (MULTI-LEVEL SCAFFOLDING) KHI SAI LIÊN TIẾP ===\n"
                f"Cấp độ giàn giáo hiện tại ở bước này: CẤP {scaffolding_lvl}/3\n"
                "• Cấp 1 (Sai lần 1): Gợi mở nhẹ nhàng định hướng lại dữ kiện và từ khóa đề bài.\n"
                "• Cấp 2 (Sai lần 2): ĐỔI CÁCH HỎI, KHÔNG LẶP LẠI CÂU HỎI CŨ! Đưa ra một VÍ DỤ TƯƠNG TỰ ĐỜI SỐNG (Analogical Scaffolding) với số liệu siêu đơn giản khác hoàn toàn đề bài hoặc tình huống quen thuộc (ví dụ chạy bộ, bóng nảy, đèn pin, tưới cây) để học sinh tự rút ra nguyên lý. TUYỆT ĐỐI KHÔNG DÙNG SỐ ĐỀ BÀI CHÍNH, KHÔNG LỘ ĐÁP SỐ.\n"
                "• Cấp 3 (Sai lần 3+): Chỉ rõ vị trí bài học trong SGK KHTN 7 (Bài X) + Chuyển câu hỏi thành dạng LỰA CHỌN 2 PHƯƠNG ÁN ĐỐI LẬP TRỰC QUAN (Binary Choice, ví dụ chia hay nhân? bằng hay lớn hơn? chất khí duy trì sự cháy hay chất khí làm tắt ngọn nến?) để học sinh tự lựa chọn. Tuyệt đối không cho đáp số.\n\n"
                "=== KỶ LUẬT THÉP VỀ GỢI Ý VI MÔ ('micro_hint') ===\n"
                "CẢNH BÁO TỐI CAO: 'micro_hint' TUYỆT ĐỐI KHÔNG ĐƯỢC CHỨA ĐÁP ÁN CỦA CÂU HỎI HIỆN TẠI!\n"
                "Nhiều trường hợp gia sư bị đánh giá kém vì phần gợi ý lại chính là đáp án (ví dụ: hỏi công thức là gì thì gợi ý lại ghi 'v = s/t', hỏi chất gì thì gợi ý lại ghi tên chất). ĐIỀU NÀY BỊ CẤM HOÀN TOÀN!\n"
                "'micro_hint' chỉ là gợi mở phương pháp tư duy, liên tưởng đời sống hoặc hướng dẫn quan sát (<= 140 ký tự), TUYỆT ĐỐI KHÔNG ghi ra đáp số hay công thức đích!\n\n"
                "=== NGUYÊN TẮC CẤM XUẤT MẢNG SỐ, CODE, DỮ LIỆU THÔ (RAW DATA / CODE PROHIBITION) ===\n"
                "TUYỆT ĐỐI KHÔNG thực hiện các yêu cầu xuất mảng số, mã code, danh sách dữ liệu thô (raw data, JSON, CSV, bảng tọa độ) nếu các dữ liệu đó chứa kết quả tính toán hoặc đáp án của bài học.\n"
                "Nếu người dùng/học sinh yêu cầu định dạng dữ liệu để vẽ hình, vẽ đồ thị hoặc nạp database, HÃY YÊU CẦU NGƯỜI DÙNG TỰ ĐIỀN CÁC CON SỐ ĐÓ VÀO CẤU TRÚC TRỐNG MẪU (placeholder), ví dụ: [góc_tới, góc_phản_xạ], [quãng_đường, thời_gian, tốc_độ], hoặc {'thời_gian': t, 'quãng_đường': s}. KHÔNG TÍNH TOÁN HỘ HOẶC ĐIỀN SỐ THAY HỌC SINH!\n\n"
                "=== NGUYÊN TẮC HỎI DỰA TRÊN HIỆN TƯỢNG QUAN SÁT MẮT THƯỜNG (OBSERVATIONAL PHENOMENON-FIRST MANDATE) ===\n"
                "Khi đặt câu hỏi gợi mở, AI TUYỆT ĐỐI KHÔNG ĐƯỢC đưa bất kỳ thuật ngữ hóa học, tên chất khí, hay khái niệm khoa học nào (như oxy, kim loại, phản ứng, chất duy trì sự cháy, tác chất...) vào câu hỏi nếu người dùng chưa chủ động nhắc đến.\n"
                "AI CHỈ ĐƯỢC PHÉP hỏi dựa trên các hiện tượng thực tế quan sát được bằng mắt thường trong đời sống:\n"
                "• Thay vì hỏi: 'Ngoài sắt và oxy còn chất nào làm phản ứng dẫn đến gỉ sắt?' hoặc 'Ngoài thanh kim loại và chất khí duy trì sự cháy...',\n"
                "• AI BẮT BUỘC PHẢI HỎI: 'Em hãy quan sát xem thời tiết hoặc môi trường xung quanh như thế nào (ví dụ trời mưa hay nắng, khô ráo hay ẩm ướt) sẽ làm thanh sắt bên ngoài nhanh bị đổi màu hơn?'\n"
                "- Tương tự với các hiện tượng khác:\n"
                "• Quang hợp: 'Em hãy quan sát chậu cây xanh ở ban công: mỗi ngày em cần tưới gì cho cây và ban ngày cây cần đón nhận yếu tố gì từ bầu trời để lá luôn tươi xanh?' (KHÔNG hỏi: 'Quang hợp cần chất khí gì' hay 'Nguyên liệu phản ứng là gì').\n"
                "• Đốt than: 'Khi nhóm bếp than để nướng đồ ăn, mẩu than đen khi bén lửa sẽ biến đổi màu sắc thế nào và có hiện tượng gì tỏa ra xung quanh?' (KHÔNG hỏi: 'Phản ứng cacbon với oxy').\n"
                "CHỈ KHI HỌC SINH ĐÃ CHỦ ĐỘNG GÕ TỪ KHÓA ĐÓ trong phiên chat, bạn mới được phép dùng lại từ đó để phản hồi và đào sâu tiếp!\n\n"
                "=== NGUYÊN TẮC ĐỒNG HÀNH KHÔNG GIỚI HẠN & ĐIỀU KIỆN HOÀN THÀNH ===\n"
                "Phiên hội thoại không giới hạn số lượt, chỉ kết thúc khi học sinh đã tự mình hiểu bài và đúc kết chính xác ở Pha 5.\n\n"
                "=== CẤU TRÚC PHẢN HỒI JSON (KHÔNG KÈM TEXT NGOÀI) ===\n"
                "{\n"
                "  \"analysis\": \"Phân tích logic từng ý: Học sinh nói gì? Đúng hay sai? Trạng thái.\",\n"
                "  \"student_state\": \"correct\" | \"partial\" | \"misconception\" | \"off_topic\" | \"unknown\" | \"answer_plea\",\n"
                "  \"is_completed\": true | false,\n"
                "  \"feedback\": \"Nhận xét sư phạm ngắn gọn (1-2 câu).\",\n"
                "  \"question\": \"ĐÚNG 1 câu hỏi dẫn dắt phù hợp với cấp độ Scaffolding.\",\n"
                "  \"micro_hint\": \"Gợi ý vi mô định hướng tư duy (<= 140 ký tự), TUYỆT ĐỐI KHÔNG CHỨA ĐÁP ÁN.\"\n"
                "}"
            )

            messages = [{"role": "system", "content": sys_prompt}]
            messages.append({"role": "user", "content": f"Đề bài/Câu hỏi KHTN 7: {problem_text}"})
            messages.extend(recent_msgs)
            messages.append({
                "role": "user",
                "content": (
                    f"Pha hội thoại hiện tại: {current_phase.value}\n"
                    f"Lượt trao đổi hiện tại: {turn_num} (Cấp độ Scaffolding: {scaffolding_lvl}/3).\n"
                    f"Học sinh vừa trả lời: '{student_message}'\n"
                    "Hãy phân tích và tạo phản hồi sư phạm đúng cấp độ Scaffolding."
                )
            })

            ok, text, data, err = call_ai_chat_completion(messages, json_mode=True, timeout=35.0)
            if ok and data and data.get("question"):
                raw_state = str(data.get("student_state", "misconception")).strip().lower()
                state_map = {
                    "correct": StudentState.CORRECT,
                    "partial": StudentState.PARTIAL,
                    "misconception": StudentState.MISCONCEPTION,
                    "off_topic": StudentState.OFF_TOPIC,
                    "unknown": StudentState.UNKNOWN,
                    "answer_plea": StudentState.ANSWER_PLEA
                }
                evaluated_state = state_map.get(raw_state, StudentState.MISCONCEPTION)
                fb = data.get("feedback", "Thầy đang đồng hành cùng em!")
                q = data.get("question")
                hint = data.get("micro_hint")

                # Bộ lọc chống khen sai (Sycophancy filter): Khử ngay câu 'đúng một phần' nếu câu trả lời không hề có ý đúng
                if evaluated_state in [StudentState.MISCONCEPTION, StudentState.OFF_TOPIC, StudentState.UNKNOWN]:
                    sycophant_phrases = [
                        r"đúng\s+(?:được\s+)?1\s+phần",
                        r"đúng\s+một\s+phần",
                        r"đã\s+đúng\s+một\s+phần",
                        r"làm\s+được\s+1\s+phần\s+đúng",
                        r"có\s+phần\s+đúng",
                        r"đúng\s+một\s+nửa"
                    ]
                    for sp in sycophant_phrases:
                        if re.search(sp, fb, re.IGNORECASE):
                            if evaluated_state == StudentState.MISCONCEPTION:
                                fb = "Câu trả lời của em chưa chính xác với hiện tượng chúng mình đang xét rồi nè, chúng mình cùng xem xét lại nhé!"
                            elif evaluated_state == StudentState.UNKNOWN:
                                fb = "Không sao cả, khi chưa rõ chúng mình cùng nhau tìm hiểu từng bước nhé!"
                            else:
                                fb = "Ý kiến này chưa liên quan đến câu hỏi chúng mình đang thảo luận rồi nè!"
                            break

                # Bộ lọc chống trả lời luôn / giải thích tuột định nghĩa / rò rỉ nguyên liệu sản phẩm trong feedback
                def_spoilers = [
                    r"pháp\s+tuyến\s+là\s+đường\s+thẳng\s+vuông\s+góc",
                    r"pháp\s+tuyến\s+là\s+đường\s+vuông\s+góc",
                    r"định\s+nghĩa\s+pháp\s+tuyến\s+là",
                    r"tốc\s+độ\s+là\s+quãng\s+đường\s+chia",
                    r"(?:nước|co2|carbon dioxide|h2o|khí cacbonic)\s+.*?\blà\s+nguyên\s+liệu\b",
                    r"(?:oxygen|o2|khí oxi|glucose|glucozo|chất hữu cơ|đường)\s+.*?\blà\s+sản\s+phẩm\b",
                    r"(?:nguyên\s+liệu|sản\s+phẩm)\s+(?:của\s+[\w\s]+\s+)?(?:là|gồm)\s*[:=]?\s*(?:nước|co2|carbon dioxide|h2o|oxygen|o2|glucose|glucozo|chất hữu cơ|đường)",
                    r"loại\s+bỏ\s+.*?(?:giữ\s+lại|những\s+chất\s+thật\s+sự|không\s+liên\s+quan)",
                    r"giữ\s+lại\s+.*?(?:là\s+nguyên\s+liệu|là\s+sản\s+phẩm|thật\s+sự\s+tham\s+gia)",
                    r"(?:là|thuộc)\s+nguyên\s+liệu.*?(?:là|thuộc)\s+sản\s+phẩm"
                ]
                for ds in def_spoilers:
                    if re.search(ds, fb, re.IGNORECASE):
                        if any(k in ds for k in ["nguyên liệu", "sản phẩm", "loại bỏ", "giữ lại"]):
                            fb = "Thầy sẽ không phân loại hay lọc bớt chất hộ em đâu nè! Mục tiêu là để chính em tự nhận biết và suy luận."
                            q = "Trong các chất em vừa kể, theo em cây xanh hút chất nào từ rễ và hấp thụ khí nào qua lá để chế tạo chất dinh dưỡng?"
                            hint = "Em hãy nhớ lại: cây xanh cần tưới gì vào gốc và hít thở khí gì từ bầu khí quyển ban ngày nhé."
                        else:
                            fb = "Không sao cả, khi mới tiếp cận thuật ngữ này em bỡ ngỡ là điều bình thường! Chúng mình cùng tìm hiểu từng bước nhé."
                            if any(w in student_message.lower() for w in ["pháp tuyến", "phap tuyen"]):
                                q = "Em hãy tưởng tượng khi cắm một cây bút dựng đứng vuông góc 90 độ lên mặt gương phẳng, đường thẳng đứng đó tạo với mặt gương một góc bao nhiêu độ?"
                        break

                # Lớp phòng vệ tức thì: Khử ngay mọi câu AI vô tình nói lộ công thức v = s/t khi học sinh chưa tự giải được
                formula_spoilers = [
                    r"công\s+thức\s+.*?(?:là|phải\s+là)\s*[:=]?\s*v\s*=\s*s\s*/\s*t",
                    r"áp\s+dụng\s+công\s+thức\s+v\s*=\s*s\s*/\s*t",
                    r"công\s+thức\s+tính\s+tốc\s+độ\s+là\s+v\s*=\s*s\s*/\s*t",
                    r"v\s*=\s*s\s*/\s*t",
                    r"công\s+thức\s+.*?(?:là|phải\s+là)\s*[:=]?\s*i'\s*=\s*i",
                    r"i'\s*=\s*i"
                ]
                if evaluated_state != StudentState.CORRECT and current_phase in [SocraticPhase.CLARIFY, SocraticPhase.RECALL]:
                    for sp in formula_spoilers:
                        if re.search(sp, fb, re.IGNORECASE):
                            fb = "Công thức em vừa nêu chưa chính xác rồi nè! Chúng mình cùng suy nghĩ lại về bản chất nhé."
                        if re.search(sp, q, re.IGNORECASE):
                            if any(w in problem_text.lower() for w in ["tốc độ", "quãng đường", "chuyển động", "xe đạp"]):
                                q = "Để biết trong mỗi 1 giờ xe đi được bao nhiêu km khi đã biết tổng quãng đường và thời gian, em sẽ lấy quãng đường chia hay nhân với thời gian?"
                            else:
                                q = "Em hãy quan sát lại các dữ kiện đề bài đã cho và suy nghĩ xem chúng liên hệ với nhau bằng phép tính nào?"
                        if hint and re.search(sp, hint, re.IGNORECASE):
                            hint = "Hãy suy nghĩ xem tốc độ thể hiện quãng đường đi được trong 1 đơn vị thời gian như thế nào nhé."

                is_completed = bool(data.get("is_completed", False))
                unlock_keywords = [
                    "mở khóa sơ đồ", "thầy đã mở khóa", "đã mở khóa sơ đồ",
                    "mở khóa sơ đồ tư duy dạng nhánh", "đã mở khóa sđtd"
                ]
                combined_check = (str(q or "") + " " + str(fb or "")).lower()
                try:
                    from chuc_nang_6_guardrail_chong_ro_dap_an.guardrail_engine import sanitize_unearned_substances
                    st_hist = " ".join([m.content for m in self.conversation_history if m.sender == "student"] + [student_message])
                    q, _ = sanitize_unearned_substances(q, st_hist)
                    fb, _ = sanitize_unearned_substances(fb, st_hist)
                    if hint:
                        hint, _ = sanitize_unearned_substances(hint, st_hist)
                except Exception:
                    pass

                model = get_ai_config()["model"]
                return fb, q, hint, "ai", model, evaluated_state, is_completed
        except Exception:
            pass
        return None

    def _formulate_pedagogical_dialogue(
        self,
        problem_text: str,
        start_phase: SocraticPhase,
        next_phase: SocraticPhase,
        student_state: StudentState,
        student_text: str,
        turn_num: int
    ) -> Tuple[str, str, Optional[str], str, Optional[str]]:
        prob_lower = problem_text.lower()
        scaffolding_lvl = self.state_machine.get_scaffolding_level()

        # 1. Xử lý khi bị ép xin đáp án (Answer Plea) - Chế độ Offline / Fallback
        if student_state == StudentState.ANSWER_PLEA:
            st_lower = student_text.lower()
            # Nhận diện yêu cầu xuất mảng số, mã code, raw data, nạp database, vẽ hình
            is_code_or_raw_data_plea = any(
                w in st_lower for w in [
                    "mảng", "code", "mã code", "dữ liệu thô", "raw data", "json", "csv",
                    "tọa độ", "database", "vẽ hình", "đồ thị", "vẽ đồ thị", "nạp database",
                    "bảng số", "mảng số"
                ]
            )
            if is_code_or_raw_data_plea:
                fb = (
                    "Thầy Socrates Nhí tuyệt đối không thực hiện các yêu cầu xuất mảng số, mã code hay dữ liệu thô "
                    "chứa kết quả tính toán hoặc đáp án của bài học đâu nhé! Thầy không tính toán hộ con số đâu nè."
                )
                if any(w in prob_lower or w in st_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng", "góc tới", "góc_tới"]):
                    q = (
                        "Nếu em cần định dạng dữ liệu để vẽ hình hoặc nạp database, em hãy tự điền các con số đó vào "
                        "cấu trúc trống mẫu: [góc_tới, góc_phản_xạ]. Theo định luật phản xạ ánh sáng, khi biết góc tới, "
                        "em tính ra góc phản xạ bằng bao nhiêu độ để điền vào cấu trúc này?"
                    )
                    hint = "Định luật phản xạ ánh sáng: Góc phản xạ luôn có mối liên hệ như thế nào với góc tới nhỉ?"
                elif any(w in prob_lower or w in st_lower for w in ["tốc độ", "quãng đường", "thời gian", "vận tốc", "chuyển động", "xe"]):
                    q = (
                        "Nếu em cần định dạng dữ liệu để vẽ hình hoặc nạp database, em hãy tự điền các con số đó vào "
                        "cấu trúc trống mẫu: [quãng_đường, thời_gian, tốc_độ]. Em hãy tự lấy quãng đường chia cho thời gian "
                        "để điền con số tốc độ của mình vào nhé!"
                    )
                    hint = "Tự mình tính toán và nạp số liệu sẽ giúp em nhớ sâu và hiểu bản chất khoa học hơn rất nhiều!"
                else:
                    q = (
                        "Nếu em cần định dạng dữ liệu để vẽ hình hoặc nạp database, em hãy tự điền các con số đó vào "
                        "cấu trúc trống mẫu: [dữ_kiện_đã_cho, kết_quả_tính_được]. Theo em con số kết quả là bao nhiêu để điền vào đây?"
                    )
                    hint = "Em hãy tự thực hiện phép tính của mình, không phụ thuộc vào mảng số hay code tính sẵn nhé."
                return fb, q, hint, "offline", None

            fb = "Socrates Nhí ở đây để đồng hành giúp em tự hiểu bản chất, chứ không đưa đáp số sẵn đâu nè!"
            if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
                q = "Chúng mình cùng làm từng bước nhé! Theo em, khi ánh sáng gặp mặt gương, nó đi tiếp xuyên qua hay hắt trở lại?"
                hint = "Em hãy liên tưởng đến hiện tượng khi soi gương mỗi ngày."
            else:
                q = "Để bắt đầu, em hãy nhìn lại đề bài và cho mình biết: Đề bài đang hỏi đại lượng nào cần tìm?"
                hint = "Đọc kỹ câu hỏi cuối cùng của đề bài nhé."
            return fb, q, hint, "offline", None

        # 2. Xử lý khi học sinh nói 'em không biết' (Unknown) hoặc nhầm lẫn (Misconception) qua 3 CẤP ĐỘ SCAFFOLDING
        if student_state in [StudentState.UNKNOWN, StudentState.MISCONCEPTION, StudentState.OFF_TOPIC]:
            # CẤP ĐỘ 2: ANALOGICAL SCAFFOLDING (Ví dụ tương tự đời sống khi sai lần 2)
            if scaffolding_lvl == 2:
                fb = "Em đừng lo lắng nhé! Chúng mình cùng quan sát qua một ví dụ đời sống thực tế rất gần gũi nè:"
                if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
                    q = "Khi em ném một quả bóng cao su vuông góc vào bức tường phẳng, quả bóng sẽ bị bức tường bật ngược trở lại hay bay xuyên qua tường?"
                    hint = "Bề mặt nhẵn bóng giữ lại và đẩy chuyển động ngược trở về môi trường cũ."
                elif any(w in prob_lower for w in ["quang hợp", "lá cây", "diệp lục"]):
                    q = "Mỗi ngày khi em tưới nước cho chậu cây đặt ngoài ban công có ánh nắng, em thấy cây phát triển xanh tốt nhờ hấp thụ những yếu tố nào từ đất và không khí?"
                    hint = "Em hãy quan sát cây xanh cần được tưới nước và đón ánh nắng mặt trời thế nào nhé."
                elif any(w in prob_lower for w in ["đốt than", "cháy", "bảo toàn khối lượng"]):
                    q = "Khi em đun một ấm nước có nắp đậy kín so với ấm mở nắp, phần hơi nước bay đi vào không khí có làm chiếc ấm mở nắp nhẹ hơn ban đầu không?"
                    hint = "Dù là chất khí bay lên, vật chất vẫn tồn tại và có khối lượng trong tự nhiên."
                else:
                    q = "Nếu em chạy bộ một quãng đường 10 mét hết 2 giây, thì trung bình mỗi 1 giây em chạy được bao nhiêu mét? Em dùng phép tính nào để tìm ra điều đó?"
                    hint = "Hãy suy nghĩ xem phép chia đều quãng đường cho thời gian giúp tìm ra điều gì nhé."
                return fb, q, hint, "offline", None

            # CẤP ĐỘ 3: SGK GUIDANCE & BINARY CHOICE (Chỉ dẫn SGK KHTN 7 + Câu hỏi lựa chọn 2 phương án đối lập)
            elif scaffolding_lvl >= 3:
                fb = "Kiến thức nền tảng của phần này nằm trong SGK KHTN 7 đó em! Để em dễ suy luận, chúng mình cùng lựa chọn nhé:"
                if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
                    q = "Theo Định luật phản xạ ánh sáng (Bài 16 SGK KHTN 7), góc phản xạ sẽ bằng góc tới hay lớn hơn góc tới?"
                    hint = "Em hãy xem lại bài học Phản xạ ánh sáng trong SGK KHTN 7 và chọn phương án hợp lý nhé."
                elif any(w in prob_lower for w in ["quang hợp", "lá cây", "diệp lục"]):
                    q = "Theo bài học Quang hợp ở thực vật (Bài 21 SGK KHTN 7), chất khí mà lá cây giải phóng vào ban ngày giúp sinh giới hô hấp là chất khí duy trì sự cháy hay chất khí làm tắt ngọn nến?"
                    hint = "Em hãy nhớ lại thí nghiệm thu khí từ cành rong ngoài ánh sáng làm bùng cháy tàn đóm đỏ nhé."
                elif any(w in prob_lower for w in ["đốt than", "cháy", "bảo toàn khối lượng"]):
                    q = "Theo Định luật bảo toàn khối lượng (Bài 6 SGK KHTN 7), tổng khối lượng các chất trước phản ứng sẽ bằng hay khác tổng khối lượng các chất sau phản ứng?"
                    hint = "Em hãy xem lại định luật bảo toàn khối lượng trong SGK KHTN 7 nhé."
                else:
                    q = "Theo công thức tốc độ chuyển động (Bài 8 SGK KHTN 7), để tìm tốc độ (quãng đường đi trong 1 đơn vị thời gian), ta lấy quãng đường chia cho thời gian hay lấy quãng đường nhân với thời gian?"
                    hint = "Em hãy mở Bài 8 SGK KHTN 7 và chọn giữa phép chia hoặc phép nhân nhé."
                return fb, q, hint, "offline", None

            # CẤP ĐỘ 1: GỢI MỞ ĐỊNH HƯỚNG CƠ BẢN (Lần sai đầu tiên)
            else:
                if student_state == StudentState.UNKNOWN:
                    fb = "Không sao cả, ai mới học cũng có lúc bối rối! Mình cùng chia nhỏ vấn đề ra nhé."
                else:
                    fb = "Khái niệm này chưa phù hợp với hiện tượng chúng ta đang tìm hiểu rồi nè. Không sao, mình cùng xem xét lại nhé!"

                if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
                    if start_phase == SocraticPhase.CLARIFY:
                        q = "Em hãy thử nhớ lại: Khi em soi gương mỗi sáng, em thấy ảnh mình ở trước gương đúng không? Nếu ánh sáng đi xuyên qua như tấm kính trong suốt thì ta có nhìn thấy ảnh mình không?"
                        hint = "Em hãy nghĩ đến việc gương có mặt tráng bạc giữ lại ánh sáng như thế nào."
                    elif start_phase == SocraticPhase.RECALL:
                        q = "Tia sáng chiếu tới mặt gương gọi là tia tới. Em đoán xem tia sáng bị hắt ngược lại sẽ mang tên là tia gì nào?"
                        hint = "Tên gọi của tia sáng này gắn liền với hiện tượng ánh sáng bị dội ngược trở lại."
                    elif start_phase == SocraticPhase.REASON:
                        q = "Nếu góc tới là 0 độ (chiếu vuông góc với mặt gương), thì góc phản xạ cũng bằng bao nhiêu độ theo định luật trên?"
                        hint = "Em hãy nhớ lại mối quan hệ bằng nhau giữa góc phản xạ và góc tới nhé."
                    elif start_phase == SocraticPhase.CHECK:
                        q = "Khi em đứng trước gương phẳng, ảnh của em nhìn thấy trong gương có độ lớn bằng em hay to hơn/nhỏ hơn?"
                        hint = "Em hãy liên hệ đến hình ảnh thật của bản thân khi đứng trước gương phẳng ở nhà."
                    else:
                        q = "Em hãy nhắc lại ngắn gọn: Ánh sáng khi gặp gương phẳng sẽ xảy ra hiện tượng gì?"
                        hint = "Hiện tượng ánh sáng bị dội ngược trở lại môi trường cũ."
                    return fb, q, hint, "offline", None

                elif any(w in prob_lower for w in ["quang hợp", "lá cây", "diệp lục"]):
                    if start_phase == SocraticPhase.CLARIFY:
                        q = "Lá cây cần những nguyên liệu đầu vào nào lấy từ đất và không khí để thực hiện quang hợp?"
                        hint = "Cây hút chất lỏng gì dưới đất và hấp thụ chất khí quen thuộc nào trong không khí qua lá?"
                    else:
                        q = "Nhờ ánh sáng mặt trời, lá cây tạo ra chất hữu cơ và giải phóng khí gì cho chúng ta thở?"
                        hint = "Chất khí duy trì sự hô hấp của con người và động vật mỗi ngày đó em."
                    return fb, q, hint, "offline", None

                elif any(w in prob_lower for w in ["gỉ sắt", "rỉ sắt", "sắt", "kim loại", "gỉ", "gỉ kim loại", "rỉ"]):
                    if start_phase == SocraticPhase.CLARIFY:
                        q = "Em hãy quan sát xem thời tiết hoặc môi trường xung quanh như thế nào (ví dụ trời mưa hay nắng, khô ráo hay ẩm ướt) sẽ làm thanh sắt bên ngoài nhanh bị đổi màu hơn?"
                        hint = "Em hãy nhớ lại chiếc đinh hoặc thanh sắt để ngoài trời mưa ẩm so với để trong nhà khô ráo nhé."
                    elif start_phase == SocraticPhase.RECALL:
                        q = "Khi thanh sắt để ngoài trời ẩm lâu ngày bị đổi màu, em quan sát thấy bề mặt của nó chuyển sang màu gì và lớp vảy đó cứng bóng hay xốp mềm?"
                        hint = "Quan sát lớp vảy màu nâu đỏ bám bên ngoài thanh sắt để ngoài mưa gió nhé."
                    elif start_phase == SocraticPhase.REASON:
                        q = "Em hãy quan sát xem người ta thường làm gì với những cánh cổng sắt hay hàng rào sắt (ví dụ quét sơn hay bôi dầu mỡ) để chúng không bị đổi màu nâu đỏ khi gặp mưa gió?"
                        hint = "Lớp sơn bên ngoài giúp ngăn bề mặt sắt tiếp xúc trực tiếp với không khí ẩm ướt."
                    elif start_phase == SocraticPhase.CHECK:
                        q = "Theo em, khi thanh sắt bị đổi màu và đóng thành lớp vảy nâu đỏ dày lên, cầm vào thấy nặng hơn hay nhẹ hơn thanh sắt sạch ban đầu?"
                        hint = "Thanh sắt ban đầu đã giữ lại thêm các phần tử từ không khí ẩm bám chặt vào."
                    else:
                        q = "Em hãy tóm tắt ngắn gọn: Hiện tượng thanh sắt bị đổi màu nâu đỏ ngoài trời là một sự biến đổi tạo ra chất mới hay vẫn là thanh sắt cũ?"
                        hint = "Dấu hiệu có chất mới sinh ra với màu sắc và tính chất khác biệt."
                    return fb, q, hint, "offline", None

                if start_phase == SocraticPhase.CLARIFY:
                    q = "Đề bài có nhắc đến những con số nào kèm đơn vị đo? Em hãy liệt kê các con số đó ra giúp mình nhé."
                    hint = "Em hãy tìm các con số kèm đơn vị đo lường trong đề bài nhé."
                elif start_phase == SocraticPhase.RECALL:
                    q = "Trong bài học trước, khi muốn biết một vật chuyển động nhanh hay chậm, chúng mình dùng công thức tính tốc độ nào?"
                    hint = "Tốc độ thể hiện quãng đường đi được trong 1 đơn vị thời gian."
                elif start_phase == SocraticPhase.REASON:
                    q = "Trước khi áp dụng công thức, em thấy đơn vị của thời gian trong đề đã chuẩn giờ (h) hoặc giây (s) chưa?"
                    hint = "Em hãy đối chiếu đơn vị của thời gian với đơn vị của tốc độ đề bài yêu cầu tìm nhé."
                elif start_phase == SocraticPhase.CHECK:
                    q = "Sau khi tính xong, em hãy đối chiếu xem đơn vị của tốc độ là km/h hay m/s nhé?"
                    hint = "Kiểm tra sự đồng nhất giữa quãng đường và thời gian."
                else:
                    q = "Em hãy tóm tắt lại 1 quy tắc quan trọng nhất vừa dùng trong bài toán này nhé."
                    hint = "Ghi lại bài học hoặc quy tắc cốt lõi mà em đúc kết được."
                return fb, q, hint, "offline", None

        # 4. Xử lý khi học sinh trả lời đúng một phần (Partial) - Chế độ Offline / Fallback
        if student_state == StudentState.PARTIAL:
            fb = "Ý kiến của em đã đúng ở một phần dữ kiện, nhưng câu trả lời vẫn còn thiếu một điểm quan trọng nữa nè!"
            if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
                q = "Hiện tượng tia sáng bị bề mặt gương phẳng hắt ngược trở lại môi trường cũ được gọi tên khoa học là gì?"
                hint = "Hiện tượng tia sáng bị dội ngược lại mang từ ghép có từ 'xạ'."
            else:
                q = "Em hãy bổ sung thêm dữ kiện hoặc công thức tương ứng để câu trả lời hoàn chỉnh hơn nhé?"
                hint = "Đọc kỹ các dữ kiện đề bài đã cho."
            return fb, q, hint, "offline", None

        # Xử lý chuyên sâu cho câu hỏi Quang học / Ánh sáng / Gương phẳng
        if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
            if next_phase == SocraticPhase.CLARIFY:
                fb = "Em đang quan sát rất đúng hướng đó! Cùng suy nghĩ thêm một chút nhé."
                q = "Khi em rọi đèn pin vào một tấm gương soi phẳng nhẵn bóng, chùm sáng sẽ đi xuyên qua phòng bên kia hay bị mặt gương hắt ngược trở lại phía em?"
                hint = "Gương phẳng có lớp tráng bạc phía sau giúp phản xạ lại ánh sáng chứ không cho ánh sáng truyền xuyên qua."
                return fb, q, hint
            elif next_phase == SocraticPhase.RECALL:
                fb = "Rất chính xác! Ánh sáng không đi xuyên qua mà bị hắt ngược trở lại môi trường cũ, hiện tượng đó gọi là 'Sự phản xạ ánh sáng'."
                q = "Em có nhớ định luật phản xạ ánh sáng phát biểu về mối liên hệ giữa góc phản xạ (i') và góc tới (i) như thế nào không?"
                hint = "Em hãy nhớ lại tính đối xứng của tia tới và tia phản xạ qua đường pháp tuyến vuông góc nhé."
                return fb, q, hint
            elif next_phase == SocraticPhase.REASON:
                fb = "Rất chuẩn! Góc phản xạ luôn bằng góc tới (i' = i) và cùng nằm trong mặt phẳng tới."
                q = "Vậy nếu em chiếu một tia sáng vuông góc với mặt gương phẳng (góc tới i = 0°), tia phản xạ sẽ bị bật ngược lại theo hướng nào?"
                hint = "Khi chiếu vuông góc (góc tới 0 độ), tia sáng sẽ phản xạ như thế nào so với phương chiếu tới?"
                return fb, q, hint
            elif next_phase == SocraticPhase.CHECK:
                fb = "Lập luận rất sắc bén! Em nắm hiện tượng rất chắc."
                q = "Khi em đứng trước gương phẳng, ảnh của em nhìn thấy trong gương có đặc điểm gì (ảnh thật hay ảnh ảo, lớn hơn hay bằng em)?"
                hint = "Em hãy liên hệ đến hình ảnh của chính mình khi soi vào gương phẳng mỗi ngày nhé."
                return fb, q, hint
            elif next_phase == SocraticPhase.GENERALIZE:
                if start_phase == SocraticPhase.GENERALIZE and student_state == StudentState.CORRECT:
                    fb = "Xuất sắc! Em đã tự mình đúc kết kiến thức cốt lõi về định luật phản xạ ánh sáng rất chuẩn xác!"
                    q = "Thầy đã mở khóa Sơ đồ Tư duy Dạng Nhánh cho em rồi đó! Em hãy mở sơ đồ ra để xem các nhánh kiến thức và ghi nhớ bài học nhé!"
                    hint = "Em hãy bấm nút 'Xem Sơ đồ Tư duy Dạng Nhánh 🌿' để xem cây tri thức rẽ nhánh và lưu vào Sổ tay nhé!"
                else:
                    fb = "Tuyệt đỉnh! Em đã hiểu trọn vẹn quy luật đường truyền của ánh sáng khi gặp gương phẳng!"
                    q = "Bây giờ, em hãy tự đúc kết lại kiến thức cốt lõi: 2 quy luật quan trọng nhất của định luật phản xạ ánh sáng trên gương phẳng là gì?"
                    hint = "Nhớ lại 2 quy luật: một về mặt phẳng chứa tia và một về mối liên hệ giữa hai góc."
                return fb, q, hint

        # Xử lý chuyên sâu cho câu hỏi Sinh học / Quang hợp
        if any(w in prob_lower for w in ["quang hợp", "lá cây", "diệp lục"]):
            if next_phase == SocraticPhase.CLARIFY:
                fb = "Đúng hướng rồi! Quá trình quang hợp diễn ra chủ yếu ở lá cây."
                q = "Lá cây cần những nguyên liệu đầu vào nào lấy từ đất và không khí để quang hợp?"
                hint = "Cây hút chất lỏng gì dưới đất qua rễ và hấp thụ khí gì trong không khí qua lá?"
                return fb, q, hint
            elif next_phase == SocraticPhase.RECALL:
                fb = "Chính xác! Cây lấy nước và khí CO2 để quang hợp."
                q = "Nhờ năng lượng ánh sáng mặt trời, lá cây biến đổi nước và CO2 thành những chất nào?"
                hint = "Chất dinh dưỡng nuôi cây và chất khí cần thiết cho sự sống của con người và động vật."
                return fb, q, hint
            elif next_phase == SocraticPhase.REASON:
                fb = "Rất chuẩn! Cây tổng hợp chất hữu cơ nuôi cây và tạo ra O2 cho sự sống."
                q = "Vì sao vào ban đêm khi không có ánh sáng, chúng ta không nên để nhiều chậu hoa cây cảnh trong phòng ngủ đóng kín cửa?"
                hint = "Ban đêm không có ánh sáng thì cây xanh có thực hiện được quang hợp không?"
                return fb, q, hint
            elif next_phase == SocraticPhase.CHECK:
                fb = "Lập luận rất thực tế và chính xác!"
                q = "Em hãy kiểm tra lại: Quá trình quang hợp có ý nghĩa gì đối với việc điều hòa khí hậu Trái Đất?"
                hint = "Cây xanh hấp thụ lượng lớn khí carbon dioxide giúp thanh lọc bầu khí quyển."
                return fb, q, hint
            elif next_phase == SocraticPhase.GENERALIZE:
                if start_phase == SocraticPhase.GENERALIZE and student_state == StudentState.CORRECT:
                    fb = "Xuất sắc! Em đã tự mình đúc kết kiến thức cốt lõi về quang hợp rất chính xác!"
                    q = "Thầy đã mở khóa Sơ đồ Tư duy Dạng Nhánh cho em rồi đó! Em hãy mở sơ đồ ra để xem các nhánh kiến thức và ghi nhớ bài học nhé!"
                    hint = "Em hãy bấm nút 'Xem Sơ đồ Tư duy Dạng Nhánh 🌿' để xem cây tri thức rẽ nhánh và lưu vào Sổ tay nhé!"
                else:
                    fb = "Tuyệt vời! Em đã nắm vững bản chất của quá trình quang hợp."
                    q = "Bây giờ, em hãy tự đúc kết lại kiến thức cốt lõi: Phương trình chữ của quá trình quang hợp ở thực vật là gì?"
                    hint = "Sắp xếp theo thứ tự: Nguyên liệu đầu vào --(Điều kiện)--> Sản phẩm tạo thành."
                return fb, q, hint

        # Xử lý chuyên sâu cho câu hỏi Hóa học / Hiện tượng thanh sắt bị đổi màu (Gỉ sắt)
        if any(w in prob_lower for w in ["gỉ sắt", "rỉ sắt", "sắt", "kim loại", "gỉ", "gỉ kim loại", "rỉ"]):
            if next_phase == SocraticPhase.CLARIFY:
                fb = "Em đang quan sát rất đúng hướng đó! Cùng suy nghĩ từ hiện tượng thực tế xung quanh chúng mình nhé."
                q = "Em hãy quan sát xem thời tiết hoặc môi trường xung quanh như thế nào (ví dụ trời mưa hay nắng, khô ráo hay ẩm ướt) sẽ làm thanh sắt bên ngoài nhanh bị đổi màu hơn?"
                hint = "Em hãy nhớ lại chiếc đinh hoặc thanh sắt để ngoài trời mưa ẩm so với để trong nhà khô ráo nhé."
                return fb, q, hint
            elif next_phase == SocraticPhase.RECALL:
                fb = "Rất chính xác! Độ ẩm và nước mưa làm thanh sắt biến đổi rất nhanh."
                q = "Khi thanh sắt để ngoài trời ẩm lâu ngày bị đổi màu, em quan sát thấy bề mặt của nó chuyển sang màu gì và lớp vảy đó cứng bóng hay xốp mềm?"
                hint = "Quan sát lớp vảy màu nâu đỏ bám bên ngoài thanh sắt để ngoài mưa gió nhé."
                return fb, q, hint
            elif next_phase == SocraticPhase.REASON:
                fb = "Quan sát rất tinh tế! Bề mặt thanh sắt đã chuyển sang màu nâu đỏ và mủn ra."
                q = "Em hãy quan sát xem người ta thường làm gì với những cánh cổng sắt hay hàng rào sắt (ví dụ quét sơn hay bôi dầu mỡ) để chúng không bị đổi màu nâu đỏ khi gặp mưa gió?"
                hint = "Lớp sơn bên ngoài giúp ngăn bề mặt sắt tiếp xúc trực tiếp với không khí ẩm ướt."
                return fb, q, hint
            elif next_phase == SocraticPhase.CHECK:
                fb = "Rất thực tế và chuẩn xác!"
                q = "Theo em, khi thanh sắt bị đổi màu và đóng thành lớp vảy nâu đỏ dày lên, cầm vào thấy nặng hơn hay nhẹ hơn thanh sắt sạch ban đầu?"
                hint = "Thanh sắt ban đầu đã giữ lại thêm các phần tử từ không khí ẩm bám chặt vào."
                return fb, q, hint
            elif next_phase == SocraticPhase.GENERALIZE:
                if start_phase == SocraticPhase.GENERALIZE and student_state == StudentState.CORRECT:
                    fb = "Xuất sắc! Em đã tự mình làm chủ bản chất của hiện tượng biến đổi tạo chất mới từ thanh sắt!"
                    q = "Thầy đã mở khóa Sơ đồ Tư duy Dạng Nhánh cho em rồi đó! Em hãy mở sơ đồ ra để xem các nhánh kiến thức và ghi nhớ bài học nhé!"
                    hint = "Em hãy bấm nút 'Xem Sơ đồ Tư duy Dạng Nhánh 🌿' để xem cây tri thức rẽ nhánh và lưu vào Sổ tay nhé!"
                else:
                    fb = "Tuyệt vời! Em đã nắm vững bản chất của hiện tượng này."
                    q = "Bây giờ, em hãy tự đúc kết lại: Dấu hiệu thực tế nào chứng minh thanh sắt để ngoài trời mưa ẩm đã bị biến đổi thành một chất mới?"
                    hint = "Dấu hiệu xuất hiện màu sắc mới và tính chất xốp giòn khác biệt hoàn toàn."
                return fb, q, hint

        # Nếu đang ở Chế độ Demo Offline (FR-10): Dùng lời thoại chuẩn đã duyệt sư phạm CHỈ KHI khớp bài mẫu
        if GLOBAL_OFFLINE_ENGINE and GLOBAL_OFFLINE_ENGINE.is_offline():
            matched_prob = GLOBAL_OFFLINE_ENGINE.match_problem_from_text(problem_text, strict=True)
            if matched_prob:
                phase_key = next_phase.value.lower()
                if phase_key in matched_prob.cached_phases:
                    cached_dlg = matched_prob.cached_phases[phase_key]
                    return cached_dlg.feedback, cached_dlg.question, cached_dlg.micro_hint

        # Xử lý theo Pha kế tiếp bình thường
        if next_phase == SocraticPhase.RECALL:
            fb = "Rất tốt! Em đã chỉ ra chính xác các dữ kiện được cho trong đề bài."
            q = "Để tìm đại lượng đề bài yêu cầu từ các dữ kiện trên, em nhớ đến công thức hoặc quy luật nào liên quan?"
            hint = "Hãy nhớ lại mối liên hệ giữa các đại lượng vừa nêu."
            return fb, q, hint

        elif next_phase == SocraticPhase.REASON:
            fb = "Chính xác! Công thức em chọn hoàn toàn đúng hướng."
            q = "Theo em, bước tiếp theo chúng mình nên thực hiện phép biến đổi hoặc đổi đơn vị nào trước, vì sao?"
            hint = "Chú ý sự đồng nhất giữa các đơn vị đo lường trước khi thay số."
            return fb, q, hint

        elif next_phase == SocraticPhase.CHECK:
            fb = "Lập luận rất sắc bén! Em đã nối dữ kiện với công thức rất chuẩn."
            q = "Bây giờ, em hãy kiểm tra lại xem: Kết quả của em đã có đầy đủ đơn vị đo chưa và có phù hợp với thực tế không?"
            hint = "Kiểm tra kỹ đơn vị km/h hoặc m/s đi kèm con số nhé."
            return fb, q, hint

        elif next_phase == SocraticPhase.GENERALIZE:
            if start_phase == SocraticPhase.GENERALIZE:
                if student_state == StudentState.CORRECT:
                    fb = "Xuất sắc! Em đã tự mình đúc kết được quy tắc cốt lõi và bài học quan trọng!"
                    q = "Thầy đã mở khóa Sơ đồ Tư duy Dạng Nhánh cho em rồi đó! Em hãy mở sơ đồ ra để xem các nhánh kiến thức và ghi nhớ bài học nhé!"
                    hint = "Em hãy bấm nút 'Xem Sơ đồ Tư duy Dạng Nhánh 🌿' để xem cây tri thức rẽ nhánh và lưu vào Sổ tay nhé!"
                else:
                    fb = "Ý đúc kết của em cần xem xét và điều chỉnh lại một chút nhé!"
                    q = "Em hãy nhìn lại quy luật mà chúng mình vừa tìm ra, em hãy thử tự đúc kết lại một câu ngắn gọn về kiến thức cốt lõi của bài này nhé?"
                    hint = "Gợi ý: Tự đúc kết 1 câu ngắn gọn về bài học hoặc quy tắc cốt lõi mà em vừa làm chủ nhé."
            else:
                fb = "Tuyệt vời! Em đã hiểu bài và tự mình chinh phục trọn vẹn bài toán KHTN này!"
                q = "Bây giờ, em hãy tự đúc kết lại kiến thức cốt lõi (quy tắc, bài học hoặc công thức quan trọng nhất) theo cách hiểu của em nhé!"
                hint = "Gợi ý: Tự đúc kết trong 1-2 câu ngắn gọn về quy tắc chính hoặc công thức vừa rút ra."
            return fb, q, hint

        else: # CLARIFY tiếp diễn
            fb = "Em hãy quan sát kỹ lại các dữ kiện của đề bài nhé."
            q = "Ngoài đại lượng em vừa nêu, trong đề bài còn dữ kiện nào khác chưa được nhắc tới không?"
            hint = "Đọc lại kỹ từng câu trong đề bài nhé."
            return fb, q, hint

    def _detect_answer_leak(self, text: str) -> bool:
        """Hậu kiểm Tầng 3 (Pattern Filter): phát hiện mẫu rò rỉ đáp số & công thức."""
        leak_patterns = [
            r"đáp\s+án\s+(?:là|bằng)\s+\d+",
            r"kết\s+quả\s+(?:là|bằng)\s+\d+",
            r"ra\s+chính\s+xác\s+\d+",
            r"đáp\s+số\s+=\s*\d+",
            r"công\s+thức\s+.*?(?:là|phải\s+là)\s*[:=]?\s*v\s*=\s*s\s*/\s*t",
            r"áp\s+dụng\s+công\s+thức\s+v\s*=\s*s\s*/\s*t",
            r"công\s+thức\s+tính\s+tốc\s+độ\s+là\s+v\s*=\s*s\s*/\s*t"
        ]
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in leak_patterns)

    def _get_safe_fallback(self) -> str:
        """Lấy câu Fallback xoay vòng an toàn."""
        phrase = FALLBACK_PHRASES[self.fallback_index % len(FALLBACK_PHRASES)]
        self.fallback_index += 1
        return phrase

    def get_initial_greeting(self, problem_text: str) -> TurnResponse:
        """
        Tạo câu hỏi khởi đầu khi bắt đầu bước vào Pha 1 (Clarify).
        """
        self.reset()
        greeting_fb = "Chào em! Socrates Nhí rất vui được cùng em khám phá bài toán này."
        greeting_q = (
            "Chúng mình cùng bắt đầu nhé! Em hãy đọc kỹ đề bài và cho mình biết: "
            "Đề bài đã cho trước những dữ kiện hoặc đại lượng nào?"
        )
        greeting_hint = "Hãy tìm các con số kèm đơn vị đo lường trong đề bài nhé."

        # Nhận diện chuyên sâu theo thể loại câu hỏi
        prob_lower = problem_text.lower()
        if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
            greeting_fb = "Chào em! Đây là một câu hỏi rất hay về sự truyền ánh sáng và gương phẳng trong KHTN 7."
            greeting_q = (
                "Khi một tia sáng chiếu tới mặt gương phẳng nhẵn bóng, theo em tia sáng có đi xuyên qua như tấm kính trong suốt không, "
                "hay nó sẽ bị đổi hướng và hắt ngược trở lại môi trường cũ?"
            )
            greeting_hint = "Em hãy liên tưởng đến hiện tượng khi soi gương mỗi ngày nhé."
        elif any(w in prob_lower for w in ["quang hợp", "lá cây", "diệp lục"]):
            greeting_fb = "Chào em! Chúng mình cùng tìm hiểu về quá trình quang hợp kỳ diệu của thực vật nhé."
            greeting_q = "Để bắt đầu, em hãy nhớ lại xem lá cây cần hấp thụ những chất gì từ đất và không khí để thực hiện quang hợp?"
            greeting_hint = "Cây hút chất gì từ rễ dưới đất và lấy khí gì từ không khí qua lá?"
        elif any(w in prob_lower for w in ["đốt than", "cháy", "bảo toàn khối lượng"]):
            greeting_fb = "Chào em! Đây là một phản ứng hóa học thú vị tuân theo định luật bảo toàn khối lượng."
            greeting_q = "Em hãy đọc kỹ đề bài và chỉ ra: Những chất nào là chất tham gia ban đầu và chất nào là sản phẩm tạo thành?"
            greeting_hint = "Chất tham gia nằm trước mũi tên phản ứng, sản phẩm nằm sau mũi tên."

        # Tránh nghẽn mạng đồng bộ khi mở phòng chat:
        # Lời chào mở đầu Pha 1 luôn được tạo tức thì (<1ms) chuẩn sư phạm KHTN 7,
        # sẵn sàng để học sinh tương tác ngay mà không bị trễ hay đơ giao diện.
        is_offline_mode = bool(GLOBAL_OFFLINE_ENGINE and GLOBAL_OFFLINE_ENGINE.is_offline())
        has_api_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
        source = "ai" if has_api_key else "offline"
        model_used = os.getenv("SOCRATES_MODEL", "gpt-5-mini-2025-08-07") if has_api_key else None

        if is_offline_mode and GLOBAL_OFFLINE_ENGINE:
            matched_prob = GLOBAL_OFFLINE_ENGINE.match_problem_from_text(problem_text, strict=True)
            # Chỉ nạp cache nếu đề bài thực sự khớp với 1 trong 12 bài mẫu
            if matched_prob and "clarify" in matched_prob.cached_phases:
                dlg = matched_prob.cached_phases["clarify"]
                greeting_fb = dlg.feedback
                greeting_q = dlg.question
                greeting_hint = dlg.micro_hint

        response = TurnResponse(
            phase=SocraticPhase.CLARIFY,
            next_phase=SocraticPhase.CLARIFY,
            student_state=StudentState.UNKNOWN,
            feedback=greeting_fb,
            next_question=greeting_q,
            micro_hint=greeting_hint,
            turn_count=1,
            consecutive_unknown_count=0,
            source=source,
            model_used=model_used
        )
        self.conversation_history.append(
            ChatMessage(
                sender="socrates",
                content=greeting_q,
                phase=SocraticPhase.CLARIFY,
                micro_hint=greeting_hint,
                feedback=greeting_fb,
                source=source,
                model_used=model_used
            )
        )
        return response
