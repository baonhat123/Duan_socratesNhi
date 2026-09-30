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
        self.engine = SocraticEngine(unlimited_turns=True)
        self.is_processing = False

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

        # 2. Thẻ gia sư Socrates Nhí đồng hành
        self.mission_card = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.FORUM_ROUNDED, color=ft.Colors.INDIGO_700, size=22),
                    bgcolor=ft.Colors.INDIGO_50,
                    radius=20
                ),
                ft.Column([
                    ft.Text("Gia sư Socrates Nhí 💡 Đồng hành cùng em", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.INDIGO_900),
                    ft.Text(
                        "Socrates Nhí ở đây để cùng em trao đổi và gợi mở từng bước. Em hãy tự tin nêu suy nghĩ của mình nhé!",
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

        self.turn_progress_text = ft.Text("Lượt: 1", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800)
        self.turn_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FORUM_OUTLINED, color=ft.Colors.AMBER_800, size=16),
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
                        ft.Text("Vấn đề / Câu hỏi đang trao đổi:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
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

        # 4. Học sinh chủ động nhập câu trả lời (Đã bỏ dải mớm câu trả lời nhanh)
        # 5. Thanh nhập tin nhắn (Input Bar - Phong cách Capsule Dock Cao cấp)
        self.txt_message = ft.TextField(
            hint_text="Nhập câu trả lời hoặc suy nghĩ của em để trao đổi cùng thầy Socrates...",
            hint_style=ft.TextStyle(color=ft.Colors.GREY_400, size=13),
            expand=True,
            border=ft.InputBorder.NONE,
            content_padding=ft.Padding(14, 10, 14, 10),
            text_size=13,
            color=ft.Colors.GREY_900,
            cursor_color=ft.Colors.INDIGO_700,
            autofocus=True,
            on_submit=self._on_send_click
        )

        self.is_chat_recording = False
        self.btn_mic = ft.Container(
            content=ft.Icon(ft.Icons.MIC_ROUNDED, color=ft.Colors.WHITE, size=18),
            bgcolor=ft.Colors.RED_600,
            width=36,
            height=36,
            border_radius=18,
            alignment=ft.Alignment.CENTER,
            tooltip="Thu âm câu trả lời qua Micro 🎙️",
            on_click=self._toggle_chat_voice_recording
        )

        self.btn_send = ft.Container(
            content=ft.Icon(ft.Icons.ARROW_UPWARD_ROUNDED, color=ft.Colors.WHITE, size=19),
            bgcolor=ft.Colors.INDIGO_600,
            width=36,
            height=36,
            border_radius=18,
            alignment=ft.Alignment.CENTER,
            tooltip="Gửi câu trả lời (Enter)",
            on_click=self._on_send_click
        )

        self.input_bar = ft.Container(
            content=ft.Row([
                ft.Container(width=4),
                ft.Icon(ft.Icons.QUESTION_ANSWER_OUTLINED, color=ft.Colors.INDIGO_400, size=18),
                self.txt_message,
                self.btn_mic,
                self.btn_send,
                ft.Container(width=4)
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(6, 4, 6, 4),
            border_radius=25,
            border=ft.Border.all(1.5, ft.Colors.INDIGO_300),
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 3)),
            on_click=lambda _: self.txt_message.focus()
        )


    def _start_initial_turn(self):
        """Bắt đầu phiên hội thoại bằng câu hỏi gợi mở đầu tiên."""
        init_res = self.engine.get_initial_greeting(self.problem_text)
        self._add_socrates_message(init_res)

    def _on_send_click(self, e):
        """Xử lý khi học sinh gửi tin nhắn (Bất đồng bộ - siêu mượt, không đơ nút)."""
        if getattr(self, "is_processing", False):
            return

        user_text = (self.txt_message.value or "").strip()
        if not user_text:
            return

        self.is_processing = True

        # 1. Xóa nội dung ô nhập và tạm khóa input để tránh click đúp
        self.txt_message.value = ""
        self.txt_message.disabled = True
        if hasattr(self, "btn_send") and self.btn_send:
            self.btn_send.opacity = 0.4

        # 2. Thêm tin nhắn của học sinh vào giao diện ngay lập tức
        self._add_student_message(user_text)

        # 3. Thêm bong bóng 'Đang suy ngẫm' với vòng xoay động và chỉ báo thời gian trực tiếp
        thinking_text = ft.Text("Thầy Socrates đang suy ngẫm phản hồi cho em...", size=12, italic=True, color=ft.Colors.INDIGO_800)
        thinking_bubble = ft.Row(
            [
                ft.Container(
                    content=ft.Row([
                        ft.ProgressRing(width=16, height=16, stroke_width=2.2, color=ft.Colors.INDIGO_600),
                        thinking_text,
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.INDIGO_50,
                    border=ft.Border.all(1, ft.Colors.INDIGO_200),
                    padding=ft.Padding(14, 10, 14, 10),
                    border_radius=ft.BorderRadius(4, 18, 18, 18),
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=8
        )
        self.chat_list.controls.append(thinking_bubble)
        self.page.update()

        # Biến cờ kiểm soát nhịp tim giao diện (Heartbeat Liveness)
        heartbeat_active = [True]

        import threading
        import time

        def heartbeat_worker():
            sec = 0
            while heartbeat_active[0]:
                time.sleep(0.7)
                if not heartbeat_active[0]:
                    break
                sec += 1
                def tick(s=sec):
                    if heartbeat_active[0]:
                        thinking_text.value = f"Thầy Socrates đang suy ngẫm phản hồi cho em... ({s}s)"
                        try:
                            thinking_text.update()
                        except Exception:
                            try:
                                self.page.update()
                            except Exception:
                                pass
                self._safe_ui_call(tick)

        threading.Thread(target=heartbeat_worker, daemon=True).start()

        # 4. Chạy tạo phản hồi trên background thread (Đồng bộ thread-safe mượt mà)
        def worker():
            try:
                response = self.engine.generate_turn_response(
                    problem_text=self.problem_text,
                    student_message=user_text
                )
            except Exception as ex:
                from .socratic_model import TurnResponse, StudentState
                response = TurnResponse(
                    phase=self.engine.state_machine.current_phase,
                    next_phase=self.engine.state_machine.current_phase,
                    student_state=StudentState.UNKNOWN,
                    feedback="Thầy đang lắng nghe em nè!",
                    next_question="Em hãy thử chia sẻ thêm suy nghĩ của mình về câu hỏi nhé?",
                    micro_hint="Đọc kỹ lại đề bài và quan sát hiện tượng.",
                    turn_count=self.engine.state_machine.turn_count,
                    consecutive_unknown_count=0,
                    is_session_closed=False,
                    safety_flags=[],
                    source="offline",
                    model_used=None
                )
            finally:
                heartbeat_active[0] = False

            # Cập nhật giao diện an toàn trực tiếp trên event loop của Flet
            def apply_ui_update():
                # 1. Xóa bong bóng suy ngẫm
                if thinking_bubble in self.chat_list.controls:
                    self.chat_list.controls.remove(thinking_bubble)

                # 2. Cập nhật thanh trạng thái Pha và Số lượt (Không giới hạn)
                phase_label = PHASE_NAMES.get(response.next_phase, str(response.next_phase))
                self.phase_badge_text.value = phase_label
                self.turn_progress_text.value = f"Lượt: {response.turn_count}"

                # 3. Hiển thị phản hồi của Socrates Nhí
                self._add_socrates_message(response, auto_update=False)

                # 4. Kiểm tra nếu phiên đã thực sự hoàn thành (CHỈ KHI học sinh đã hoàn tất Pha 5 và is_session_closed == True)
                if response.is_session_closed:
                    self._show_completion_banner(auto_update=False)
                    if self.on_session_complete:
                        self.on_session_complete(response.to_dict())

                # 5. Mở khóa ô nhập liệu
                self.txt_message.disabled = False
                if hasattr(self, "btn_send") and self.btn_send:
                    self.btn_send.opacity = 1.0
                self.is_processing = False

                # 6. Đẩy toàn bộ thay đổi lên màn hình ngay trong một frame duy nhất
                try:
                    self.page.update()
                except Exception:
                    pass

                try:
                    self.chat_list.scroll_to(offset=-1, duration=150)
                except Exception:
                    pass

            self._safe_ui_call(apply_ui_update)

        if hasattr(self.page, "run_thread") and callable(self.page.run_thread):
            self.page.run_thread(worker)
        else:
            threading.Thread(target=worker, daemon=True).start()

    def _toggle_chat_voice_recording(self, e):
        """Bật/tắt thu âm câu trả lời của học sinh bằng giọng nói trong phòng chat."""
        import os
        import threading
        from chuc_nang_1_nhap_de.voice_service import GLOBAL_AUDIO_RECORDER, transcribe_audio_file

        recorder = GLOBAL_AUDIO_RECORDER
        if not getattr(self, "is_chat_recording", False):
            success, msg = recorder.start_recording()
            if not success:
                self.txt_message.hint_text = f"⚠️ {msg}"
                try:
                    self.page.update()
                except Exception:
                    pass
                return

            self.is_chat_recording = True
            self.btn_mic.bgcolor = ft.Colors.RED_800
            self.btn_mic.content = ft.Icon(ft.Icons.STOP_CIRCLE_ROUNDED, color=ft.Colors.WHITE, size=19)
            self.btn_mic.tooltip = "Bấm để dừng và chuyển giọng nói thành văn bản ⏹️"
            self.txt_message.hint_text = "🎙️ Đang lắng nghe câu trả lời của em... Em đọc to rồi bấm lại nút Micro đỏ để dừng nhé!"
            try:
                self.page.update()
            except Exception:
                pass
        else:
            self.is_chat_recording = False
            self.btn_mic.disabled = True
            self.btn_mic.opacity = 0.6
            self.btn_mic.bgcolor = ft.Colors.AMBER_700
            self.btn_mic.content = ft.Icon(ft.Icons.HOURGLASS_TOP_ROUNDED, color=ft.Colors.WHITE, size=18)
            self.txt_message.hint_text = "⏳ Đang nhận diện giọng nói AI và chuẩn hóa KHTN..."
            try:
                self.page.update()
            except Exception:
                pass

            wav_path = recorder.stop_recording()

            def process_chat_audio():
                transcript = None
                if wav_path:
                    try:
                        transcript = transcribe_audio_file(wav_path)
                    finally:
                        try:
                            if os.path.exists(wav_path):
                                os.remove(wav_path)
                        except Exception:
                            pass

                def update_ui():
                    self.btn_mic.disabled = False
                    self.btn_mic.opacity = 1.0
                    self.btn_mic.bgcolor = ft.Colors.RED_600
                    self.btn_mic.content = ft.Icon(ft.Icons.MIC_ROUNDED, color=ft.Colors.WHITE, size=18)
                    self.btn_mic.tooltip = "Thu âm câu trả lời qua Micro 🎙️"
                    self.txt_message.hint_text = "Nhập câu trả lời hoặc suy nghĩ của em để trao đổi cùng thầy Socrates..."

                    if transcript and transcript.strip():
                        current_val = (self.txt_message.value or "").strip()
                        if current_val:
                            self.txt_message.value = f"{current_val} {transcript.strip()}"
                        else:
                            self.txt_message.value = transcript.strip()
                        try:
                            self.txt_message.focus()
                        except Exception:
                            pass
                    try:
                        self.page.update()
                    except Exception:
                        pass

                self._safe_ui_call(update_ui)

            threading.Thread(target=process_chat_audio, daemon=True).start()

    def _send_quick_reply(self, text: str):
        """Hỗ trợ bấm nút trả lời nhanh."""
        if getattr(self, "is_processing", False):
            return
        self.txt_message.value = text
        self._on_send_click(None)

    def _add_student_message(self, text: str):
        """Thêm bong bóng chat của học sinh (bên phải)."""
        bubble = ft.Row(
            [
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Em 🙋‍♂️", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_100),
                        ], alignment=ft.MainAxisAlignment.END),
                        ft.Text(text, size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.W_400),
                    ], spacing=2),
                    bgcolor=ft.Colors.INDIGO_700,
                    padding=ft.Padding(16, 12, 16, 12),
                    border_radius=ft.BorderRadius(18, 4, 18, 18),
                    shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.18, ft.Colors.INDIGO_700), offset=ft.Offset(0, 2))
                ),
                ft.Container(
                    content=ft.Icon(ft.Icons.PERSON_ROUNDED, color=ft.Colors.WHITE, size=18),
                    bgcolor=ft.Colors.INDIGO_500,
                    width=34,
                    height=34,
                    border_radius=17,
                    alignment=ft.Alignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=8
        )
        self.chat_list.controls.append(bubble)
        self.page.update()

    def _safe_ui_call(self, callback):
        """
        Đảm bảo thực thi callback cập nhật UI ngay trên asyncio event loop của Flet.
        Khắc phục triệt để lỗi Flet Socket Server bị trễ/treo gói tin gửi sang Flutter client
        khi được gọi từ background worker thread (buộc người dùng phải minimize/restore mới hiện).
        """
        try:
            loop = getattr(self.page, "loop", None)
            if loop and loop.is_running():
                loop.call_soon_threadsafe(callback)
                return
        except Exception:
            pass

        try:
            callback()
        except Exception:
            pass

    def _add_socrates_message(self, response: TurnResponse, auto_update: bool = True):
        """
        Thêm bong bóng chat của Socrates Nhí (bên trái).
        Tuân thủ đúng quy tắc sư phạm:
        - 1 câu phản hồi tích cực
        - Đúng 1 câu hỏi chính
        - 1 gợi ý vi mô (mở rộng được)
        """
        inner_elements = []

        # Header bong bóng Socrates Nhí
        source_badge = None
        if getattr(response, "source", "") == "ai":
            model_lbl = getattr(response, "model_used", "") or "Trí tuệ nhân tạo"
            source_badge = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.GREEN_700, size=12),
                    ft.Text(f"AI: {model_lbl}", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800)
                ], spacing=3),
                bgcolor=ft.Colors.GREEN_50,
                padding=ft.Padding(6, 2, 8, 2),
                border_radius=8,
                border=ft.Border.all(0.8, ft.Colors.GREEN_200)
            )
        elif getattr(response, "source", "") == "offline":
            source_badge = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.BOLT_ROUNDED, color=ft.Colors.AMBER_800, size=12),
                    ft.Text("Demo Offline", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
                ], spacing=3),
                bgcolor=ft.Colors.AMBER_50,
                padding=ft.Padding(6, 2, 8, 2),
                border_radius=8,
                border=ft.Border.all(0.8, ft.Colors.AMBER_200)
            )

        header_row_controls = [
            ft.Row([
                ft.Text("Thầy Socrates Nhí 💡", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=4)
        ]
        if source_badge:
            header_row_controls.append(source_badge)

        inner_elements.append(
            ft.Row(header_row_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

        # 1. Nhận xét sư phạm
        if response.feedback:
            st = getattr(response, "student_state", None)
            is_misconcept = st in [StudentState.MISCONCEPTION, StudentState.OFF_TOPIC]
            is_correct = st == StudentState.CORRECT

            fb_icon = ft.Icons.LIGHTBULB_OUTLINE_ROUNDED if is_misconcept else (ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED if is_correct else ft.Icons.AUTO_AWESOME)
            fb_color = ft.Colors.AMBER_800 if is_misconcept else (ft.Colors.TEAL_700 if is_correct else ft.Colors.AMBER_800)
            fb_bg = ft.Colors.AMBER_50 if (is_misconcept or not is_correct) else ft.Colors.TEAL_50
            fb_border = ft.Colors.AMBER_200 if (is_misconcept or not is_correct) else ft.Colors.TEAL_200
            fb_text_color = ft.Colors.AMBER_900 if (is_misconcept or not is_correct) else ft.Colors.TEAL_900

            inner_elements.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(fb_icon, color=fb_color, size=15),
                        ft.Text(response.feedback, size=12, weight=ft.FontWeight.W_500, color=fb_text_color, expand=True)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=fb_bg,
                    padding=ft.Padding(10, 6, 10, 6),
                    border_radius=8,
                    border=ft.Border.all(1, fb_border)
                )
            )

        # 2. Câu hỏi chính của lượt này (Thẻ nổi bật trọng tâm)
        inner_elements.append(
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, color=ft.Colors.INDIGO_700, size=18),
                        padding=ft.Padding(0, 2, 0, 0),
                        alignment=ft.Alignment.TOP_LEFT
                    ),
                    ft.Text(response.next_question, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900, expand=True)
                ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=8),
                bgcolor=ft.Colors.INDIGO_50,
                padding=12,
                border_radius=10,
                border=ft.Border.all(1.2, ft.Colors.INDIGO_200)
            )
        )

        # 3. Gợi ý vi mô (Micro-hint <= 140 ký tự)
        if response.micro_hint:
            hint_box = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.TIPS_AND_UPDATES_OUTLINED, color=ft.Colors.BLUE_800, size=15),
                    ft.Column([
                        ft.Text("Gợi ý suy nghĩ 💡:", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                        ft.Text(response.micro_hint, size=11, color=ft.Colors.BLUE_900, italic=True)
                    ], spacing=1, expand=True)
                ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=8),
                bgcolor=ft.Colors.BLUE_50,
                padding=ft.Padding(10, 7, 10, 7),
                border_radius=8,
                border=ft.Border.all(1, ft.Colors.BLUE_200)
            )
            inner_elements.append(hint_box)

        # 4. Cảnh báo an toàn Guardrail nếu có
        if "answer_leak" in response.safety_flags:
            inner_elements.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SHIELD_ROUNDED, color=ft.Colors.RED_700, size=14),
                        ft.Text("🛡️ Đã kích hoạt Khiên Guardrail: Không rò rỉ đáp án trực tiếp.", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_800)
                    ]),
                    bgcolor=ft.Colors.RED_50,
                    padding=ft.Padding(8, 4, 8, 4),
                    border_radius=6,
                    border=ft.Border.all(1, ft.Colors.RED_200)
                )
            )

        bubble = ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.WHITE, size=18),
                    bgcolor=ft.Colors.AMBER_500,
                    width=34,
                    height=34,
                    border_radius=17,
                    alignment=ft.Alignment.CENTER,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.3, ft.Colors.AMBER_500), offset=ft.Offset(0, 2))
                ),
                ft.Container(
                    content=ft.Column(inner_elements, spacing=8),
                    bgcolor=ft.Colors.WHITE,
                    padding=ft.Padding(14, 12, 14, 12),
                    border_radius=ft.BorderRadius(4, 18, 18, 18),
                    border=ft.Border.all(1, ft.Colors.INDIGO_100),
                    shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=8
        )
        self.chat_list.controls.append(bubble)
        if auto_update:
            try:
                self.page.update()
            except Exception:
                pass

    def _show_completion_banner(self, auto_update: bool = True):
        """Hiển thị thông báo khi khép phiên ở Pha 5 (Generalize) sau khi học sinh đúc kết đạt."""
        btn_open_mindmap = ft.FilledButton(
            "Khám Phá Sơ đồ Tư duy Dạng Nhánh 🌿",
            icon=ft.Icons.WORKSPACE_PREMIUM_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            on_click=lambda _: self.on_session_complete({
                "turn_count": self.engine.state_machine.turn_count,
                "next_phase": "completed"
            }) if self.on_session_complete else None
        )

        banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CELEBRATION_ROUNDED, color=ft.Colors.GREEN_700, size=32),
                ft.Column([
                    ft.Text("Chúc mừng em đã đúc kết bài học thành công! 🎉", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.GREEN_900),
                    ft.Text("Em đã tự đúc kết kiến thức cốt lõi. Sơ đồ Tư duy Dạng Nhánh (SGK KHTN 7) đã được mở khóa!", size=12, color=ft.Colors.GREEN_800)
                ], spacing=2, expand=True),
                btn_open_mindmap
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            bgcolor=ft.Colors.GREEN_50,
            border=ft.Border.all(1.5, ft.Colors.GREEN_500),
            padding=ft.Padding(14, 12, 14, 12),
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_800), offset=ft.Offset(0, 2))
        )
        self.chat_list.controls.append(banner)
        if auto_update:
            try:
                self.page.update()
            except Exception:
                pass

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
                    self.input_bar
                ],
                spacing=8,
                expand=True
            ),
            padding=ft.Padding(15, 10, 15, 15),
            expand=True
        )
