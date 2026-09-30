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

import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional
import flet as ft
from PIL import ImageGrab, Image

from .input_model import ProblemInput, InputType
from .validator import (
    process_image_input,
    process_text_input,
    process_sample_input,
    MAX_FILE_SIZE_BYTES,
    SOCRATES_TEMP_DIR,
    resolve_image_asset_src,
    ASSETS_UPLOADS_DIR,
    ASSETS_SAMPLE_DIR
)

from .sample_bank import get_all_samples, get_sample_by_id, get_samples_by_strand
from .voice_service import (
    process_voice_input,
    normalize_spoken_khtn,
    get_demo_voice_presets,
    transcribe_audio_file,
    GLOBAL_AUDIO_RECORDER
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
        self.is_voice_recording = False
        self.recorder = GLOBAL_AUDIO_RECORDER
        self._recording_timer_thread = None
        self._stop_timer_flag = False


        # Tuyệt đối KHÔNG đưa FilePicker vào page.overlay (trong Flet 1.0 sẽ làm Flutter báo lỗi đỏ "Unknown control: FilePicker")
        if hasattr(self.page, "overlay") and self.page.overlay is not None:
            self.page.overlay[:] = [c for c in self.page.overlay if not isinstance(c, ft.FilePicker)]

        self.file_picker = None
        try:
            self.file_picker = ft.FilePicker(on_result=self._on_file_selected)
            if hasattr(self.page, "services") and self.page.services is not None:
                if self.file_picker not in self.page.services:
                    self.page.services.append(self.file_picker)
        except Exception:
            pass

        # Lắng nghe phím tắt Ctrl + V trên toàn trang (khi ở tab ảnh thì tự động dán ảnh)
        if hasattr(self.page, "on_keyboard_event"):
            old_handler = self.page.on_keyboard_event
            def _key_handler(e: ft.KeyboardEvent):
                is_ctrl = getattr(e, "ctrl", False)
                key_name = str(getattr(e, "key", "")).lower()
                if is_ctrl and key_name == "v" and self.active_mode == "image":
                    self._paste_image_from_clipboard(None)
                elif old_handler:
                    try:
                        old_handler(e)
                    except Exception:
                        pass
            self.page.on_keyboard_event = _key_handler

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

        # 2. Hướng dẫn thân thiện cho học sinh (Card Hero chào đón)
        self.welcome_banner = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.WHITE, size=24),
                    bgcolor=ft.Colors.AMBER_500,
                    border_radius=22,
                    width=44,
                    height=44,
                    alignment=ft.Alignment.CENTER,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.3, ft.Colors.AMBER_500), offset=ft.Offset(0, 2))
                ),
                ft.Column([
                    ft.Text("Chào em! Hôm nay em muốn khám phá bài tập KHTN nào cùng thầy Socrates?", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.INDIGO_900),
                    ft.Text("Em có thể tự gõ câu hỏi vào ô bên dưới, chọn từ các bài tập mẫu, chụp ảnh đề bài hoặc đọc bằng giọng nói nhé!", size=12, color=ft.Colors.GREY_700)
                ], spacing=2, expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(16, 14, 16, 14),
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        # 3. Ba thẻ lựa chọn phương thức nhập (Interactive Mode Cards)
        self.btn_mode_text = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.EDIT_NOTE_ROUNDED, size=20, color=ft.Colors.INDIGO_700),
                ft.Text("1. Tự gõ đề bài ✍️", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.INDIGO_900)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            bgcolor=ft.Colors.INDIGO_50,
            padding=ft.Padding(14, 11, 14, 11),
            border_radius=12,
            border=ft.Border.all(2, ft.Colors.INDIGO_600),
            on_click=lambda _: self._switch_mode("text"),
            expand=True
        )

        self.btn_mode_image = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CAMERA_ALT_ROUNDED, size=19, color=ft.Colors.GREY_700),
                ft.Text("2. Tải ảnh đề (≤ 5MB) 📷", weight=ft.FontWeight.W_500, size=13, color=ft.Colors.GREY_800)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(14, 11, 14, 11),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            on_click=lambda _: self._switch_mode("image"),
            expand=True
        )

        self.btn_mode_sample = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_STORIES_ROUNDED, size=19, color=ft.Colors.GREY_700),
                ft.Text("3. Bài mẫu KHTN 7 📚", weight=ft.FontWeight.W_500, size=13, color=ft.Colors.GREY_800)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(14, 11, 14, 11),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            on_click=lambda _: self._switch_mode("sample"),
            expand=True
        )

        self.btn_mode_voice = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.MIC_ROUNDED, size=19, color=ft.Colors.GREY_700),
                ft.Text("4. Giọng nói 🎙️", weight=ft.FontWeight.W_500, size=13, color=ft.Colors.GREY_800)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(14, 11, 14, 11),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            on_click=lambda _: self._switch_mode("voice"),
            expand=True
        )

        self.mode_row = ft.Row([self.btn_mode_text, self.btn_mode_image, self.btn_mode_sample, self.btn_mode_voice], spacing=10)

        # 4. KHU VỰC 1: Tự gõ đề bài (Thiết kế cao cấp, dễ bấm, tự động focus)
        self.txt_content = ft.TextField(
            hint_text="Nhập đề bài hoặc câu hỏi KHTN của em vào đây...\n(Ví dụ: Một người đi xe đạp với tốc độ 12 km/h trong thời gian 30 phút...)",
            hint_style=ft.TextStyle(color=ft.Colors.GREY_400, size=13),
            multiline=True,
            min_lines=5,
            max_lines=9,
            text_size=14,
            color=ft.Colors.GREY_900,
            cursor_color=ft.Colors.INDIGO_700,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.INDIGO_300,
            focused_border_color=ft.Colors.INDIGO_600,
            focused_border_width=2,
            border_radius=12,
            content_padding=ft.Padding(16, 14, 16, 14),
            autofocus=True,
            on_change=self._on_text_change
        )
        self.char_count_text = ft.Text("0 ký tự", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700)

        # Gợi ý câu hỏi KHTN 7 nhanh 1-chạm
        quick_prompts = [
            ("🚴 Chuyển động xe đạp (v = s/t)", "Một người đi xe đạp chuyển động đều trên quãng đường thẳng s = 12 km trong thời gian t = 30 phút. Hãy xác định tốc độ v của người đó theo đơn vị km/h và m/s."),
            ("🪞 Phản xạ ánh sáng gương phẳng", "Chiếu một tia sáng tới hợp với mặt gương phẳng một góc 30 độ. Hãy xác định góc tới và góc phản xạ của tia sáng đó."),
            ("🌿 Quá trình quang hợp ở thực vật", "Nêu các nguyên liệu chính và sản phẩm được tạo ra trong quá trình quang hợp ở thực vật. Quá trình này có ý nghĩa gì đối với sự sống trên Trái Đất?"),
            ("🧪 Phản ứng tạo gỉ sắt", "Hiện tượng gỉ sắt xảy ra khi sắt tiếp xúc với những chất nào trong không khí? Hãy viết phương trình chữ của phản ứng hóa học này.")
        ]

        quick_prompt_chips = [
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=13, color=ft.Colors.INDIGO_600),
                    ft.Text(label, size=11, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_900)
                ], spacing=4),
                bgcolor=ft.Colors.INDIGO_50,
                border=ft.Border.all(1, ft.Colors.INDIGO_200),
                padding=ft.Padding(10, 5, 10, 5),
                border_radius=16,
                tooltip="Bấm để đưa câu hỏi này vào ô nhập liệu",
                on_click=lambda _, t=text: self._apply_quick_prompt(t)
            )
            for label, text in quick_prompts
        ]

        self.text_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.EDIT_ROUNDED, size=16, color=ft.Colors.INDIGO_700),
                        ft.Text("Nội dung câu hỏi / Bài tập KHTN của em:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ], spacing=6),
                    self.char_count_text
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=self.txt_content,
                    on_click=lambda _: self.txt_content.focus()
                ),
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.LIGHTBULB_OUTLINE_ROUNDED, size=14, color=ft.Colors.AMBER_800),
                        ft.Text("Mẹo: Em có thể gõ công thức v = s/t, CO₂, O₂, m/s bình thường nhé.", size=11, color=ft.Colors.GREY_700, italic=True)
                    ], spacing=4),
                    ft.TextButton(
                        "Xóa nội dung 🗑️",
                        style=ft.ButtonStyle(color=ft.Colors.GREY_600, padding=4),
                        on_click=lambda _: self._clear_text_content()
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=2),
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.FLASH_ON_ROUNDED, size=14, color=ft.Colors.AMBER_700),
                        ft.Text("Thử nhanh với câu hỏi KHTN 7 mẫu (Bấm để điền ngay vào ô):", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700)
                    ], spacing=4),
                    ft.Row(quick_prompt_chips, spacing=6, wrap=True)
                ], spacing=4)
            ], spacing=6),
            bgcolor=ft.Colors.WHITE,
            padding=16,
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
            visible=True
        )

        # 5. KHU VỰC 2: Tải ảnh bài tập (Có 2 loại: Tải từ tệp ảnh & Dán ảnh từ Clipboard)
        self.btn_select_file = ft.FilledButton(
            "1. Chọn tệp ảnh từ máy tính (File) 📁",
            icon=ft.Icons.FOLDER_OPEN_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.INDIGO_600,
                color=ft.Colors.WHITE,
                padding=ft.Padding(18, 14, 18, 14),
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            tooltip="Mở hộp thoại máy tính để chọn ảnh JPG, PNG, WebP có sẵn",
            on_click=self._pick_image_from_file
        )

        self.btn_paste_clipboard = ft.FilledButton(
            "2. Dán ảnh vừa copy (Clipboard / Ctrl+V) 📋",
            icon=ft.Icons.CONTENT_PASTE_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL_600,
                color=ft.Colors.WHITE,
                padding=ft.Padding(18, 14, 18, 14),
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            tooltip="Dán ảnh vừa chụp (Win + Shift + S) hoặc vừa sao chép từ mạng/tài liệu",
            on_click=self._paste_image_from_clipboard
        )

        self.img_preview = ft.Image(src="", visible=False, fit=ft.BoxFit.CONTAIN, border_radius=8)
        self.img_info_text = ft.Text("Chưa chọn tệp ảnh nào (Chấp nhận JPG, PNG, WebP • Tối đa 5 MB)", size=12, color=ft.Colors.GREY_600)
        self.btn_clear_image = ft.TextButton("Bỏ chọn ảnh 🗑️", icon=ft.Icons.DELETE_OUTLINE, visible=False, on_click=self._on_clear_image)

        quick_sample_images = [
            ("⚡ Đề Cơ học Tốc độ (SGK)", "ocr_co_hoc_toc_do.png"),
            ("⚡ Đề Hóa Quang hợp (SGK)", "ocr_hoa_hoc_quang_hop.png"),
            ("⚡ Đề Vật lý Khối lượng (SGK)", "ocr_vat_ly_khoi_luong.png"),
        ]

        quick_image_chips = [
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.IMAGE_ROUNDED, size=13, color=ft.Colors.TEAL_700),
                    ft.Text(label, size=11, weight=ft.FontWeight.W_500, color=ft.Colors.TEAL_900)
                ], spacing=4),
                bgcolor=ft.Colors.TEAL_50,
                border=ft.Border.all(1, ft.Colors.TEAL_200),
                padding=ft.Padding(10, 5, 10, 5),
                border_radius=16,
                tooltip=f"Bấm để tải nhanh ảnh mẫu '{fname}' kiểm thử OCR",
                on_click=lambda _, f=fname: self._load_sample_image(f)
            )
            for label, fname in quick_sample_images
        ]

        self.image_container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.CircleAvatar(
                            content=ft.Icon(ft.Icons.CLOUD_UPLOAD_ROUNDED, size=32, color=ft.Colors.INDIGO_600),
                            bgcolor=ft.Colors.INDIGO_50,
                            radius=28
                        ),
                        ft.Text("Tải ảnh đề bài KHTN (Hỗ trợ 2 phương thức tải)", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.INDIGO_900),
                        ft.Text(
                            "Em có thể chọn tệp ảnh có sẵn trong máy tính, hoặc chụp ảnh màn hình rồi dán trực tiếp:",
                            size=12,
                            color=ft.Colors.GREY_700,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Container(height=6),
                        ft.Row([
                            self.btn_select_file,
                            self.btn_paste_clipboard
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=12, wrap=True),
                        ft.Container(height=6),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_800, size=18),
                                ft.Column([
                                    ft.Text("Hướng dẫn 2 loại tải ảnh:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.INDIGO_900),
                                    ft.Text("• Loại 1 (Tải từ file): Bấm 'Chọn tệp ảnh từ máy tính' để chọn ảnh JPG, PNG chụp từ sách vở.", size=11, color=ft.Colors.GREY_700),
                                    ft.Text("• Loại 2 (Copy ảnh): Nhấn phím Windows + Shift + S chụp đề bài, rồi bấm 'Dán ảnh' (hoặc nhấn Ctrl + V).", size=11, color=ft.Colors.GREY_700),
                                ], spacing=2, expand=True)
                            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.START),
                            bgcolor=ft.Colors.AMBER_50,
                            padding=10,
                            border_radius=10,
                            border=ft.Border.all(1, ft.Colors.AMBER_200)
                        ),
                        ft.Container(height=4),
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=13, color=ft.Colors.TEAL_800),
                                ft.Text("Thử nghiệm nhanh với ảnh chụp đề bài mẫu có sẵn:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700)
                            ], spacing=4),
                            ft.Row(quick_image_chips, spacing=6, wrap=True)
                        ], spacing=4)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    alignment=ft.Alignment.CENTER,
                    padding=20,
                    border=ft.Border.all(1.5, ft.Colors.INDIGO_200),
                    border_radius=16,
                    bgcolor=ft.Colors.WHITE
                ),
                ft.Row([self.img_info_text, self.btn_clear_image], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=self.img_preview,
                    alignment=ft.Alignment.CENTER,
                    padding=6,
                    border_radius=10
                )
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
                padding=ft.Padding(26, 16, 26, 16),
                shape=ft.RoundedRectangleBorder(radius=25),
                shadow_color=ft.Colors.with_opacity(0.3, ft.Colors.INDIGO_700),
                elevation=3
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
            try:
                self.txt_content.focus()
            except Exception:
                pass
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
        """Chọn bài mẫu và chuyển sang xem/sửa ngay trong ô hỏi."""
        self.selected_sample_id = sample_id
        sample = get_sample_by_id(sample_id)
        self.txt_content.value = sample["content"]
        self._on_text_change(None)
        self._switch_mode("text")
        try:
            self.txt_content.focus()
        except Exception:
            pass
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
        """Bật/tắt trạng thái thu âm giọng nói thực tế và chuyển đổi sang văn bản KHTN."""
        import threading
        import time

        if not self.is_voice_recording:
            # 1. BẮT ĐẦU THU ÂM
            success, msg = self.recorder.start_recording()
            if not success:
                self._show_alert(f"⚠️ {msg}\nEm hãy đảm bảo microphone trên máy tính đang hoạt động hoặc thử chọn các câu nói mẫu bên dưới nhé.")
                return

            self.is_voice_recording = True
            self._stop_timer_flag = False
            self.alert_box.visible = False

            # Cập nhật giao diện nút thu âm đang lắng nghe
            self.voice_mic_btn.bgcolor = ft.Colors.RED_800
            self.voice_mic_btn.content.controls[0].name = ft.Icons.STOP_CIRCLE_ROUNDED
            self.voice_mic_btn.content.controls[1].value = "Đang thu âm... Bấm để dừng ⏹️"
            self.voice_status_text.value = "🎙️ Đang thu âm từ Microphone... Em hãy đọc to, rõ ràng đề bài nhé! (0s)"
            self.voice_status_text.color = ft.Colors.RED_700
            self.page.update()

            # Luồng cập nhật số giây ghi âm trực tiếp
            def timer_worker():
                while not self._stop_timer_flag and self.is_voice_recording:
                    time.sleep(0.8)
                    if self._stop_timer_flag or not self.is_voice_recording:
                        break
                    sec = self.recorder.get_elapsed_seconds()
                    if self.is_voice_recording:
                        self.voice_status_text.value = f"🎙️ Đang thu âm từ Microphone... ({sec}s) - Bấm nút đỏ khi em nói xong nhé!"
                        try:
                            self.page.update()
                        except Exception:
                            pass

            self._recording_timer_thread = threading.Thread(target=timer_worker, daemon=True)
            self._recording_timer_thread.start()

        else:
            # 2. DỪNG THU ÂM VÀ CHUYỂN ĐỔI SANG VĂN BẢN (STT)
            self.is_voice_recording = False
            self._stop_timer_flag = True

            # Cập nhật giao diện sang trạng thái đang phân tích
            self.voice_mic_btn.disabled = True
            self.voice_mic_btn.opacity = 0.7
            self.voice_mic_btn.bgcolor = ft.Colors.AMBER_800
            self.voice_mic_btn.content.controls[0].name = ft.Icons.HOURGLASS_TOP_ROUNDED
            self.voice_mic_btn.content.controls[1].value = "Đang nhận diện giọng nói AI... ⏳"
            self.voice_status_text.value = "⏳ Đang chuyển đổi âm thanh sang văn bản và chuẩn hóa ký hiệu KHTN..."
            self.voice_status_text.color = ft.Colors.AMBER_900
            self.page.update()

            # Dừng ghi âm lấy file WAV
            wav_path = self.recorder.stop_recording()

            # Xử lý STT trong luồng nền để không làm đơ giao diện Flet
            def transcribe_worker():
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

                # Khôi phục trạng thái nút bấm và áp dụng kết quả
                self.voice_mic_btn.disabled = False
                self.voice_mic_btn.opacity = 1.0
                self.voice_mic_btn.bgcolor = ft.Colors.RED_600
                self.voice_mic_btn.content.controls[0].name = ft.Icons.MIC_ROUNDED
                self.voice_mic_btn.content.controls[1].value = "Bắt đầu nói 🎙️"

                if transcript and transcript.strip():
                    self.txt_voice_transcript.value = transcript
                    self.txt_content.value = transcript
                    self.voice_status_text.value = f"✅ Nhận diện thành công ({len(transcript)} ký tự)! Đã chuẩn hóa thuật ngữ KHTN."
                    self.voice_status_text.color = ft.Colors.GREEN_700
                else:
                    self.voice_status_text.value = "⚠️ Chưa nhận diện được âm thanh rõ ràng (có thể do nói quá nhanh hoặc im lặng). Em đọc lại hoặc chọn câu mẫu bên dưới nhé!"
                    self.voice_status_text.color = ft.Colors.ORANGE_800

                try:
                    self.page.update()
                except Exception:
                    pass

            threading.Thread(target=transcribe_worker, daemon=True).start()


    def _apply_voice_preset(self, text: str):
        """Áp dụng câu nói mẫu phát âm tiếng Việt và tự động chuẩn hóa KHTN."""
        normalized = normalize_spoken_khtn(text)
        self.txt_voice_transcript.value = normalized
        self.voice_status_text.value = "✅ Đã chọn và chuẩn hóa thuật ngữ KHTN thành công!"
        self.voice_status_text.color = ft.Colors.GREEN_700
        self.alert_box.visible = False
        self.page.update()

    def _apply_quick_prompt(self, text: str):
        """Áp dụng câu hỏi gợi ý nhanh và tự động focus vào ô hỏi."""
        self.txt_content.value = text
        self._on_text_change(None)
        self._switch_mode("text")
        try:
            self.txt_content.focus()
        except Exception:
            pass
        self.page.update()

    def _clear_text_content(self):
        """Xóa trắng nội dung ô hỏi để học sinh gõ lại từ đầu."""
        self.txt_content.value = ""
        self._on_text_change(None)
        try:
            self.txt_content.focus()
        except Exception:
            pass
        self.page.update()

    def _on_text_change(self, e):
        count = len(self.txt_content.value or "")
        self.char_count_text.value = f"{count} ký tự"
        self.page.update()

    def _pick_image_from_file(self, e=None):
        """Loại 1: Mở hộp thoại chọn tệp ảnh chuẩn trên máy tính (Native Windows Dialog)."""
        def _open_file_dialog():
            selected_path = None
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                selected_path = filedialog.askopenfilename(
                    title="Chọn ảnh bài tập KHTN (JPG/PNG/WebP)",
                    filetypes=[
                        ("Tệp hình ảnh (*.jpg, *.png, *.jpeg, *.webp)", "*.jpg;*.jpeg;*.png;*.webp;*.bmp"),
                        ("Tất cả các tệp (*.*)", "*.*")
                    ]
                )
                root.destroy()
            except Exception as ex:
                # Dự phòng bằng Flet FilePicker nếu Tkinter không gọi được
                if self.file_picker and hasattr(self.file_picker, "pick_files"):
                    try:
                        self.file_picker.pick_files(
                            dialog_title="Chọn ảnh bài tập KHTN (JPG/PNG, tối đa 5MB)",
                            allowed_extensions=["jpg", "jpeg", "png", "webp"]
                        )
                        return
                    except Exception:
                        pass

            if selected_path:
                self._process_selected_file_path(selected_path)

        threading.Thread(target=_open_file_dialog, daemon=True).start()

    def _paste_image_from_clipboard(self, e=None):
        """
        Loại 2: Dán ảnh trực tiếp từ bộ nhớ tạm (Clipboard / Ctrl+V):
        - Hỗ trợ ảnh chụp màn hình bằng Windows + Shift + S.
        - Hỗ trợ 'Sao chép hình ảnh' từ trình duyệt/Word/PDF.
        - Hỗ trợ copy tệp ảnh từ Windows Explorer.
        """
        try:
            clip_data = ImageGrab.grabclipboard()
            if clip_data is None:
                self._show_alert(
                    "Bộ nhớ tạm (Clipboard) chưa có ảnh nào!\n"
                    "👉 Em hãy nhấn tổ hợp phím Windows + Shift + S để chụp ảnh đề bài, hoặc chuột phải vào ảnh chọn 'Sao chép hình ảnh' rồi bấm lại nút này nhé!"
                )
                return

            # Trường hợp 1: Đối tượng hình ảnh (Image)
            if isinstance(clip_data, Image.Image):
                ASSETS_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
                timestamp = int(time.time() * 1000)
                temp_filename = f"clip_{timestamp}.png"
                temp_file_path = str(ASSETS_UPLOADS_DIR / temp_filename)

                # Lưu ảnh dưới định dạng PNG vào thư mục assets/uploads
                clip_data.save(temp_file_path, "PNG")
                try:
                    clip_data.save(str(SOCRATES_TEMP_DIR / temp_filename), "PNG")
                except Exception:
                    pass

                self._process_selected_file_path(temp_file_path, display_name="Ảnh chụp màn hình (Clipboard)")
                return

            # Trường hợp 2: Danh sách đường dẫn tệp (khi học sinh copy file trong Windows Explorer)
            if isinstance(clip_data, list):
                valid_images = [
                    p for p in clip_data
                    if isinstance(p, str) and os.path.splitext(p)[1].lower() in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]
                ]
                if valid_images:
                    self._process_selected_file_path(valid_images[0], display_name=os.path.basename(valid_images[0]))
                    return
                else:
                    self._show_alert("Các tệp vừa sao chép không phải là định dạng hình ảnh hợp lệ (chỉ nhận JPG, PNG, WebP).")
                    return

            self._show_alert(
                "Trong bộ nhớ tạm không có hình ảnh!\n"
                "Em hãy chụp màn hình bằng Win + Shift + S hoặc sao chép ảnh trước khi bấm Dán nhé."
            )
        except Exception as ex:
            self._show_alert(f"Lỗi khi đọc ảnh từ bộ nhớ tạm: {str(ex)}")

    def _load_sample_image(self, asset_filename: str):
        """Tải nhanh ảnh mẫu KHTN 7 có sẵn trong dự án để kiểm thử OCR."""
        possible_paths = [
            ASSETS_SAMPLE_DIR / asset_filename,
            Path(__file__).resolve().parent.parent / "chuc_nang_2_ocr_xac_nhan" / "sample_assets" / asset_filename,
            Path("assets") / "sample_assets" / asset_filename,
            Path("chuc_nang_2_ocr_xac_nhan") / "sample_assets" / asset_filename,
        ]
        found_path = None
        for p in possible_paths:
            if p.exists():
                found_path = str(p.resolve())
                break

        if found_path:
            self._process_selected_file_path(found_path, display_name=f"Ảnh mẫu ({asset_filename})")
        else:
            self._show_alert(f"Không tìm thấy ảnh mẫu: {asset_filename}")

    def _process_selected_file_path(self, file_path: str, display_name: Optional[str] = None):
        """Xử lý tệp ảnh được chọn (từ File, Clipboard, hoặc Ảnh mẫu)."""
        if not file_path or not os.path.exists(file_path):
            self._show_alert(f"Không tìm thấy tệp ảnh: {file_path}")
            return

        name = display_name or os.path.basename(file_path)
        problem_input = process_image_input(file_path)
        self.current_input = problem_input

        if problem_input.validation_error:
            self._show_alert(problem_input.validation_error)
            self.img_preview.visible = False
            self.img_preview.src = ""
            self.btn_clear_image.visible = False
            self.img_info_text.value = f"❌ Tệp không hợp lệ: {name}"
            self.img_info_text.color = ft.Colors.RED_700
        else:
            self.alert_box.visible = False
            # Chuyển đổi sang Web Asset URL tương thích Flet Web (Edge / Chrome)
            web_src = resolve_image_asset_src(problem_input.file_path)
            self.img_preview.src = web_src
            self.img_preview.visible = True
            self.img_preview.height = 240
            self.btn_clear_image.visible = True
            self.img_info_text.value = f"✅ Đã tải: {name} ({problem_input.file_size_mb:.2f} MB - Rõ nét)"
            self.img_info_text.color = ft.Colors.GREEN_700

        try:
            self.page.update()
        except Exception:
            pass


    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        """Nhận kết quả từ Flet FilePicker (nếu dùng)."""
        if not e.files or len(e.files) == 0:
            return
        selected_file = e.files[0]
        self._process_selected_file_path(selected_file.path, display_name=selected_file.name)

    def _on_clear_image(self, e):
        self.current_input = None
        self.img_preview.visible = False
        self.img_preview.src = ""
        self.btn_clear_image.visible = False
        self.img_info_text.value = "Chưa chọn tệp ảnh nào (Chấp nhận JPG, PNG, WebP • Tối đa 5 MB)"
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
                ft.Container(height=2),
                self.mode_row,
                ft.Container(height=4),
                self.text_container,
                self.image_container,
                self.sample_container,
                self.voice_container,
                ft.Container(height=2),
                self.privacy_card,
                self.alert_box,
                ft.Container(height=6),
                ft.Row([self.btn_confirm], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10)
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=ft.Padding(20, 10, 20, 20),
            expand=True
        )
