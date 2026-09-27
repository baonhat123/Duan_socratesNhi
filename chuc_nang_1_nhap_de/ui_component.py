"""
Module: ui_component.py
Chức năng 1 (FR-01): Giao diện Nhập đề bài (Phiên bản UI 2.0 Thân thiện Học sinh)
Đặc tả: Socrates Nhí v3.0 (Tương thích Flet 1.0+)

Nâng cấp giao diện:
- Thiết kế chuẩn Ed-Tech thân thiện với học sinh THCS (màu sắc hài hòa, card bo góc, đổ bóng mềm).
- Bộ chuyển đổi 3 chế độ (Gõ chữ / Chụp ảnh / Bài mẫu KHTN) dạng thẻ tương tác sinh động.
- Khu vực tải ảnh dạng Dropzone cao cấp, hiển thị xem trước ảnh với badge dung lượng trực quan.
- Thẻ bài mẫu KHTN 7 chia theo mạch kiến thức có icon và màu sắc đặc trưng.
- Đã khắc phục triệt để lỗi Service FilePicker trong Flet 1.0.
"""

from pathlib import Path
from typing import Callable, Optional
import flet as ft

from .input_model import ProblemInput, InputType
from .validator import (
    process_image_input,
    process_text_input,
    process_sample_input,
    MAX_FILE_SIZE_BYTES
)
from .sample_bank import get_all_samples, get_sample_by_id, get_samples_by_strand
from .voice_service import (
    process_voice_input,
    normalize_spoken_khtn,
    get_demo_voice_presets
)




