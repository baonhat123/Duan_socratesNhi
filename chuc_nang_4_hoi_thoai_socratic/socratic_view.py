"""
Module: socratic_view.py
Chức năng 4 (FR-04): Giao diện Hội thoại Socratic gợi mở tư duy 5 pha
Đặc tả: Socrates Nhí v3.0 (Tương thích Flet 1.0+)

Giao diện Chat hiện đại, sư phạm và lôi cuốn:
- Huy hiệu Pha Socratic động (Pha 1 -> 5) kèm bộ đếm lượt tiến trình (Lượt x/7).
- Thẻ ghi nhớ đề bài gập/mở để học sinh dễ dàng đối chiếu.
- Bong bóng chat AI: Phản hồi tích cực + Đúng 1 câu hỏi chính + Thẻ mở rộng Gợi ý vi mô.
- Dải nút gợi ý trả lời nhanh 1-chạm (Ví dụ: "Em chưa biết bắt đầu", "Cho em đáp án đi" để test Guardrail).
- Ô nhập liệu tin nhắn bo góc hiện đại kèm nút gửi.
"""

from typing import Optional, Callable
import flet as ft

from .socratic_model import SocraticPhase, StudentState, TurnResponse, ChatMessage, PHASE_NAMES
from .socratic_engine import SocraticEngine


