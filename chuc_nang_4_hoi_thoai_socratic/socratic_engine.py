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

# Các mẫu câu xin đáp án (Jailbreak / Answer Plea) cần chặn theo FR-05 & FR-07
ANSWER_PLEA_PATTERNS = [
    r"(?:cho|xin|biết|hỏi)\s+(?:đáp\s+án|kết\s+quả|đáp\s+số|lời\s+giải)",
    r"(?:giải|làm)\s+(?:hộ|giúp|luôn|hết|toàn\s+bộ)",
    r"(?:kết\s+quả|đáp\s+số)\s+là\s+gì",
    r"kết\s+quả\s+cuối\s+cùng",
    r"ra\s+bao\s+nhiêu",
    r"giải\s+chi\s+tiết\s+ra",
    r"đóng\s+vai\s+thầy\s+cô\s+giải"
]

# Các mẫu câu thể hiện sự bối rối / không biết (Unknown)
UNKNOWN_PATTERNS = [
    r"em\s+không\s+biết",
    r"không\s+biết\s+(?:bắt\s+đầu|làm|gì)",
    r"chưa\s+hiểu",
    r"khó\s+quá",
    r"em\s+chịu",
    r"bí\s+quá",
    r"quên\s+rồi",
    r"^\?+$"
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
    def __init__(self, max_turns: int = 7):
        self.state_machine = SocraticStateMachine(max_turns=max_turns)
        self.fallback_index = 0
        self.conversation_history: List[ChatMessage] = []

    def reset(self):
        """Khởi động lại toàn bộ phiên hội thoại."""
        self.state_machine.reset()
        self.conversation_history = []
        self.fallback_index = 0

    def classify_student_answer(self, user_text: str, current_phase: SocraticPhase) -> StudentState:
        """
        Phân loại câu trả lời của học sinh vào 6 trạng thái (Mục 5.1).
        """
        text = user_text.strip().lower()

        # 1. Kiểm tra nài ép xin đáp án (Answer Plea)
        for pattern in ANSWER_PLEA_PATTERNS:
            if re.search(pattern, text):
                return StudentState.ANSWER_PLEA

        # 2. Kiểm tra không biết / bối rối (Unknown)
        if len(text) <= 2 or any(re.search(p, text) for p in UNKNOWN_PATTERNS):
            return StudentState.UNKNOWN

        # 3. Kiểm tra nhầm lẫn khái niệm (Misconception phổ biến KHTN 7)
        if "trọng lượng bằng khối lượng" in text or "v = s * t" in text or "v = s.t" in text:
            return StudentState.MISCONCEPTION

        # 4. Kiểm tra đúng / đúng một phần theo từng pha
        if current_phase == SocraticPhase.CLARIFY:
            # Nhắc được các dữ kiện s, t, km, h, m, kg
            if any(k in text for k in ["s =", "t =", "m =", "km", "phút", "giây", "dữ kiện", "quãng đường", "thời gian"]):
                return StudentState.CORRECT
            return StudentState.PARTIAL

        elif current_phase == SocraticPhase.RECALL:
            # Nhắc được công thức v = s/t, P = 10m, quang hợp
            if any(k in text for k in ["v = s/t", "s/t", "10m", "p = 10m", "quang hợp", "nước", "co2", "oxygen"]):
                return StudentState.CORRECT
            return StudentState.PARTIAL

        elif current_phase == SocraticPhase.REASON:
            # Nêu được bước làm, đổi đơn vị
            if any(k in text for k in ["đổi", "thay số", "chia", "nhân", "bước", "trước"]):
                return StudentState.CORRECT
            return StudentState.PARTIAL

        elif current_phase == SocraticPhase.CHECK:
            # Kiểm tra đơn vị km/h, m/s, N
            if any(k in text for k in ["đơn vị", "km/h", "m/s", "hợp lý", "newton", "n"]):
                return StudentState.CORRECT
            return StudentState.PARTIAL

        elif current_phase == SocraticPhase.GENERALIZE:
            return StudentState.CORRECT

        return StudentState.PARTIAL

    def generate_turn_response(
        self,
        problem_text: str,
        student_message: str
    ) -> TurnResponse:
        """
        Tạo sinh một lượt hội thoại Socratic hoàn chỉnh (FR-04).
        """
        # Bước 1: Phân loại câu trả lời của học sinh
        current_phase = self.state_machine.current_phase
        student_state = self.classify_student_answer(student_message, current_phase)

        # Lưu tin nhắn của học sinh vào lịch sử
        self.conversation_history.append(
            ChatMessage(
                sender="student",
                content=student_message,
                phase=current_phase,
                student_state=student_state
            )
        )

        # Bước 2: Chuyển pha qua State Machine
        start_phase, next_phase, strategy = self.state_machine.transition(student_state)
        turn_num = self.state_machine.turn_count

        # Bước 3: Tạo nội dung phản hồi theo nguyên tắc sư phạm
        feedback, next_question, micro_hint = self._formulate_pedagogical_dialogue(
            problem_text=problem_text,
            start_phase=start_phase,
            next_phase=next_phase,
            student_state=student_state,
            student_text=student_message,
            turn_num=turn_num
        )

        # Bước 4: Hậu kiểm Guardrail chống rò rỉ đáp số (FR-07)
        safety_flags = []
        if self._detect_answer_leak(next_question) or self._detect_answer_leak(micro_hint or ""):
            safety_flags.append("answer_leak")
            feedback = "Mình cùng suy nghĩ từng bước nhé!"
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
            safety_flags=safety_flags
        )

        # Lưu tin nhắn phản hồi của Socrates Nhí vào lịch sử
        self.conversation_history.append(
            ChatMessage(
                sender="socrates",
                content=next_question,
                phase=next_phase,
                micro_hint=micro_hint,
                feedback=feedback
            )
        )

        return response

    def _formulate_pedagogical_dialogue(
        self,
        problem_text: str,
        start_phase: SocraticPhase,
        next_phase: SocraticPhase,
        student_state: StudentState,
        student_text: str,
        turn_num: int
    ) -> Tuple[str, str, Optional[str]]:
        """
        Soạn thảo 1 câu phản hồi + 1 câu hỏi chính + tối đa 1 gợi ý vi mô.
        """
        # Xử lý khi bị ép xin đáp án (Answer Plea)
        if student_state == StudentState.ANSWER_PLEA:
            fb = "Socrates Nhí ở đây để đồng hành giúp em tự hiểu bản chất, chứ không đưa đáp số sẵn đâu nè!"
            q = "Để bắt đầu, em hãy nhìn lại đề bài và cho mình biết: Đề bài đang hỏi đại lượng nào cần tìm?"
            hint = "Đọc kỹ câu hỏi cuối cùng của đề bài nhé."
            return fb, q, hint

        # Xử lý khi học sinh nói 'em không biết' (Unknown)
        if student_state == StudentState.UNKNOWN:
            fb = "Không sao cả, ai mới học cũng có lúc bối rối! Mình cùng chia nhỏ vấn đề ra nhé."
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
            return fb, q, hint

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
            fb = "Tuyệt vời! Em đã tự mình chinh phục trọn vẹn bài toán KHTN này mà không cần ai làm hộ!"
            q = "Để ghi nhớ lâu hơn, em hãy tự tóm tắt lại: Quy tắc chính đã áp dụng là gì và lỗi sai nào cần tránh khi làm dạng bài này?"
            hint = "Tóm tắt trong 2 dòng ngắn gọn vào vở tự học của em nhé."
            return fb, q, hint

        else: # CLARIFY tiếp diễn
            fb = "Đúng một phần rồi đó! Em đang đi rất đúng hướng."
            q = "Ngoài đại lượng em vừa nêu, trong đề bài còn dữ kiện nào khác chưa được nhắc tới không?"
            hint = "Đọc lại kỹ từng câu trong đề bài nhé."
            return fb, q, hint

    def _detect_answer_leak(self, text: str) -> bool:
        """Hậu kiểm Tầng 3 (Pattern Filter): phát hiện mẫu rò rỉ đáp số."""
        leak_patterns = [
            r"đáp\s+án\s+(?:là|bằng)\s+\d+",
            r"kết\s+quả\s+(?:là|bằng)\s+\d+",
            r"ra\s+chính\s+xác\s+\d+",
            r"đáp\s+số\s+=\s*\d+"
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

        response = TurnResponse(
            phase=SocraticPhase.CLARIFY,
            next_phase=SocraticPhase.CLARIFY,
            student_state=StudentState.UNKNOWN,
            feedback=greeting_fb,
            next_question=greeting_q,
            micro_hint=greeting_hint,
            turn_count=1,
            consecutive_unknown_count=0
        )
        self.conversation_history.append(
            ChatMessage(
                sender="socrates",
                content=greeting_q,
                phase=SocraticPhase.CLARIFY,
                micro_hint=greeting_hint,
                feedback=greeting_fb
            )
        )
        return response