class ProblemInputView:
    """
    Component giao diện Flet cho Chức năng 1: Nhập đề bài (Giao diện 2.0)
    """
    def __init__(
        self,
        page: ft.Page,
        on_confirm: Optional[Callable[[ProblemInput], None]] = None,
        is_standalone: bool = False
    ):
        self.page = page
        self.on_confirm = on_confirm
        self.is_standalone = is_standalone
        self.current_input: Optional[ProblemInput] = None
        self.active_mode = "text"  # "text", "image", "sample"
        self.selected_sample_id: Optional[str] = "VL01"
        self.sample_filter_strand: str = "Tất cả"

        # Thiết lập FilePicker đúng chuẩn Service trong Flet 1.0 (Tuyệt đối không đưa vào overlay)
        self.file_picker = ft.FilePicker(on_result=self._on_file_selected)
        if hasattr(self.page, "services") and self.page.services is not None:
            if self.file_picker not in self.page.services:
                self.page.services.append(self.file_picker)

        # Xây dựng giao diện
        self._build_controls()


    def _build_controls(self):
        # 1. Header độc lập (Chỉ hiển thị khi chạy riêng lẻ Chức năng 1)
        self.standalone_header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_600, size=28),
                    ft.Text("Socrates Nhí 💡", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                ]),
                ft.Text("Chức năng 1: Tiếp nhận đề bài Khoa học tự nhiên THCS (FR-01)", size=13, color=ft.Colors.GREY_700),
                ft.Container(height=5)
            ]),
            visible=self.is_standalone
        )

        # 2. Hướng dẫn thân thiện cho học sinh
        self.welcome_banner = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.AMBER_900, size=18),
                    bgcolor=ft.Colors.AMBER_100,
                    radius=16
                ),
                ft.Column([
                    ft.Text("Chào em! Em muốn nhập bài tập KHTN theo cách nào?", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.INDIGO_900),
                    ft.Text("Em có thể tự gõ nội dung, tải ảnh chụp từ sách/vở, hoặc thử ngay với bài tập mẫu có sẵn.", size=12, color=ft.Colors.GREY_700)
                ], spacing=2, expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        # 3. Ba thẻ lựa chọn phương thức nhập (Interactive Mode Cards)
        self.btn_mode_text = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.EDIT_NOTE_ROUNDED, size=20, color=ft.Colors.INDIGO_700),
                ft.Text("1. Tự gõ đề bài", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.INDIGO_900)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.INDIGO_50,
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=10,
            border=ft.Border.all(2, ft.Colors.INDIGO_600),
            on_click=lambda _: self._switch_mode("text"),
            expand=True
        )

        self.btn_mode_image = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CAMERA_ALT_OUTLINED, size=20, color=ft.Colors.GREY_700),
                ft.Text("2. Tải ảnh đề (≤ 5MB)", weight=ft.FontWeight.W_500, size=13, color=ft.Colors.GREY_800)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            on_click=lambda _: self._switch_mode("image"),
            expand=True
        )

        self.btn_mode_sample = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_STORIES_OUTLINED, size=20, color=ft.Colors.GREY_700),
                ft.Text("3. Bài mẫu KHTN 7", weight=ft.FontWeight.W_500, size=13, color=ft.Colors.GREY_800)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            on_click=lambda _: self._switch_mode("sample"),
            expand=True
        )

        self.btn_mode_voice = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.MIC_OUTLINED, size=20, color=ft.Colors.GREY_700),
                ft.Text("4. Giọng nói 🎙️", weight=ft.FontWeight.W_500, size=13, color=ft.Colors.GREY_800)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            on_click=lambda _: self._switch_mode("voice"),
            expand=True
        )

        self.mode_row = ft.Row([self.btn_mode_text, self.btn_mode_image, self.btn_mode_sample, self.btn_mode_voice], spacing=10)


        # 4. KHU VỰC 1: Tự gõ đề bài
        self.txt_content = ft.TextField(
            hint_text="Nhập đề bài của em vào đây (Ví dụ: Một người đi xe đạp với tốc độ 12 km/h trong thời gian 30 phút...)",
            multiline=True,
            min_lines=6,
            max_lines=10,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            content_padding=15,
            on_change=self._on_text_change
        )
        self.char_count_text = ft.Text("0 ký tự", size=11, color=ft.Colors.GREY_500)

        self.text_container = ft.Container(
            content=ft.Column([
                self.txt_content,
                ft.Row([
                    ft.Text("💡 Mẹo: Em có thể gõ công thức như v = s/t hoặc đơn vị km/h, m/s bình thường.", size=11, color=ft.Colors.GREY_600, italic=True),
                    self.char_count_text
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=6),
            visible=True
        )

        # 5. KHU VỰC 2: Tải ảnh bài tập (Dropzone thẩm mỹ)
        self.btn_select_file = ft.FilledButton(
            "Chọn tệp ảnh từ máy tính",
            icon=ft.Icons.FILE_UPLOAD_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE, padding=16),
            on_click=lambda _: self.file_picker.pick_files(
                dialog_title="Chọn ảnh bài tập KHTN (JPG/PNG, tối đa 5MB)",
                allowed_extensions=["jpg", "jpeg", "png"]
            )
        )
        self.img_preview = ft.Image(src="", visible=False, fit=ft.BoxFit.CONTAIN, border_radius=8)
        self.img_info_text = ft.Text("Chưa chọn tệp ảnh nào (Chấp nhận JPG, PNG • Tối đa 5 MB)", size=12, color=ft.Colors.GREY_600)
        self.btn_clear_image = ft.TextButton("Bỏ chọn ảnh", icon=ft.Icons.DELETE_OUTLINE, visible=False, on_click=self._on_clear_image)

        self.image_container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.CircleAvatar(
                            content=ft.Icon(ft.Icons.CLOUD_UPLOAD_ROUNDED, size=32, color=ft.Colors.INDIGO_600),
                            bgcolor=ft.Colors.INDIGO_50,
                            radius=30
                        ),
                        ft.Text("Tải ảnh chụp đề bài từ sách hoặc vở bài tập", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.INDIGO_900),
                        ft.Text("Yêu cầu: Ảnh chụp rõ nét, đủ ánh sáng, không bị nhòe chữ • Dung lượng ≤ 5 MB", size=12, color=ft.Colors.GREY_600),
                        ft.Container(height=6),
                        self.btn_select_file
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    alignment=ft.Alignment.CENTER,
                    padding=25,
                    border=ft.Border.all(1.5, ft.Colors.INDIGO_200),
                    border_radius=16,
                    bgcolor=ft.Colors.WHITE
                ),
                ft.Row([self.img_info_text, self.btn_clear_image], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(content=self.img_preview, alignment=ft.Alignment.CENTER)
            ], spacing=8),
            visible=False
        )

        # 6. KHU VỰC 3: Chọn bài mẫu KHTN 7 (Đầy đủ 12 bài chuẩn 3 mạch)
        self.sample_cards_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=270)
        self.filter_chips_row = ft.Row(spacing=8, wrap=True)
        self._build_sample_section()

        self.sample_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Ngân hàng 12 bài tập mẫu KHTN 7 chuẩn SGK:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                    self.filter_chips_row
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(
                    content=self.sample_cards_column,
                    border=ft.Border.all(1, ft.Colors.INDIGO_100),
                    border_radius=12,
                    padding=8,
                    bgcolor=ft.Colors.GREY_50
                )
            ], spacing=8),
            visible=False
        )

        # 6B. KHU VỰC 4: Đọc đề bài bằng giọng nói (Voice-to-Text)
        self.is_voice_recording = False
        self.txt_voice_transcript = ft.TextField(
            hint_text="Lời nói của em sẽ xuất hiện ở đây... Em có thể đọc trực tiếp đề bài hoặc thử nhanh với câu nói mẫu bên dưới.",
            multiline=True,
            min_lines=4,
            max_lines=7,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            content_padding=15
        )
        self.voice_status_text = ft.Text("Nhấn vào Micro để bắt đầu nói đề bài KHTN của em nhé!", size=12, color=ft.Colors.GREY_700)
        self.voice_mic_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.MIC_ROUNDED, color=ft.Colors.WHITE, size=24),
                ft.Text("Bắt đầu nói 🎙️", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.RED_600,
            padding=ft.Padding(18, 12, 18, 12),
            border_radius=25,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.3, ft.Colors.RED_600), offset=ft.Offset(0, 3)),
            on_click=self._toggle_voice_recording
        )

        preset_chips = []
        for p in get_demo_voice_presets():
            chip = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.RECORD_VOICE_OVER_ROUNDED, size=14, color=ft.Colors.INDIGO_700),
                    ft.Text(p["title"], size=11, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_900)
                ], spacing=4),
                bgcolor=ft.Colors.INDIGO_50,
                border=ft.Border.all(1, ft.Colors.INDIGO_200),
                padding=ft.Padding(8, 4, 8, 4),
                border_radius=12,
                tooltip="Bấm để phát âm câu mẫu thử nghiệm",
                on_click=lambda _, text=p["raw_speech"]: self._apply_voice_preset(text)
            )
            preset_chips.append(chip)

        self.voice_container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Row([self.voice_mic_btn], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=4),
                        ft.Row([self.voice_status_text], alignment=ft.MainAxisAlignment.CENTER),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.RED_50,
                    padding=16,
                    border_radius=14,
                    border=ft.Border.all(1, ft.Colors.RED_200)
                ),
                ft.Text("Văn bản nhận diện từ giọng nói (tự động chuẩn hóa công thức KHTN):", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                self.txt_voice_transcript,
                ft.Column([
                    ft.Text("Hoặc thử nhanh với các câu phát âm KHTN mẫu:", size=11, color=ft.Colors.GREY_600),
                    ft.Row(preset_chips, spacing=6, wrap=True)
                ], spacing=4)
            ], spacing=8),
            visible=False
        )

        # 7. Banner bảo vệ quyền riêng tư PII (Thiết kế nhẹ nhàng)
        self.privacy_card = ft.Container(

            content=ft.Row([
                ft.Icon(ft.Icons.SECURITY_ROUNDED, color=ft.Colors.BLUE_700, size=18),
                ft.Text(
                    "Socrates Nhí ẩn danh 100%: Em hãy an tâm học tập, ứng dụng không thu thập tên, trường, lớp hay số điện thoại của em.",
                    size=12,
                    color=ft.Colors.BLUE_900,
                    expand=True
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.BLUE_50,
            padding=10,
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.BLUE_100)
        )

        # 8. Hộp cảnh báo lỗi
        self.alert_text = ft.Text("", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.RED_900)
        self.alert_box = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_700, size=18),
                self.alert_text
            ]),
            bgcolor=ft.Colors.RED_50,
            border=ft.Border.all(1, ft.Colors.RED_200),
            padding=10,
            border_radius=8,
            visible=False
        )

        # 9. Nút hành động chính
        self.btn_confirm = ft.FilledButton(
            "Hỏi Gia sư Socrates Nhí ngay 💬",
            icon=ft.Icons.CHAT_BUBBLE_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.INDIGO_700,
                color=ft.Colors.WHITE,
                padding=20
            ),
            on_click=self._on_confirm_click
        )

    def _switch_mode(self, mode: str):
        """Chuyển đổi giao diện giữa 4 tab nhập liệu (Chữ / Ảnh / Mẫu / Giọng nói)."""
        self.active_mode = mode

        # Cập nhật style nút chọn
        tabs = [
            ("text", self.btn_mode_text),
            ("image", self.btn_mode_image),
            ("sample", self.btn_mode_sample),
            ("voice", self.btn_mode_voice)
        ]
        for m, btn in tabs:
            if m == mode:
                btn.bgcolor = ft.Colors.INDIGO_50
                btn.border = ft.Border.all(2, ft.Colors.INDIGO_600)
                btn.content.controls[0].color = ft.Colors.INDIGO_700
                btn.content.controls[1].color = ft.Colors.INDIGO_900
                btn.content.controls[1].weight = ft.FontWeight.BOLD
            else:
                btn.bgcolor = ft.Colors.WHITE
                btn.border = ft.Border.all(1, ft.Colors.GREY_300)
                btn.content.controls[0].color = ft.Colors.GREY_700
                btn.content.controls[1].color = ft.Colors.GREY_800
                btn.content.controls[1].weight = ft.FontWeight.W_500

        if mode == "text":
            self.btn_confirm.text = "Hỏi Gia sư Socrates Nhí ngay 💬"
            self.btn_confirm.icon = ft.Icons.CHAT_BUBBLE_ROUNDED
        elif mode == "image":
            self.btn_confirm.text = "Tiếp tục nhận diện chữ từ ảnh 📷"
            self.btn_confirm.icon = ft.Icons.ARROW_FORWARD_ROUNDED
        elif mode == "sample":
            self.btn_confirm.text = "Khám phá bài học này cùng Gia sư 🚀"
            self.btn_confirm.icon = ft.Icons.AUTO_AWESOME_ROUNDED
        elif mode == "voice":
            self.btn_confirm.text = "Gửi đề bài qua giọng nói 🎙️"
            self.btn_confirm.icon = ft.Icons.RECORD_VOICE_OVER_ROUNDED

        self.text_container.visible = (mode == "text")
        self.image_container.visible = (mode == "image")
        self.sample_container.visible = (mode == "sample")
        self.voice_container.visible = (mode == "voice")
        self.alert_box.visible = False
        self.page.update()

    def _build_sample_section(self):
        """Xây dựng bộ lọc và danh sách thẻ bài mẫu 12 bài KHTN 7."""
        # 1. Bộ lọc Mạch kiến thức
        filter_tabs = [
            ("Tất cả", "Tất cả (12)"),
            ("Vật lý", "Vật lý (4)"),
            ("Hóa học", "Hóa học (4)"),
            ("Sinh học", "Sinh học (4)")
        ]
        self.filter_chips_row.controls.clear()
        for strand_key, label in filter_tabs:
            is_active = (self.sample_filter_strand == strand_key)
            chip = ft.Container(
                content=ft.Text(
                    label,
                    size=11,
                    weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500,
                    color=ft.Colors.WHITE if is_active else ft.Colors.INDIGO_900
                ),
                bgcolor=ft.Colors.INDIGO_600 if is_active else ft.Colors.WHITE,
                border=ft.Border.all(1, ft.Colors.INDIGO_600 if is_active else ft.Colors.GREY_300),
                padding=ft.Padding(10, 4, 10, 4),
                border_radius=16,
                on_click=lambda _, sk=strand_key: self._on_filter_strand_click(sk)
            )
            self.filter_chips_row.controls.append(chip)

        # 2. Thẻ bài mẫu theo mạch kiến thức
        filtered = get_samples_by_strand(self.sample_filter_strand)
        self.sample_cards_column.controls.clear()

        for s in filtered:
            sid = s["id"]
            is_selected = (self.selected_sample_id == sid)
            strand_short = s.get("strand_short", "KHTN")
            if strand_short == "Vật lý":
                tag_bg, tag_color = ft.Colors.BLUE_50, ft.Colors.BLUE_700
            elif strand_short == "Hóa học":
                tag_bg, tag_color = ft.Colors.AMBER_50, ft.Colors.AMBER_900
            else:
                tag_bg, tag_color = ft.Colors.GREEN_50, ft.Colors.GREEN_800

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(f"{sid} • {strand_short}", size=11, weight=ft.FontWeight.BOLD, color=tag_color),
                                bgcolor=tag_bg,
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=4
                            ),
                            ft.Container(
                                content=ft.Text(f"Độ khó: {s['difficulty']}", size=10, color=ft.Colors.GREY_700),
                                bgcolor=ft.Colors.GREY_100,
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=4
                            )
                        ], spacing=6),
                        ft.Text("✓ Đang chọn" if is_selected else "", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(s["title"], weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.INDIGO_900),
                    ft.Text(s["content"], size=11, color=ft.Colors.GREY_700, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Row([
                        ft.Text(f"💡 {', '.join(s['concepts'])}", size=10, color=ft.Colors.INDIGO_700, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Row([
                            ft.OutlinedButton(
                                "Tùy chỉnh đề ✏️",
                                style=ft.ButtonStyle(padding=6),
                                on_click=lambda _, sid=sid: self._customize_sample(sid)
                            ),
                            ft.FilledButton(
                                "Hỏi Gia sư ngay 🚀",
                                style=ft.ButtonStyle(padding=8, bgcolor=ft.Colors.INDIGO_600),
                                on_click=lambda _, sid=sid: self._confirm_sample_immediately(sid)
                            )
                        ], spacing=6)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], spacing=4),
                bgcolor=ft.Colors.INDIGO_50 if is_selected else ft.Colors.WHITE,
                padding=10,
                border_radius=10,
                border=ft.Border.all(1.5 if is_selected else 1, ft.Colors.INDIGO_500 if is_selected else ft.Colors.GREY_200),
                on_click=lambda _, sid=sid: self._on_sample_card_click(sid)
            )
            self.sample_cards_column.controls.append(card)

    def _on_filter_strand_click(self, strand_key: str):
        """Lọc bài mẫu theo mạch kiến thức."""
        self.sample_filter_strand = strand_key
        self._build_sample_section()
        self.page.update()

    def _on_sample_card_click(self, sample_id: str):
        """Chọn bài mẫu và xem trước nội dung."""
        self.selected_sample_id = sample_id
        sample = get_sample_by_id(sample_id)
        self.txt_content.value = sample["content"]
        self._build_sample_section()
        self.page.update()

    def _customize_sample(self, sample_id: str):
        """Chuyển bài mẫu sang chế độ gõ văn bản để học sinh tùy chỉnh đề bài."""
        self.selected_sample_id = sample_id
        sample = get_sample_by_id(sample_id)
        self.txt_content.value = sample["content"]
        self._switch_mode("text")
        self._on_text_change(None)

    def _confirm_sample_immediately(self, sample_id: str):
        """Bắt đầu phiên học ngay với bài tập mẫu đã chọn."""
        self.selected_sample_id = sample_id
        final_input = process_sample_input(sample_id)
        final_input.is_confirmed = True
        self.current_input = final_input
        if self.on_confirm:
            self.on_confirm(final_input)

    def _select_sample(self, sample_id: str):
        """Bí danh tương thích ngược."""
        self._customize_sample(sample_id)

    def _toggle_voice_recording(self, e):
        """Bật/tắt trạng thái thu âm giọng nói và chuẩn hóa thuật ngữ KHTN."""
        self.is_voice_recording = not self.is_voice_recording
        if self.is_voice_recording:
            self.voice_mic_btn.bgcolor = ft.Colors.RED_800
            self.voice_mic_btn.content.controls[1].value = "Đang lắng nghe... (Bấm để dừng ⏹️)"
            self.voice_status_text.value = "🎙️ Đang ghi nhận giọng nói của em... Em có thể đọc to rõ đề bài KHTN nhé!"
            self.voice_status_text.color = ft.Colors.RED_700
        else:
            self.voice_mic_btn.bgcolor = ft.Colors.RED_600
            self.voice_mic_btn.content.controls[1].value = "Bắt đầu nói 🎙️"
            if self.txt_voice_transcript.value:
                norm = normalize_spoken_khtn(self.txt_voice_transcript.value)
                self.txt_voice_transcript.value = norm
                self.voice_status_text.value = "✅ Đã nhận diện và chuẩn hóa thuật ngữ KHTN từ giọng nói!"
                self.voice_status_text.color = ft.Colors.GREEN_700
            else:
                self.voice_status_text.value = "Đã dừng. Em có thể đọc lại hoặc bấm chọn câu nói mẫu bên dưới."
                self.voice_status_text.color = ft.Colors.GREY_700
        self.page.update()

    def _apply_voice_preset(self, text: str):
        """Áp dụng câu nói mẫu phát âm tiếng Việt và tự động chuẩn hóa KHTN."""
        normalized = normalize_spoken_khtn(text)
        self.txt_voice_transcript.value = normalized
        self.voice_status_text.value = "✅ Đã chọn và chuẩn hóa thuật ngữ KHTN thành công!"
        self.voice_status_text.color = ft.Colors.GREEN_700
        self.alert_box.visible = False
        self.page.update()

    def _on_text_change(self, e):
        count = len(self.txt_content.value or "")
        self.char_count_text.value = f"{count} ký tự"
        self.page.update()

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        if not e.files or len(e.files) == 0:
            return
        selected_file = e.files[0]
        problem_input = process_image_input(selected_file.path)
        self.current_input = problem_input

        if problem_input.validation_error:
            self._show_alert(problem_input.validation_error)
            self.img_preview.visible = False
            self.btn_clear_image.visible = False
            self.img_info_text.value = f"❌ Tệp không hợp lệ: {selected_file.name}"
            self.img_info_text.color = ft.Colors.RED_700
        else:
            self.alert_box.visible = False
            self.img_preview.src = problem_input.file_path
            self.img_preview.visible = True
            self.img_preview.height = 180
            self.btn_clear_image.visible = True
            self.img_info_text.value = f"✅ Đã tải: {selected_file.name} ({problem_input.file_size_mb:.2f} MB - Rõ nét)"
            self.img_info_text.color = ft.Colors.GREEN_700

        self.page.update()

    def _on_clear_image(self, e):
        self.current_input = None
        self.img_preview.visible = False
        self.img_preview.src = ""
        self.btn_clear_image.visible = False
        self.img_info_text.value = "Chưa chọn tệp ảnh nào (Chấp nhận JPG, PNG • Tối đa 5 MB)"
        self.img_info_text.color = ft.Colors.GREY_600
        self.alert_box.visible = False
        self.page.update()

    def _show_alert(self, msg: str):
        self.alert_text.value = msg
        self.alert_box.visible = True
        self.page.update()

    def _on_confirm_click(self, e):
        final_input: Optional[ProblemInput] = None
        if self.active_mode == "text":
            final_input = process_text_input(self.txt_content.value or "")
        elif self.active_mode == "image":
            if not self.current_input or not self.current_input.file_path:
                self._show_alert("Em chưa chọn ảnh bài tập nào! Hãy bấm nút chọn ảnh trước nhé.")
                return
            final_input = self.current_input
        elif self.active_mode == "sample":
            if self.selected_sample_id:
                final_input = process_sample_input(self.selected_sample_id)
            else:
                self._show_alert("Em hãy bấm chọn một bài tập mẫu ở trên để tiếp tục nhé!")
                return
        elif self.active_mode == "voice":
            speech_text = (self.txt_voice_transcript.value or "").strip()
            if not speech_text:
                self._show_alert("Em chưa đọc hoặc nhập lời nói! Hãy bấm Micro hoặc thử nhanh câu nói mẫu nhé.")
                return
            final_input = process_voice_input(speech_text)

        if not final_input or final_input.validation_error:
            self._show_alert(final_input.validation_error if final_input else "Dữ liệu chưa hợp lệ!")
            return

        final_input.is_confirmed = True
        self.current_input = final_input
        if self.on_confirm:
            self.on_confirm(final_input)


    def build(self) -> ft.Control:
        return ft.Container(
            content=ft.Column([
                self.standalone_header,
                self.welcome_banner,
                ft.Container(height=4),
                self.mode_row,
                ft.Container(height=6),
                self.text_container,
                self.image_container,
                self.sample_container,
                self.voice_container,
                ft.Container(height=4),
                self.privacy_card,
                self.alert_box,
                ft.Container(height=8),
                ft.Row([self.btn_confirm], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=10),
            padding=ft.Padding(20, 10, 20, 20)
        )
