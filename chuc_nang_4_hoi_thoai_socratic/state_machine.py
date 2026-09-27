"""
Module: state_machine.py
Chức năng 4 (FR-04): Bộ điều phối State Machine 5 pha Socratic
Đặc tả: Socrates Nhí v3.0 (Mục 5 - State machine chuyển pha)

Hiện thực hóa toàn bộ ma trận chuyển pha:
- Ma trận 5 Pha × 6 Kiểu câu trả lời
- Ngưỡng tối đa 7 lượt hội thoại
- Ngưỡng tối đa 2 lần 'unknown' liên tiếp (lần 3 hạ độ khó và reset)
- Quy tắc xử lý khi bị ép xin đáp án ('answer_plea': giữ nguyên pha, từ chối nhẹ)
- Quy tắc kẹt ở Pha 3 sau 5 lượt: khép phiên sớm bằng tóm tắt, không lộ đáp số
"""

from typing import Tuple
from .socratic_model import SocraticPhase, StudentState


class SocraticStateMachine:
    """
    Bộ máy chuyển đổi trạng thái sư phạm cho phiên tự học KHTN.
    """
    def __init__(self, max_turns: int = 7):
        self.current_phase: SocraticPhase = SocraticPhase.CLARIFY
        self.turn_count: int = 1
        self.consecutive_unknown_count: int = 0
        self.max_turns: int = max_turns
        self.is_session_closed: bool = False

    def reset(self):
        """Khởi động lại trạng thái ban đầu của phiên."""
        self.current_phase = SocraticPhase.CLARIFY
        self.turn_count = 1
        self.consecutive_unknown_count = 0
        self.is_session_closed = False

    def transition(self, student_state: StudentState) -> Tuple[SocraticPhase, SocraticPhase, str]:
        """
        Thực hiện chuyển pha dựa trên pha hiện tại và kiểu câu trả lời của học sinh.
        Trả về: (Pha bắt đầu lượt, Pha kế tiếp, Chiến lược sư phạm)
        """
        start_phase = self.current_phase

        # 1. Cập nhật bộ đếm 'unknown' liên tiếp
        if student_state == StudentState.UNKNOWN:
            self.consecutive_unknown_count += 1
        else:
            self.consecutive_unknown_count = 0

        # 2. Kiểm tra ngưỡng tối đa 7 lượt (Mục 5.3)
        if self.turn_count >= self.max_turns:
            self.current_phase = SocraticPhase.GENERALIZE
            self.is_session_closed = True
            strategy = "Đạt ngưỡng 7 lượt hội thoại: Chuyển thẳng sang pha generalize để học sinh tự tóm tắt bài học."
            return start_phase, SocraticPhase.GENERALIZE, strategy

        # 3. Kiểm tra kẹt ở Pha 3 sau 5 lượt (Mục 5.3)
        if self.turn_count >= 5 and self.current_phase in [SocraticPhase.CLARIFY, SocraticPhase.RECALL, SocraticPhase.REASON]:
            self.current_phase = SocraticPhase.GENERALIZE
            self.is_session_closed = True
            strategy = "Sau 5 lượt chưa vượt qua lập luận: Khép sớm bằng tự tóm tắt, tuyệt đối không phát đáp án."
            return start_phase, SocraticPhase.GENERALIZE, strategy

        # 4. Xử lý quá 2 lần 'unknown' liên tiếp: từ lần 3 hạ độ khó và reset bộ đếm
        if self.consecutive_unknown_count >= 3:
            self.consecutive_unknown_count = 0
            lowered_phase = self._step_back_phase(self.current_phase)
            self.current_phase = lowered_phase
            strategy = "Unknown liên tiếp lần 3: Hạ độ khó (lùi 1 pha hoặc tách câu hỏi nhỏ) và đặt lại bộ đếm."
            return start_phase, lowered_phase, strategy

        # 5. Tra cứu MA TRẬN CHUYỂN PHA (Mục 5.2)
        next_phase, strategy = self._lookup_matrix(self.current_phase, student_state)
        self.current_phase = next_phase

        if next_phase == SocraticPhase.GENERALIZE and student_state == StudentState.CORRECT:
            self.is_session_closed = True

        return start_phase, next_phase, strategy

    def _lookup_matrix(self, phase: SocraticPhase, state: StudentState) -> Tuple[SocraticPhase, str]:
        """Bảng tra ma trận chuyển pha theo đúng bảng ở mục 5.2 của tài liệu đặc tả."""

        # PHA 1: CLARIFY (Làm rõ)
        if phase == SocraticPhase.CLARIFY:
            if state == StudentState.CORRECT:
                return SocraticPhase.RECALL, "Đúng dữ kiện -> Tiến sang recall: khen cụ thể, hỏi khái niệm liên quan."
            elif state == StudentState.PARTIAL:
                return SocraticPhase.CLARIFY, "Còn thiếu dữ kiện -> Giữ clarify: hỏi sâu thêm 1 dữ kiện còn thiếu."
            elif state == StudentState.UNKNOWN:
                return SocraticPhase.CLARIFY, "Chưa rõ bắt đầu -> Giữ clarify: hỏi câu nhỏ hơn + 1 gợi ý vi mô."
            elif state == StudentState.MISCONCEPTION:
                return SocraticPhase.CLARIFY, "Nhầm dữ kiện -> Giữ clarify: chỉ ra điểm nhầm, hỏi lại dữ kiện gốc."
            else:  # ANSWER_PLEA hoặc OFF_TOPIC
                return SocraticPhase.CLARIFY, "Xin đáp án -> Giữ nguyên clarify: từ chối nhẹ + quay lại dữ kiện đề bài."

        # PHA 2: RECALL (Gợi nhớ)
        elif phase == SocraticPhase.RECALL:
            if state == StudentState.CORRECT:
                return SocraticPhase.REASON, "Đúng công thức -> Tiến sang reason: yêu cầu nối khái niệm với dữ kiện."
            elif state == StudentState.PARTIAL:
                return SocraticPhase.RECALL, "Thiếu đặc điểm -> Giữ recall: gợi thêm 1 đặc điểm còn thiếu của khái niệm."
            elif state == StudentState.UNKNOWN:
                return SocraticPhase.RECALL, "Quên kiến thức -> Giữ recall: gợi ý vi mô + ví dụ đời sống không kèm số."
            elif state == StudentState.MISCONCEPTION:
                return SocraticPhase.CLARIFY, "Nhầm bản chất -> Lùi 1 pha về clarify: làm rõ lại dữ kiện trước."
            else:
                return SocraticPhase.RECALL, "Xin đáp án -> Giữ nguyên recall: từ chối nhẹ + hỏi khái niệm cơ bản."

        # PHA 3: REASON (Lập luận)
        elif phase == SocraticPhase.REASON:
            if state == StudentState.CORRECT:
                return SocraticPhase.CHECK, "Lập luận đúng -> Tiến sang check: yêu cầu tự kiểm tra đơn vị, tính hợp lý."
            elif state == StudentState.PARTIAL:
                return SocraticPhase.REASON, "Chưa đủ bước -> Giữ reason: hỏi 'vì sao' sâu thêm một nấc."
            elif state == StudentState.UNKNOWN:
                return SocraticPhase.REASON, "Bí bước giải -> Giữ reason: hạ độ khó, tách bước lập luận thành 2 câu hỏi nhỏ."
            elif state == StudentState.MISCONCEPTION:
                return SocraticPhase.RECALL, "Nhầm công thức -> Lùi 1 pha về recall: ôn lại khái niệm rồi lập luận lại."
            else:
                return SocraticPhase.REASON, "Xin đáp án -> Giữ nguyên reason: từ chối nhẹ + hỏi bước lập luận nhỏ nhất."

        # PHA 4: CHECK (Kiểm tra)
        elif phase == SocraticPhase.CHECK:
            if state == StudentState.CORRECT:
                return SocraticPhase.GENERALIZE, "Kiểm tra tốt -> Tiến sang generalize: yêu cầu tự tóm tắt quy tắc & lỗi cần tránh."
            elif state == StudentState.PARTIAL:
                return SocraticPhase.CHECK, "Kiểm tra sót -> Giữ check: chỉ đúng phần còn thiếu, yêu cầu kiểm tra nốt."
            elif state == StudentState.UNKNOWN:
                return SocraticPhase.CHECK, "Chưa biết soát -> Giữ check: đưa checklist 2-3 mục (đơn vị, dấu, điều kiện)."
            elif state == StudentState.MISCONCEPTION:
                return SocraticPhase.REASON, "Sai kết quả -> Lùi 1 pha về reason: lập luận lại từ bước có sai sót."
            else:
                return SocraticPhase.CHECK, "Xin đáp án -> Giữ nguyên check: từ chối nhẹ + hỏi cách tự kiểm tra."

        # PHA 5: GENERALIZE (Khái quát)
        else:
            return SocraticPhase.GENERALIZE, "Khép phiên: ghi nhận tóm tắt của học sinh, hiện sơ đồ tư duy hoàn chỉnh."

    def _step_back_phase(self, phase: SocraticPhase) -> SocraticPhase:
        """Lùi 1 pha khi học sinh gặp khó khăn liên tiếp."""
        if phase == SocraticPhase.REASON:
            return SocraticPhase.RECALL
        elif phase == SocraticPhase.RECALL:
            return SocraticPhase.CLARIFY
        elif phase == SocraticPhase.CHECK:
            return SocraticPhase.REASON
        return SocraticPhase.CLARIFY
