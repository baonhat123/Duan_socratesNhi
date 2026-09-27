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
            clarify_keywords = [
                # Cơ học
                "s =", "t =", "m =", "km", "phút", "giây", "dữ kiện", "quãng đường", "thời gian", "tốc độ", "vận tốc",
                # Quang học (Ánh sáng & Gương)
                "hắt", "bật lại", "phản xạ", "không đi qua", "không xuyên", "đổi hướng", "bị hắt", "dội lại", "ngược lại", "quay lại", "bật ngược",
                # Sinh học (Quang hợp & Tế bào)
                "nước", "h2o", "co2", "cacbonic", "ánh sáng", "diệp lục", "khí", "rễ",
                # Hóa học
                "carbon", "oxi", "oxygen", "caco3", "chất tham gia", "sản phẩm"
            ]
            if any(k in text for k in clarify_keywords):
                return StudentState.CORRECT
            if len(text.split()) >= 3:
                return StudentState.CORRECT
            return StudentState.PARTIAL

        elif current_phase == SocraticPhase.RECALL:
            recall_keywords = [
                # Cơ học
                "v = s/t", "s/t", "10m", "p = 10m", "công thức",
                # Quang học
                "bằng", "bằng nhau", "i' = i", "i = i'", "góc phản xạ bằng góc tới", "phản xạ", "mặt phẳng tới",
                # Sinh học & Hóa học
                "quang hợp", "glucozo", "tinh bột", "bảo toàn", "khối lượng"
            ]
            if any(k in text for k in recall_keywords):
                return StudentState.CORRECT
            if len(text.split()) >= 3:
                return StudentState.CORRECT
            return StudentState.PARTIAL

        elif current_phase == SocraticPhase.REASON:
            reason_keywords = [
                # Cơ học
                "đổi", "thay số", "chia", "nhân", "bước", "trước",
                # Quang học
                "bật lại", "bật ngược", "trùng", "phương cũ", "vuông góc", "0 độ", "0°", "ngược chiều", "thẳng lại", "bật thẳng",
                # Sinh học & Hóa học
                "tổng", "khối lượng", "tăng", "giảm", "phương trình"
            ]
            if any(k in text for k in reason_keywords):
                return StudentState.CORRECT
            if len(text.split()) >= 3:
                return StudentState.CORRECT
            return StudentState.PARTIAL

        elif current_phase == SocraticPhase.CHECK:
            check_keywords = [
                # Cơ học
                "đơn vị", "km/h", "m/s", "hợp lý", "newton", "n",
                # Quang học
                "ảnh ảo", "bằng", "bằng nhau", "bằng vật", "đối xứng", "không hứng được",
                # Sinh học & Hóa học
                "cân bằng", "đúng", "hợp lý", "chính xác"
            ]
            if any(k in text for k in check_keywords):
                return StudentState.CORRECT
            if len(text.split()) >= 2:
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
        student_state = self.classify_student_answer(student_message, current_phase, problem_text=problem_text)

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

        # Bước 4: Hậu kiểm Guardrail chống rò rỉ đáp số 3 Tầng (FR-07)
        safety_flags = []
        if self.guardrail:
            audit_q = self.guardrail.inspect_response(next_question)
            if not audit_q.is_safe:
                safety_flags.extend(audit_q.safety_flags)
                feedback = "Mình cùng suy nghĩ từng bước nhé!"
                next_question = audit_q.sanitized_text
                micro_hint = "Em hãy chú ý các đại lượng đề bài đã cho trước."
            elif micro_hint:
                audit_h = self.guardrail.inspect_response(micro_hint)
                if not audit_h.is_safe:
                    safety_flags.extend(audit_h.safety_flags)
                    micro_hint = "Em hãy chú ý các đại lượng đề bài đã cho trước."
        else:
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
        prob_lower = problem_text.lower()

        # Xử lý khi bị ép xin đáp án (Answer Plea)
        if student_state == StudentState.ANSWER_PLEA:
            fb = "Socrates Nhí ở đây để đồng hành giúp em tự hiểu bản chất, chứ không đưa đáp số sẵn đâu nè!"
            if any(w in prob_lower for w in ["gương", "gương phẳng", "phản xạ", "ánh sáng"]):
                q = "Chúng mình cùng làm từng bước nhé! Theo em, khi ánh sáng gặp mặt gương, nó đi tiếp xuyên qua hay hắt trở lại?"
                hint = "Gợi ý: Mặt gương nhẵn bóng và tráng bạc phía sau."
            else:
                q = "Để bắt đầu, em hãy nhìn lại đề bài và cho mình biết: Đề bài đang hỏi đại lượng nào cần tìm?"
                hint = "Đọc kỹ câu hỏi cuối cùng của đề bài nhé."
            return fb, q, hint

        # Xử lý khi học sinh nói 'em không biết' (Unknown)
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
                return fb, q, hint

            elif any(w in prob_lower for w in ["quang hợp", "lá cây", "diệp lục"]):
                if start_phase == SocraticPhase.CLARIFY:
                    q = "Lá cây cần những nguyên liệu đầu vào nào lấy từ đất và không khí để thực hiện quang hợp?"
                    hint = "Nước (H2O) từ rễ và khí Carbon dioxide (CO2) qua khí khổng của lá."
                else:
                    q = "Nhờ ánh sáng mặt trời, lá cây tạo ra chất hữu cơ và giải phóng khí gì cho chúng ta thở?"
                    hint = "Giải phóng khí Oxygen (O2)."
                return fb, q, hint

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

        # Thử gọi OpenAI API nếu có cấu hình OPENAI_API_KEY
        if os.getenv("OPENAI_API_KEY") and not (GLOBAL_OFFLINE_ENGINE and GLOBAL_OFFLINE_ENGINE.is_offline() and GLOBAL_OFFLINE_ENGINE.match_problem_from_text(problem_text, strict=True)):
            try:
                import json
                from openai import OpenAI
                client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL") or None, api_key=os.getenv("OPENAI_API_KEY"))
                sys_prompt = (
                    "Bạn là Gia sư Socrates Nhí đồng hành cùng học sinh THCS học KHTN 7. "
                    "NGUYÊN TẮC BẮT BUỘC: Tuyệt đối không làm bài hộ hay cho đáp số. "
                    "Hãy phản hồi câu trả lời của học sinh, đưa ra ĐÚNG 1 CÂU HỎI dẫn dắt cho pha tiếp theo và 1 gợi ý vi mô (<= 140 ký tự). "
                    "Trả về JSON: {\"feedback\": str, \"question\": str, \"micro_hint\": str}"
                )
                user_prompt = (
                    f"Bài toán/Câu hỏi: {problem_text}\n"
                    f"Pha tiếp theo: {next_phase.value}\n"
                    f"Trạng thái học sinh: {student_state.value}\n"
                    f"Học sinh vừa nói: '{student_text}'"
                )
                res = client.chat.completions.create(
                    model=os.getenv("SOCRATES_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    timeout=15.0
                )
                data = json.loads(res.choices[0].message.content)
                if data.get("question"):
                    return data.get("feedback", "Rất tốt!"), data.get("question"), data.get("micro_hint")
            except Exception:
                pass

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
                fb = "Tuyệt đỉnh! Em đã hiểu trọn vẹn quy luật đường truyền của ánh sáng khi gặp gương phẳng!"
                q = "Em hãy tóm tắt lại 2 quy luật quan trọng nhất của định luật phản xạ ánh sáng trên gương phẳng nhé."
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
                fb = "Tuyệt vời! Em đã nắm vững bản chất của quá trình quang hợp."
                q = "Em hãy tự đúc kết phương trình chữ của quá trình quang hợp ở thực vật nhé."
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

        # Thử gọi OpenAI API nếu có cấu hình OPENAI_API_KEY
        if os.getenv("OPENAI_API_KEY") and not (GLOBAL_OFFLINE_ENGINE and GLOBAL_OFFLINE_ENGINE.is_offline() and GLOBAL_OFFLINE_ENGINE.match_problem_from_text(problem_text, strict=True)):
            try:
                import json
                from openai import OpenAI
                client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL") or None, api_key=os.getenv("OPENAI_API_KEY"))
                sys_prompt = (
                    "Bạn là Gia sư Socrates Nhí đồng hành cùng học sinh THCS học KHTN 7. "
                    "NGUYÊN TẮC BẮT BUỘC: Tuyệt đối không làm bài hộ hay cho đáp số. "
                    "Hãy chào đón học sinh và đưa ra ĐÚNG 1 CÂU HỎI gợi mở dẫn dắt đầu tiên (Pha 1: Làm rõ hiện tượng/dữ kiện) "
                    "và 1 gợi ý vi mô (<= 140 ký tự). "
                    "Trả về JSON: {\"feedback\": str, \"question\": str, \"micro_hint\": str}"
                )
                res = client.chat.completions.create(
                    model=os.getenv("SOCRATES_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": f"Đề bài/Câu hỏi của học sinh: '{problem_text}'"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    timeout=15.0
                )
                data = json.loads(res.choices[0].message.content)
                if data.get("question"):
                    greeting_fb = data.get("feedback", greeting_fb)
                    greeting_q = data.get("question", greeting_q)
                    greeting_hint = data.get("micro_hint", greeting_hint)
            except Exception:
                pass

        elif GLOBAL_OFFLINE_ENGINE and GLOBAL_OFFLINE_ENGINE.is_offline():
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