class SocraticChatView:
    """
    Component giao diện Flet cho Chức năng 4: Hội thoại Socratic
    """
    def __init__(
        self,
        page: ft.Page,
        problem_text: str = "",
        on_session_complete: Optional[Callable[[dict], None]] = None,
        is_standalone: bool = False
    ):
        self.page = page
        self.problem_text = problem_text or (
            "Một người đi xe đạp chuyển động đều trên quãng đường thẳng s = 12 km "
            "trong thời gian t = 30 phút. Hãy xác định tốc độ v của người đó theo đơn vị km/h và m/s."
        )
        self.on_session_complete = on_session_complete
        self.is_standalone = is_standalone
        self.engine = SocraticEngine(max_turns=7)

        # Xây dựng giao diện
        self._build_controls()

        # Bắt đầu lượt chào đầu tiên của Pha 1
        self._start_initial_turn()

    def _build_controls(self):
        # 1. Header độc lập (Chỉ hiển thị khi chạy riêng lẻ Chức năng 4)
        self.standalone_header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_600, size=28),
                    ft.Text("Socrates Nhí 💡", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                ]),
                ft.Text("Chức năng 4: Hội thoại Socratic gợi mở tư duy 5 pha (FR-04)", size=13, color=ft.Colors.GREY_700),
                ft.Container(height=5)
            ]),
            visible=self.is_standalone
        )

        # 2. Thẻ chỉ dẫn nhiệm vụ Trạm 4 (Mission Briefing Card)
        self.mission_card = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.FORUM_ROUNDED, color=ft.Colors.INDIGO_700, size=22),
                    bgcolor=ft.Colors.INDIGO_50,
                    radius=20
                ),
                ft.Column([
                    ft.Text("Trạm 4: Hội thoại Gợi mở Socratic 5 Pha", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.INDIGO_900),
                    ft.Text(
                        "Socrates Nhí không đưa đáp án sẵn. Em hãy tự tin trả lời từng câu hỏi gợi mở "
                        "để từng bước tự mình chinh phục bài toán này nhé!",
                        size=12,
                        color=ft.Colors.GREY_700
                    )
                ], spacing=2, expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        # 3. Header & Thanh trạng thái Pha Socratic
        self.phase_badge_text = ft.Text("Pha 1: Làm rõ dữ kiện", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
        self.phase_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PSYCHOLOGY, color=ft.Colors.INDIGO_700, size=16),
                self.phase_badge_text
            ]),
            bgcolor=ft.Colors.INDIGO_50,
            padding=ft.Padding(10, 5, 10, 5),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.INDIGO_200)
        )

        self.turn_progress_text = ft.Text("Lượt: 1/7", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800)
        self.turn_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.TIMER_OUTLINED, color=ft.Colors.AMBER_800, size=16),
                self.turn_progress_text
            ]),
            bgcolor=ft.Colors.AMBER_50,
            padding=ft.Padding(10, 5, 10, 5),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.AMBER_200)
        )

        self.header_row = ft.Row(
            [self.phase_badge, self.turn_badge],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # 2. Thẻ hiển thị nội dung đề bài tham chiếu (Problem Reference Card)
        self.problem_preview_text = ft.Text(self.problem_text, size=12, italic=True, color=ft.Colors.GREY_800)
        self.problem_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=14, color=ft.Colors.INDIGO_700),
                        ft.Text("Đề bài đang học:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                    ]),
                    self.problem_preview_text
                ], spacing=4),
                padding=10
            )
        )

        # 3. Danh sách tin nhắn hội thoại (Chat Stream ListView)
        self.chat_list = ft.ListView(
            expand=True,
            spacing=12,
            auto_scroll=True
        )

        # 4. Dải gợi ý trả lời nhanh 1-chạm (Quick Reply Chips)
        quick_replies = [
            ("Em chưa biết bắt đầu từ đâu", "Em chưa biết bắt đầu từ đâu"),
            ("Cho em đáp án luôn đi", "Cho em đáp án luôn đi"),
            ("Dữ kiện là s = 12 km và t = 30 phút", "Dữ kiện là s = 12 km và t = 30 phút"),
            ("Dùng công thức v = s/t", "Dùng công thức v = s/t"),
            ("Đổi 30 phút = 0.5 h", "Đổi 30 phút = 0.5 h")
        ]
        self.quick_chips = [
            ft.TextButton(
                q[0],
                style=ft.ButtonStyle(
                    padding=6,
                    bgcolor=ft.Colors.INDIGO_50,
                    color=ft.Colors.INDIGO_900
                ),
                on_click=lambda _, text=q[1]: self._send_quick_reply(text)
            )
            for q in quick_replies
        ]
        self.quick_reply_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Gợi ý nhanh:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                    *self.quick_chips
                ],
                wrap=True,
                spacing=5
            ),
            padding=ft.Padding(5, 2, 5, 2)
        )

        # 5. Thanh nhập tin nhắn (Input Bar)
        self.txt_message = ft.TextField(
            hint_text="Nhập câu trả lời hoặc thắc mắc của em...",
            expand=True,
            border_radius=25,
            content_padding=ft.Padding(15, 10, 15, 10),
            on_submit=self._on_send_click
        )

        self.btn_send = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.INDIGO_700,
            tooltip="Gửi câu trả lời",
            on_click=self._on_send_click
        )

        self.input_bar = ft.Container(
            content=ft.Row([self.txt_message, self.btn_send], spacing=8),
            padding=ft.Padding(5, 5, 5, 5)
        )

    def _start_initial_turn(self):
        """Bắt đầu phiên hội thoại bằng câu hỏi gợi mở đầu tiên."""
        init_res = self.engine.get_initial_greeting(self.problem_text)
        self._add_socrates_message(init_res)

    def _on_send_click(self, e):
        """Xử lý khi học sinh gửi tin nhắn."""
        user_text = (self.txt_message.value or "").strip()
        if not user_text:
            return

        self.txt_message.value = ""
        self.page.update()

        # 1. Thêm tin nhắn của học sinh vào giao diện
        self._add_student_message(user_text)

        # 2. Xử lý logic hội thoại Socratic
        response = self.engine.generate_turn_response(
            problem_text=self.problem_text,
            student_message=user_text
        )

        # 3. Cập nhật thanh trạng thái Pha và Số lượt
        phase_label = PHASE_NAMES.get(response.next_phase, str(response.next_phase))
        self.phase_badge_text.value = phase_label
        self.turn_progress_text.value = f"Lượt: {min(response.turn_count, 7)}/7"

        # 4. Hiển thị phản hồi của Socrates Nhí
        self._add_socrates_message(response)

        # 5. Kiểm tra nếu phiên đã kết thúc
        if response.is_session_closed or response.next_phase == SocraticPhase.GENERALIZE:
            self._show_completion_banner()
            if self.on_session_complete:
                self.on_session_complete(response.to_dict())

        self.page.update()

    def _send_quick_reply(self, text: str):
        """Hỗ trợ bấm nút trả lời nhanh."""
        self.txt_message.value = text
        self._on_send_click(None)

    def _add_student_message(self, text: str):
        """Thêm bong bóng chat của học sinh (bên phải)."""
        bubble = ft.Row(
            [
                ft.Container(
                    content=ft.Text(text, size=13, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.INDIGO_700,
                    padding=ft.Padding(14, 10, 14, 10),
                    border_radius=ft.BorderRadius(16, 16, 2, 16)
                ),
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=16),
                    bgcolor=ft.Colors.INDIGO_400,
                    radius=16
                )
            ],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=8
        )
        self.chat_list.controls.append(bubble)
        self.page.update()

    def _add_socrates_message(self, response: TurnResponse):
        """
        Thêm bong bóng chat của Socrates Nhí (bên trái).
        Tuân thủ đúng quy tắc sư phạm:
        - 1 câu phản hồi tích cực
        - Đúng 1 câu hỏi chính
        - 1 gợi ý vi mô (mở rộng được)
        """
        inner_elements = []

        # 1. Nhận xét tích cực
        if response.feedback:
            inner_elements.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.AMBER_700, size=14),
                        ft.Text(response.feedback, size=12, weight=ft.FontWeight.W_500, color=ft.Colors.AMBER_900)
                    ]),
                    bgcolor=ft.Colors.AMBER_50,
                    padding=ft.Padding(8, 4, 8, 4),
                    border_radius=6
                )
            )

        # 2. Câu hỏi chính của lượt này
        inner_elements.append(
            ft.Text(response.next_question, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
        )

        # 3. Gợi ý vi mô (Micro-hint <= 140 ký tự)
        if response.micro_hint:
            hint_box = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.TIPS_AND_UPDATES_OUTLINED, color=ft.Colors.BLUE_700, size=14),
                    ft.Text(f"Gợi ý nhỏ: {response.micro_hint}", size=11, color=ft.Colors.BLUE_900, italic=True)
                ]),
                bgcolor=ft.Colors.BLUE_50,
                padding=ft.Padding(8, 4, 8, 4),
                border_radius=6,
                border=ft.Border.all(1, ft.Colors.BLUE_200)
            )
            inner_elements.append(hint_box)

        # 4. Cảnh báo an toàn Guardrail nếu có
        if "answer_leak" in response.safety_flags:
            inner_elements.append(
                ft.Text("🛡️ Đã kích hoạt Guardrail: Không rò rỉ đáp án.", size=10, color=ft.Colors.RED_600)
            )

        bubble = ft.Row(
            [
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.LIGHTBULB, color=ft.Colors.WHITE, size=16),
                    bgcolor=ft.Colors.AMBER_600,
                    radius=16
                ),
                ft.Container(
                    content=ft.Column(inner_elements, spacing=6),
                    bgcolor=ft.Colors.WHITE,
                    padding=ft.Padding(14, 12, 14, 12),
                    border_radius=ft.BorderRadius(16, 16, 16, 2),
                    border=ft.Border.all(1, ft.Colors.GREY_300)
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=8
        )
        self.chat_list.controls.append(bubble)
        self.page.update()

    def _show_completion_banner(self):
        """Hiển thị thông báo khi khép phiên ở Pha 5 (Generalize)."""
        banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CELEBRATION, color=ft.Colors.GREEN_700, size=24),
                ft.Column([
                    ft.Text("Chúc mừng em đã hoàn thành chu trình gợi mở 5 pha!", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                    ft.Text("Em đã tự lập luận tìm ra cách làm bài mà không cần xem đáp án sẵn.", size=12, color=ft.Colors.GREEN_800)
                ], spacing=2)
            ]),
            bgcolor=ft.Colors.GREEN_50,
            border=ft.Border.all(1, ft.Colors.GREEN_300),
            padding=12,
            border_radius=8
        )
        self.chat_list.controls.append(banner)
        self.page.update()

    def update_problem_text(self, new_text: str):
        """Cập nhật đề bài khi chuyển giao từ Bước 2."""
        self.problem_text = new_text
        self.problem_preview_text.value = new_text
        self.chat_list.controls.clear()
        self._start_initial_turn()

    def build(self) -> ft.Control:
        """Trả về toàn bộ giao diện của khung chat Socratic."""
        return ft.Container(
            content=ft.Column(
                [
                    self.standalone_header,
                    self.mission_card,
                    self.header_row,
                    self.problem_card,
                    ft.Container(
                        content=self.chat_list,
                        expand=True,
                        padding=ft.Padding(12, 12, 12, 12),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=16,
                        border=ft.Border.all(1, ft.Colors.GREY_200)
                    ),
                    self.quick_reply_bar,
                    self.input_bar
                ],
                spacing=8,
                expand=True
            ),
            padding=ft.Padding(15, 10, 15, 15),
            expand=True
        )
