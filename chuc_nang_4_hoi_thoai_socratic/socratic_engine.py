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
    r"cho\s+đáp\s+án"
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
            feedback, next_question, micro_hint, source, model_used, student_state = ai_result
            start_phase, next_phase, strategy = self.state_machine.transition(student_state)
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
        if self.guardrail:
            # 1. Hậu kiểm feedback
            audit_fb = self.guardrail.inspect_response(feedback)
            if not audit_fb.is_safe:
                safety_flags.extend(audit_fb.safety_flags)
                if student_state == StudentState.CORRECT:
                    feedback = "Rất tốt! Thầy ghi nhận suy nghĩ chính xác của em, chúng mình cùng bước tiếp nhé."
                else:
                    feedback = "Thầy đang cùng em tìm hiểu từng bước. Chúng mình cùng suy luận tiếp nào!"

            # 2. Hậu kiểm next_question
            audit_q = self.guardrail.inspect_response(next_question)
            if not audit_q.is_safe:
                safety_flags.extend(audit_q.safety_flags)
                next_question = audit_q.sanitized_text or "Theo em, bước suy luận tiếp theo ta cần làm gì?"
                micro_hint = "Em hãy chú ý mối liên hệ giữa các đại lượng đề bài đã cho."
            elif micro_hint:
                audit_h = self.guardrail.inspect_response(micro_hint)
                if not audit_h.is_safe:
                    safety_flags.extend(audit_h.safety_flags)
                    micro_hint = "Em hãy chú ý các đại lượng đề bài đã cho trước."
        else:
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
    ) -> Optional[Tuple[str, str, Optional[str], str, str, StudentState]]:
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

            sys_prompt = (
                "Bạn là Chuyên gia Khảo thí & Trợ lý Gia sư Sư phạm Socrates Nhí môn Khoa học Tự nhiên 7 (Bộ GD&ĐT Việt Nam).\n"
                "Mô hình tư duy: Phân tích kiểm tra logic khoa học ở cấp độ cao nhất. Tuyệt đối không qua loa, không khen sai, không ba phải.\n\n"
                "=== NGUYÊN TẮC ĐÁNH GIÁ CÂU TRẢ LỜI CỦA HỌC SINH (SIÊU NGHIÊM NGẶT) ===\n"
                "1. BƯỚC PHÂN TÍCH TỪNG Ý ('analysis'):\n"
                "   - Viết trường 'analysis' súc tích (1-2 câu ngắn gọn): Học sinh đã trả lời ý gì? Ý đó có đúng về mặt khoa học không? Kết luận trạng thái.\n"
                "   - TUYỆT ĐỐI CẤM thói khen ngợi ba phải, vuốt ve sáo rỗng hoặc tự tiện nói 'bạn làm được 1 phần đúng' / 'ý của em đã đúng một phần' khi học sinh TRẢ LỜI SAI, đoán mò, hoặc câu trả lời không hề có ý nào đúng về mặt khoa học!\n"
                "   - CHỈ ĐƯỢC GÁN 'student_state': 'partial' KHI VÀ CHỈ KHI học sinh đã nêu ĐƯỢC ÍT NHẤT 1 Ý HOÀN TOÀN CHÍNH XAC VỀ MẶT KHOA HỌC trả lời một phần câu hỏi.\n"
                "   - NẾU HỌC SINH NÊU SAI CÔNG THỨC (ví dụ v = s * t), nêu sai bản chất vật lý (ví dụ ánh sáng đi xuyên qua gương phẳng), hoặc đoán mò vô căn cứ:\n"
                "     + BẮT BUỘC gán 'student_state': 'misconception'.\n"
                "     + 'feedback': Thẳng thắn, lịch sự chỉ rõ câu trả lời chưa đúng, nêu điểm mâu thuẫn để học sinh tự thấy vô lý. TUYỆT ĐỐI KHÔNG KHEN 'đúng một phần'!\n"
                "     + 'question': Đặt ĐÚNG 1 CÂU HỎI dẫn dắt trực quan đời sống giúp học sinh tự suy nghĩ và tự sửa sai.\n"
                "   - NẾU HỌC SINH NÓI LẠC ĐỀ (nói chuyện phiếm, nói từ khóa toán/hình học không liên quan như 'tia phân giác' khi đang học chuyển động/quang học):\n"
                "     + Gán 'student_state': 'off_topic'.\n"
                "     + 'feedback': Nhẹ nhàng nhắc nhở chưa liên quan, kéo học sinh về lại đề bài.\n"
                "   - NẾU HỌC SINH NÓI 'EM KHÔNG BIẾT', 'KHÔNG CÓ', 'CHỊU', bế tắc:\n"
                "     + Gán 'student_state': 'unknown'. Động viên nhẹ nhàng, hạ nhỏ câu hỏi thành tình huống trực quan đời sống.\n"
                "   - NẾU HỌC SINH XIN ĐÁP ÁN, ĐÒI LÀM HỘ:\n"
                "     + Gán 'student_state': 'answer_plea'. Thân thiện từ chối làm bài hộ, khích lệ tự làm.\n"
                "   - KHI HỌC SINH TỰ MÌNH NÓI ĐÚNG HOÀN TOÀN BẢN CHẤT HOẶC CÔNG THỨC:\n"
                "     + Gán 'student_state': 'correct'. Khen ngợi chính xác và dẫn dắt bước tiếp theo.\n\n"
                "2. KỶ LUẬT SƯ PHẠM THÉP (TUYỆT ĐỐI KHÔNG TRẢ LỜI LUÔN, KHÔNG NÓI HỘ ĐỊNH NGHĨA HAY ĐÁP SỐ):\n"
                "   - CẤM NÓI HỘ ĐỊNH NGHĨA HOẶC GIẢI THÍCH TRỌN GÓI CHO HỌC SINH:\n"
                "     + Khi học sinh nói 'em không biết X là gì' (ví dụ: 'em không biết pháp tuyến là gì', 'quang hợp là gì'):\n"
                "     + CẤM viết vào feedback câu định nghĩa như: 'Pháp tuyến là đường thẳng vuông góc...', 'Tốc độ là...', 'Quang hợp là...'.\n"
                "     + Nếu nói luôn định nghĩa hoặc trả lời luôn là VI PHẠM NGUYÊN TẮC SƯ PHẠM NGHIÊM TRỌNG!\n"
                "     + 'feedback' chỉ khích lệ ngắn gọn (1 câu), TUYỆT ĐỐI KHÔNG định nghĩa hộ;\n"
                "     + 'question' phải đặt câu hỏi trực quan liên hệ đời sống (ví dụ cọc cắm vuông góc 90 độ lên sàn) để học sinh TỰ NHẬN RA ĐẶC ĐIỂM và TỰ ĐỊNH NGHĨA!\n"
                "   - CẤM VIẾT RA CÔNG THỨC ĐÍCH: 'v = s/t', 'v = s:t', 's/t' hoặc '24 km/h' khi học sinh CHƯA TỰ MÌNH PHÁT BIỂU ĐƯỢC.\n"
                "   - CẤM TIẾT LỘ CÔNG THỨC trong cả 'feedback', 'question' và 'micro_hint'.\n"
                "   - 'feedback' chỉ dùng để: nhận xét ngắn gọn, chỉ ra mâu thuẫn hoặc động viên. TUYỆT ĐỐI KHÔNG BIẾN FEEDBACK THÀNH NƠI GIẢNG BÀI HAY TRẢ LỜI HỘ!\n\n"
                "3. NGUYÊN TẮC ĐỒNG HÀNH KHÔNG GIỚI HẠN & ĐIỀU KIỆN HOÀN THÀNH:\n"
                "   - PHIÊN HỘI THOẠI KHÔNG GIỚI HẠN SỐ LƯỢT: Không bao giờ được nóng vội đóng phiên. Nếu học sinh chưa hiểu, trả lời chưa chính xác hoặc còn thiếu sót, bạn BẮT BUỘC tiếp tục kiên trì đặt câu hỏi gợi mở trực quan (gần gũi đời sống) để học sinh tự suy nghĩ và sửa sai.\n"
                "   - TUYỆT ĐỐI KHÔNG kết thúc phiên hay chúc mừng hoàn thành sớm khi học sinh chưa hiểu bài hoặc câu trả lời chưa chính xác.\n"
                "   - Khi ở Pha 5 (generalize - Khái quát hóa & Tự đúc kết kiến thức cốt lõi):\n"
                "     + BẮT BUỘC yêu cầu học sinh TỰ ĐÚC KẾT KIẾN THỨC CỐT LÕI (quy tắc, bài học hoặc công thức quan trọng nhất) theo cách hiểu của học sinh.\n"
                "     + Nếu học sinh trả lời chưa đúng hoặc chưa khái quát được bản chất: gán 'student_state': 'misconception' (hoặc 'partial'/'unknown'), chỉ ra điểm mâu thuẫn trong feedback và TIẾP TỤC ĐẶT CÂU HỎI gợi mở để học sinh đúc kết lại.\n"
                "     + CHỈ KHI học sinh đã tự mình đúc kết được bài học/quy tắc cốt lõi một cách chính xác: gán 'student_state': 'correct'. Lúc này 'feedback' khen ngợi học sinh đã tự mình đúc kết kiến thức cốt lõi thành công, và 'question' thông báo: 'Thầy đã mở khóa Sơ đồ Tư duy Dạng Nhánh cho em rồi đó! Em hãy mở sơ đồ ra để xem các nhánh kiến thức và ghi nhớ bài học nhé!'. 'micro_hint' gợi ý: 'Em hãy bấm nút Xem Sơ đồ Tư duy Dạng Nhánh 🌿 để khám phá sơ đồ rẽ nhánh và lưu vào sổ tay nhé!'.\n\n"
                "4. CẤU TRÚC PHẢN HỒI (CHỈ TRẢ VỀ JSON - KHÔNG KÈM TEXT NGOÀI):\n"
                "{\n"
                "  \"analysis\": \"Phân tích logic từng ý: Câu hỏi cần gì? Học sinh nói gì? Có ý nào thực sự đúng khoa học không? Kết luận trạng thái.\",\n"
                "  \"student_state\": \"correct\" | \"partial\" | \"misconception\" | \"off_topic\" | \"unknown\" | \"answer_plea\",\n"
                "  \"feedback\": \"Nhận xét sư phạm ngắn gọn (1-2 câu). Tuyệt đối không trả lời luôn, không nói hộ định nghĩa khái niệm trong feedback.\",\n"
                "  \"question\": \"ĐÚNG 1 câu hỏi gợi mở tiếp theo kết thúc bằng dấu chấm hỏi, không kèm câu hỏi phụ.\",\n"
                "  \"micro_hint\": \"Gợi ý vi mô định hướng tư duy (<= 140 ký tự), không tiết lộ công thức hay đáp số.\"\n"
                "}"
            )

            messages = [{"role": "system", "content": sys_prompt}]
            messages.append({"role": "user", "content": f"Đề bài/Câu hỏi KHTN 7: {problem_text}"})
            messages.extend(recent_msgs)
            messages.append({
                "role": "user",
                "content": (
                    f"Pha hội thoại hiện tại: {current_phase.value}\n"
                    f"Lượt trao đổi hiện tại: {turn_num} (Phiên hội thoại mở, không giới hạn số lượt).\n"
                    f"Học sinh vừa trả lời: '{student_message}'\n"
                    "Hãy thực hiện bước 'analysis' phân tích kỹ lưỡng các ý, đánh giá trạng thái câu trả lời và tạo phản hồi sư phạm."
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

                # Bộ lọc chống trả lời luôn / giải thích tuột định nghĩa trong feedback
                def_spoilers = [
                    r"pháp\s+tuyến\s+là\s+đường\s+thẳng\s+vuông\s+góc",
                    r"pháp\s+tuyến\s+là\s+đường\s+vuông\s+góc",
                    r"định\s+nghĩa\s+pháp\s+tuyến\s+là",
                    r"tốc\s+độ\s+là\s+quãng\s+đường\s+chia"
                ]
                for ds in def_spoilers:
                    if re.search(ds, fb, re.IGNORECASE):
                        fb = "Không sao cả, khi mới tiếp cận thuật ngữ này em bỡ ngỡ là điều bình thường! Chúng mình cùng tìm hiểu từng bước nhé."
                        if any(w in student_message.lower() for w in ["pháp tuyến", "phap tuyen"]):
                            q = "Em hãy tưởng tượng khi cắm một cây bút dựng đứng vuông góc 90 độ lên mặt gương phẳng, đường thẳng đứng đó tạo với mặt gương một góc bao nhiêu độ?"
                            hint = "Hãy chú ý đến góc vuông 90 độ tại điểm tới."
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

                model = get_ai_config()["model"]
                return fb, q, hint, "ai", model, evaluated_state
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

        # 1. Xử lý khi bị ép xin đáp án (Answer Plea) - Chế độ Offline / Fallback
        if student_state == StudentState.ANSWER_PLEA:
            fb = "Socrates Nhí ở đây để đồng hành giúp em tự hiểu bản chất, chứ không đưa đáp số sẵn đâu nè!"
            if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
                q = "Chúng mình cùng làm từng bước nhé! Theo em, khi ánh sáng gặp mặt gương, nó đi tiếp xuyên qua hay hắt trở lại?"
                hint = "Gợi ý: Mặt gương nhẵn bóng và tráng bạc phía sau."
            else:
                q = "Để bắt đầu, em hãy nhìn lại đề bài và cho mình biết: Đề bài đang hỏi đại lượng nào cần tìm?"
                hint = "Đọc kỹ câu hỏi cuối cùng của đề bài nhé."
            return fb, q, hint, "offline", None

        # 2. Xử lý khi học sinh nói 'em không biết' (Unknown) - Chế độ Offline / Fallback
        if student_state == StudentState.UNKNOWN:
            fb = "Không sao cả, ai mới học cũng có lúc bối rối! Mình cùng chia nhỏ vấn đề ra nhé."
            if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
                if start_phase == SocraticPhase.CLARIFY:
                    q = "Em hãy thử nhớ lại: Khi em soi gương mỗi sáng, em thấy ảnh mình ở trước gương đúng không? Nếu ánh sáng đi xuyên qua như tấm kính trong suốt thì ta có nhìn thấy ảnh mình không?"
                    hint = "Gương soi giữ lại và hắt ánh sáng trở lại mắt ta."
                elif start_phase == SocraticPhase.RECALL:
                    q = "Tia sáng chiếu tới mặt gương gọi là tia tới. Em đoán xem tia sáng bị hắt ngược lại sẽ mang tên là tia gì nào?"
                    hint = "Đó là tia phản xạ, và góc phản xạ luôn bằng góc tới đấy."
                elif start_phase == SocraticPhase.REASON:
                    q = "Nếu góc tới là 0 độ (chiếu vuông góc với mặt gương), thì góc phản xạ cũng bằng bao nhiêu độ theo định luật trên?"
                    hint = "Góc phản xạ i' = i = 0 độ, tức là tia sáng bật thẳng ngược trở lại theo phương cũ."
                elif start_phase == SocraticPhase.CHECK:
                    q = "Khi em đứng trước gương phẳng, ảnh của em nhìn thấy trong gương có độ lớn bằng em hay to hơn/nhỏ hơn?"
                    hint = "Ảnh trong gương phẳng có độ lớn bằng đúng vật thật."
                else:
                    q = "Em hãy nhắc lại ngắn gọn: Ánh sáng khi gặp gương phẳng sẽ xảy ra hiện tượng gì?"
                    hint = "Hiện tượng phản xạ ánh sáng (bị hắt ngược trở lại)."
                return fb, q, hint, "offline", None

            elif any(w in prob_lower for w in ["quang hợp", "lá cây", "diệp lục"]):
                if start_phase == SocraticPhase.CLARIFY:
                    q = "Lá cây cần những nguyên liệu đầu vào nào lấy từ đất và không khí để thực hiện quang hợp?"
                    hint = "Nước (H2O) từ rễ và khí Carbon dioxide (CO2) qua khí khổng của lá."
                else:
                    q = "Nhờ ánh sáng mặt trời, lá cây tạo ra chất hữu cơ và giải phóng khí gì cho chúng ta thở?"
                    hint = "Giải phóng khí Oxygen (O2)."
                return fb, q, hint, "offline", None

            if start_phase == SocraticPhase.CLARIFY:
                q = "Đề bài có nhắc đến những con số nào kèm đơn vị đo? Em hãy liệt kê các con số đó ra giúp mình nhé."
                hint = "Ví dụ: quãng đường là bao nhiêu km, thời gian là bao nhiêu phút?"
            elif start_phase == SocraticPhase.RECALL:
                q = "Trong bài học trước, khi muốn biết một vật chuyển động nhanh hay chậm, chúng mình dùng công thức tính tốc độ nào?"
                hint = "Tốc độ bằng quãng đường chia cho thời gian."
            elif start_phase == SocraticPhase.REASON:
                q = "Trước khi áp dụng công thức, em thấy đơn vị của thời gian trong đề đã chuẩn giờ (h) hoặc giây (s) chưa?"
                hint = "Nếu đề cho thời gian là 30 phút thì đổi ra giờ bằng bao nhiêu?"
            elif start_phase == SocraticPhase.CHECK:
                q = "Sau khi tính xong, em hãy đối chiếu xem đơn vị của tốc độ là km/h hay m/s nhé?"
                hint = "Quãng đường km chia thời gian giờ sẽ ra km/h."
            else:
                q = "Em hãy tóm tắt lại 1 công thức quan trọng nhất vừa dùng trong bài toán này nhé."
                hint = "Viết lại công thức tổng quát mà em ghi nhớ."
            return fb, q, hint, "offline", None

        # 3. Xử lý khi học sinh nhầm lẫn hoặc lạc đề (Misconception / Off-Topic) - Chế độ Offline / Fallback
        if student_state in [StudentState.MISCONCEPTION, StudentState.OFF_TOPIC]:
            fb = "Khái niệm này chưa phù hợp với hiện tượng chúng ta đang tìm hiểu rồi nè. Không sao, mình cùng xem xét lại nhé!"
            if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
                q = "Khi chiếu một chùm sáng vào tấm gương phẳng nhẵn bóng, tia sáng sẽ đi xuyên qua luôn hay bị bề mặt gương hắt ngược trở lại?"
                hint = "Mặt sau của gương phẳng thường được tráng một lớp bạc để phản chiếu ánh sáng."
            elif any(w in prob_lower for w in ["quang hợp", "lá cây", "diệp lục"]):
                q = "Để quang hợp, cây xanh chủ yếu sử dụng lá để hấp thụ ánh sáng và chất khí nào từ không khí?"
                hint = "Khí này có công thức hóa học là CO2."
            else:
                q = "Em hãy nhìn lại đề bài: Đề bài đang cho những dữ kiện nào và muốn chúng ta tìm đại lượng gì?"
                hint = "Xác định rõ dữ kiện cho trước và đại lượng cần tìm."
            return fb, q, hint, "offline", None

        # 4. Xử lý khi học sinh trả lời đúng một phần (Partial) - Chế độ Offline / Fallback
        if student_state == StudentState.PARTIAL:
            fb = "Ý kiến của em đã đúng ở một phần dữ kiện, nhưng câu trả lời vẫn còn thiếu một điểm quan trọng nữa nè!"
            if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
                q = "Hiện tượng tia sáng bị bề mặt gương phẳng hắt ngược trở lại môi trường cũ được gọi tên khoa học là gì?"
                hint = "Hiện tượng 'phản xạ' ánh sáng."
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
                hint = "Góc phản xạ i' luôn bằng góc tới i (i' = i)."
                return fb, q, hint
            elif next_phase == SocraticPhase.REASON:
                fb = "Rất chuẩn! Góc phản xạ luôn bằng góc tới (i' = i) và cùng nằm trong mặt phẳng tới."
                q = "Vậy nếu em chiếu một tia sáng vuông góc với mặt gương phẳng (góc tới i = 0°), tia phản xạ sẽ bị bật ngược lại theo hướng nào?"
                hint = "Tia sáng sẽ bị bật thẳng ngược trở lại theo đúng phương truyền tới."
                return fb, q, hint
            elif next_phase == SocraticPhase.CHECK:
                fb = "Lập luận rất sắc bén! Em nắm hiện tượng rất chắc."
                q = "Khi em đứng trước gương phẳng, ảnh của em nhìn thấy trong gương có đặc điểm gì (ảnh thật hay ảnh ảo, lớn hơn hay bằng em)?"
                hint = "Ảnh trong gương phẳng là ảnh ảo, không hứng được trên màn và có độ lớn bằng đúng vật."
                return fb, q, hint
            elif next_phase == SocraticPhase.GENERALIZE:
                if start_phase == SocraticPhase.GENERALIZE and student_state == StudentState.CORRECT:
                    fb = "Xuất sắc! Em đã tự mình đúc kết kiến thức cốt lõi về định luật phản xạ ánh sáng rất chuẩn xác!"
                    q = "Thầy đã mở khóa Sơ đồ Tư duy Dạng Nhánh cho em rồi đó! Em hãy mở sơ đồ ra để xem các nhánh kiến thức và ghi nhớ bài học nhé!"
                    hint = "Em hãy bấm nút 'Xem Sơ đồ Tư duy Dạng Nhánh 🌿' để xem cây tri thức rẽ nhánh và lưu vào Sổ tay nhé!"
                else:
                    fb = "Tuyệt đỉnh! Em đã hiểu trọn vẹn quy luật đường truyền của ánh sáng khi gặp gương phẳng!"
                    q = "Bây giờ, em hãy tự đúc kết lại kiến thức cốt lõi: 2 quy luật quan trọng nhất của định luật phản xạ ánh sáng trên gương phẳng là gì?"
                    hint = "1. Tia phản xạ nằm trong mặt phẳng tới; 2. Góc phản xạ bằng góc tới (i' = i)."
                return fb, q, hint

        # Xử lý chuyên sâu cho câu hỏi Sinh học / Quang hợp
        if any(w in prob_lower for w in ["quang hợp", "lá cây", "diệp lục"]):
            if next_phase == SocraticPhase.CLARIFY:
                fb = "Đúng hướng rồi! Quá trình quang hợp diễn ra chủ yếu ở lá cây."
                q = "Lá cây cần những nguyên liệu đầu vào nào lấy từ đất và không khí để quang hợp?"
                hint = "Nước từ rễ và khí Carbon dioxide (CO2) qua khí khổng của lá."
                return fb, q, hint
            elif next_phase == SocraticPhase.RECALL:
                fb = "Chính xác! Cây lấy nước và khí CO2 để quang hợp."
                q = "Nhờ năng lượng ánh sáng mặt trời, lá cây biến đổi nước và CO2 thành những chất nào?"
                hint = "Tạo ra chất hữu cơ (Glucose/tinh bột) và giải phóng khí Oxygen (O2)."
                return fb, q, hint
            elif next_phase == SocraticPhase.REASON:
                fb = "Rất chuẩn! Cây tổng hợp chất hữu cơ nuôi cây và tạo ra O2 cho sự sống."
                q = "Vì sao vào ban đêm khi không có ánh sáng, chúng ta không nên để nhiều chậu hoa cây cảnh trong phòng ngủ đóng kín cửa?"
                hint = "Ban đêm không có ánh sáng để quang hợp, cây chỉ hô hấp hút O2 và thải CO2."
                return fb, q, hint
            elif next_phase == SocraticPhase.CHECK:
                fb = "Lập luận rất thực tế và chính xác!"
                q = "Em hãy kiểm tra lại: Quá trình quang hợp có ý nghĩa gì đối với việc điều hòa khí hậu Trái Đất?"
                hint = "Quang hợp giúp giảm hiệu ứng nhà kính bằng cách hấp thụ bớt khí CO2."
                return fb, q, hint
            elif next_phase == SocraticPhase.GENERALIZE:
                if start_phase == SocraticPhase.GENERALIZE and student_state == StudentState.CORRECT:
                    fb = "Xuất sắc! Em đã tự mình đúc kết kiến thức cốt lõi về quang hợp rất chính xác!"
                    q = "Thầy đã mở khóa Sơ đồ Tư duy Dạng Nhánh cho em rồi đó! Em hãy mở sơ đồ ra để xem các nhánh kiến thức và ghi nhớ bài học nhé!"
                    hint = "Em hãy bấm nút 'Xem Sơ đồ Tư duy Dạng Nhánh 🌿' để xem cây tri thức rẽ nhánh và lưu vào Sổ tay nhé!"
                else:
                    fb = "Tuyệt vời! Em đã nắm vững bản chất của quá trình quang hợp."
                    q = "Bây giờ, em hãy tự đúc kết lại kiến thức cốt lõi: Phương trình chữ của quá trình quang hợp ở thực vật là gì?"
                    hint = "Nước + Carbon dioxide + Ánh sáng -> Chất hữu cơ + Oxygen."
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
                    hint = "Gợi ý: Tự đúc kết 1 câu về công thức hoặc bài học quan trọng nhất (ví dụ: v = s / t)."
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
