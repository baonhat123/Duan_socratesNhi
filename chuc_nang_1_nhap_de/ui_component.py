"""
Module: ui_component.py
Chức năng 1 (FR-01): Giao diện Nhập đề bài
Đặc tả: Socrates Nhí v3.0 (Tương thích Flet 1.0+)

Cung cấp giao diện trực quan Flet cho màn hình Nhập đề:
- Cho phép học sinh gõ đề văn bản hoặc tải ảnh JPG/PNG <= 5MB.
- Chọn nhanh từ ngân hàng đề mẫu KHTN 7 (3 mạch kiến thức).
- Kiểm tra dung lượng & định dạng file với cảnh báo trực quan.
- Cảnh báo bảo mật PII (nhắc che tên, trường, lớp trước khi gửi).
- Nút "Xác nhận đề bài" đảm bảo nguyên tắc sư phạm: KHÔNG gửi sang AI trước khi xác nhận.
"""

from pathlib import Path
from typing import Callable, Optional
import flet as ft

from .input_model import ProblemInput, InputType
from .validator import (
    process_image_input,
    process_text_input,
    MAX_FILE_SIZE_BYTES
)
from .sample_bank import get_all_samples, get_sample_by_id


class ProblemInputView:
    """
    Component giao diện Flet cho Chức năng 1: Nhập đề bài
    """
    def __init__(self, page: ft.Page, on_confirm: Optional[Callable[[ProblemInput], None]] = None):
        self.page = page
        self.on_confirm = on_confirm
        self.current_input: Optional[ProblemInput] = None
        self.active_mode = "text"  # "text", "image", "sample"

        # Thiết lập FilePicker
        self.file_picker = ft.FilePicker(on_result=self._on_file_selected)
        if hasattr(self.page, "overlay") and self.page.overlay is not None:
            self.page.overlay.append(self.file_picker)

        # Xây dựng các control
        self._build_controls()

    def _build_controls(self):
        # 1. Header & Banner thông tin
        self.header_title = ft.Text(
            "Socrates Nhí 💡",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.INDIGO_700
        )
        self.header_sub = ft.Text(
            "Trợ lý AI gợi mở tư duy Khoa học tự nhiên • Bảng A (THCS)",
            size=14,
            color=ft.Colors.GREY_700
        )
        self.header_slogan = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.AMBER_800, size=18),
                    ft.Text(
                        "Nguyên tắc sư phạm: AI hỏi để em tự lập luận — Không phát đáp án sẵn!",
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.AMBER_900
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=ft.Colors.AMBER_50,
            padding=8,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.AMBER_200)
        )

        # 2. Segmented Button chọn phương thức nhập
        self.mode_selector = ft.SegmentedButton(
            selected=["text"],
            allow_multiple_selection=False,
            on_change=self._on_mode_change,
            segments=[
                ft.Segment(
                    value="text",
                    label=ft.Text("1. Gõ đề bài (Văn bản)"),
                    icon=ft.Icon(ft.Icons.EDIT_NOTE_OUTLINED)
                ),
                ft.Segment(
                    value="image",
                    label=ft.Text("2. Tải ảnh đề (JPG/PNG ≤ 5MB)"),
                    icon=ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED)
                ),
                ft.Segment(
                    value="sample",
                    label=ft.Text("3. Chọn đề mẫu KHTN 7"),
                    icon=ft.Icon(ft.Icons.MENU_BOOK_OUTLINED)
                )
            ]
        )

        # 3. Khu vực Tab 1: Gõ đề bài
        self.txt_content = ft.TextField(
            label="Nội dung câu hỏi hoặc bài tập KHTN",
            hint_text="Nhập đề bài vào đây (ví dụ: Một người đi xe đạp với tốc độ v = 15 km/h...)",
            multiline=True,
            min_lines=6,
            max_lines=12,
            on_change=self._on_text_change
        )
        self.char_count_text = ft.Text("0 ký tự", size=12, color=ft.Colors.GREY_600)

        self.text_container = ft.Column(
            [
                self.txt_content,
                ft.Row([self.char_count_text], alignment=ft.MainAxisAlignment.END)
            ],
            spacing=5
        )

        # 4. Khu vực Tab 2: Tải ảnh bài tập
        self.btn_select_file = ft.FilledButton(
            "Chọn tệp ảnh từ máy tính",
            icon=ft.Icons.FILE_UPLOAD_OUTLINED,
            on_click=lambda _: self.file_picker.pick_files(
                dialog_title="Chọn ảnh bài tập KHTN (JPG/PNG, tối đa 5MB)",
                allowed_extensions=["jpg", "jpeg", "png"]
            ),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.INDIGO_600,
                color=ft.Colors.WHITE
            )
        )
        self.img_preview = ft.Image(
            src="",
            visible=False,
            fit=ft.BoxFit.CONTAIN,
            border_radius=8
        )
        self.img_info_text = ft.Text(
            "Chưa chọn tệp ảnh nào. (Chấp nhận JPG, JPEG, PNG • Tối đa 5 MB)",
            size=13,
            color=ft.Colors.GREY_600
        )
        self.btn_clear_image = ft.TextButton(
            "Bỏ chọn ảnh",
            icon=ft.Icons.DELETE_OUTLINE,
            visible=False,
            on_click=self._on_clear_image
        )

        self.image_container = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=48, color=ft.Colors.INDIGO_400),
                                ft.Text(
                                    "Kéo & thả hoặc bấm nút bên dưới để tải ảnh chụp đề bài",
                                    weight=ft.FontWeight.W_500,
                                    color=ft.Colors.GREY_800
                                ),
                                ft.Text(
                                    "Yêu cầu: Ảnh rõ nét, không quá mờ/nghiêng • Dung lượng ≤ 5 MB",
                                    size=12,
                                    color=ft.Colors.GREY_600
                                ),
                                ft.Container(height=10),
                                self.btn_select_file
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        alignment=ft.Alignment.CENTER,
                        padding=20,
                        border=ft.Border.all(1.5, ft.Colors.INDIGO_200),
                        border_radius=12,
                        bgcolor=ft.Colors.GREY_50
                    ),
                    ft.Row(
                        [self.img_info_text, self.btn_clear_image],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Container(
                        content=self.img_preview,
                        alignment=ft.Alignment.CENTER,
                        padding=10
                    )
                ],
                spacing=10
            ),
            visible=False
        )

        # 5. Khu vực Tab 3: Chọn bài mẫu KHTN 7
        samples = get_all_samples()
        sample_options = [
            ft.DropdownOption(
                key=s["id"],
                text=f"[{s['strand']}] - {s['title']}"
            )
            for s in samples
        ]
        self.sample_dropdown = ft.Dropdown(
            label="Chọn một bài mẫu có sẵn",
            options=sample_options,
            value=samples[0]["id"],
            on_select=self._on_sample_selected
        )
        self.sample_preview_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"Bài: {samples[0]['title']}", weight=ft.FontWeight.BOLD, size=15),
                        ft.Text(f"Mạch kiến thức: {samples[0]['strand']}", color=ft.Colors.INDIGO_600, size=13),
                        ft.Text(f"Khái niệm: {', '.join(samples[0]['concepts'])}", color=ft.Colors.GREY_700, size=12),
                        ft.Divider(),
                        ft.Text(samples[0]["content"], size=13)
                    ],
                    spacing=6
                ),
                padding=15
            )
        )
        self.sample_container = ft.Column(
            [
                self.sample_dropdown,
                self.sample_preview_card
            ],
            visible=False,
            spacing=10
        )

        # 6. Banner cảnh báo bảo mật PII
        self.pii_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SHIELD_OUTLINED, color=ft.Colors.BLUE_800, size=20),
                    ft.Text(
                        "Bảo vệ riêng tư: Socrates Nhí hoàn toàn ẩn danh. Em vui lòng KHÔNG ghi tên, lớp, trường hay SĐT trên đề bài!",
                        size=12,
                        color=ft.Colors.BLUE_900,
                        expand=True
                    )
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=ft.Colors.BLUE_50,
            padding=10,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.BLUE_200)
        )

        # 7. Thông báo lỗi hoặc cảnh báo
        self.alert_text = ft.Text("", size=13, weight=ft.FontWeight.W_500)
        self.alert_box = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_700),
                self.alert_text
            ]),
            bgcolor=ft.Colors.RED_50,
            border=ft.Border.all(1, ft.Colors.RED_300),
            padding=10,
            border_radius=8,
            visible=False
        )

        # 8. Hộp tóm tắt kết quả sau khi xác nhận (Sẵn sàng sang Chức năng 2)
        self.summary_box = ft.Container(
            visible=False,
            bgcolor=ft.Colors.GREEN_50,
            border=ft.Border.all(1, ft.Colors.GREEN_300),
            border_radius=8,
            padding=15
        )

        # 9. Nút hành động chính (Xác nhận đề bài)
        self.btn_confirm = ft.FilledButton(
            "Xác nhận đề bài này",
            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.INDIGO_700,
                color=ft.Colors.WHITE,
                padding=18
            ),
            on_click=self._on_confirm_click
        )

        self.btn_reset = ft.OutlinedButton(
            "Làm lại từ đầu",
            icon=ft.Icons.REFRESH,
            on_click=self._on_reset_click
        )

    def _on_mode_change(self, e):
        """Chuyển đổi qua lại giữa 3 chế độ nhập."""
        selected = self.mode_selector.selected
        if not selected:
            return
        mode = list(selected)[0]
        self.active_mode = mode

        self.text_container.visible = (mode == "text")
        self.image_container.visible = (mode == "image")
        self.sample_container.visible = (mode == "sample")

        self.alert_box.visible = False
        self.summary_box.visible = False
        self.page.update()

    def _on_text_change(self, e):
        """Cập nhật số ký tự gõ."""
        count = len(self.txt_content.value or "")
        self.char_count_text.value = f"{count} ký tự"
        self.page.update()

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        """Xử lý khi học sinh chọn ảnh qua FilePicker."""
        if not e.files or len(e.files) == 0:
            return

        selected_file = e.files[0]
        file_path = selected_file.path

        # Thực hiện thẩm định qua validator
        problem_input = process_image_input(file_path)
        self.current_input = problem_input

        if problem_input.validation_error:
            # Hiển thị lỗi dung lượng hoặc định dạng
            self._show_alert(problem_input.validation_error, is_error=True)
            self.img_preview.visible = False
            self.btn_clear_image.visible = False
            self.img_info_text.value = f"❌ Lỗi: {selected_file.name} ({round(selected_file.size / (1024*1024), 2)} MB)"
            self.img_info_text.color = ft.Colors.RED_700
        else:
            # Ảnh hợp lệ
            self.alert_box.visible = False
            self.img_preview.src = problem_input.file_path
            self.img_preview.visible = True
            self.img_preview.height = 200
            self.btn_clear_image.visible = True
            size_mb = problem_input.file_size_mb
            self.img_info_text.value = f"✅ Đã chọn ảnh: {selected_file.name} ({size_mb:.2f} MB - Hợp lệ)"
            self.img_info_text.color = ft.Colors.GREEN_700

        self.page.update()

    def _on_clear_image(self, e):
        """Xóa ảnh đang chọn."""
        self.current_input = None
        self.img_preview.visible = False
        self.img_preview.src = ""
        self.btn_clear_image.visible = False
        self.img_info_text.value = "Chưa chọn tệp ảnh nào. (Chấp nhận JPG, JPEG, PNG • Tối đa 5 MB)"
        self.img_info_text.color = ft.Colors.GREY_600
        self.alert_box.visible = False
        self.page.update()

    def _on_sample_selected(self, e):
        """Cập nhật card thông tin khi đổi bài mẫu."""
        sample_id = self.sample_dropdown.value
        sample = get_sample_by_id(sample_id)
        self.sample_preview_card.content.content.controls = [
            ft.Text(f"Bài: {sample['title']}", weight=ft.FontWeight.BOLD, size=15),
            ft.Text(f"Mạch kiến thức: {sample['strand']}", color=ft.Colors.INDIGO_600, size=13),
            ft.Text(f"Khái niệm: {', '.join(sample['concepts'])}", color=ft.Colors.GREY_700, size=12),
            ft.Divider(),
            ft.Text(sample["content"], size=13)
        ]
        self.page.update()

    def _show_alert(self, message: str, is_error: bool = True):
        """Hiển thị hộp thông báo lỗi/cảnh báo."""
        self.alert_text.value = message
        self.alert_box.bgcolor = ft.Colors.RED_50 if is_error else ft.Colors.AMBER_50
        self.alert_box.border = ft.Border.all(1, ft.Colors.RED_300 if is_error else ft.Colors.AMBER_300)
        self.alert_box.visible = True
        self.summary_box.visible = False
        self.page.update()

    def _on_confirm_click(self, e):
        """
        Xử lý khi học sinh nhấn "Xác nhận đề bài này".
        TUÂN THỦ FR-01: Chỉ khi nhấn nút này thì is_confirmed mới chuyển sang True.
        """
        final_input: Optional[ProblemInput] = None

        if self.active_mode == "text":
            raw_text = self.txt_content.value or ""
            final_input = process_text_input(raw_text)

        elif self.active_mode == "image":
            if not self.current_input or not self.current_input.file_path:
                self._show_alert("Em chưa chọn ảnh bài tập nào! Hãy nhấn nút chọn ảnh trước nhé.", is_error=True)
                return
            final_input = self.current_input

        elif self.active_mode == "sample":
            sample_id = self.sample_dropdown.value
            sample = get_sample_by_id(sample_id)
            final_input = ProblemInput(
                input_type=InputType.SAMPLE,
                text_content=sample["content"],
                file_name=f"{sample['title']}.txt",
                is_confirmed=False
            )

        if not final_input:
            self._show_alert("Không thể khởi tạo dữ liệu đề bài. Vui lòng thử lại!", is_error=True)
            return

        # Kiểm tra lỗi thẩm định
        if final_input.validation_error:
            self._show_alert(final_input.validation_error, is_error=True)
            return

        # Đánh dấu XÁC NHẬN CHÍNH THỨC
        final_input.is_confirmed = True
        self.current_input = final_input
        self.alert_box.visible = False

        # Hiển thị thông báo thành công & thẻ tóm tắt
        mode_label = {
            InputType.TEXT: "Văn bản tự gõ",
            InputType.IMAGE: "Ảnh bài tập tải lên",
            InputType.SAMPLE: "Đề bài mẫu KHTN 7"
        }[final_input.input_type]

        summary_rows = [
            ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_700),
                ft.Text(f"Đã xác nhận đề bài ({mode_label}) thành công!", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900)
            ]),
            ft.Text(
                "Đã tuân thủ quy tắc FR-01: Dữ liệu đã đóng gói an toàn, sẵn sàng chuyển tiếp sang Chức năng 2 (OCR & Xác nhận nội dung).",
                size=12,
                color=ft.Colors.GREEN_800
            )
        ]

        if final_input.input_type == InputType.IMAGE:
            summary_rows.append(
                ft.Text(f"• Tệp: {final_input.file_name} ({final_input.file_size_mb:.2f} MB)", size=12)
            )
        else:
            summary_rows.append(
                ft.Text(f"• Đoạn trích: \"{final_input.text_content[:80]}...\"", size=12, italic=True)
            )

        if final_input.safety_warnings:
            for w in final_input.safety_warnings:
                summary_rows.append(
                    ft.Text(f"⚠️ {w}", size=12, color=ft.Colors.AMBER_900)
                )

        self.summary_box.content = ft.Column(summary_rows, spacing=5)
        self.summary_box.visible = True
        self.page.update()

        # Kích hoạt callback nếu có (để tích hợp vào toàn bộ app)
        if self.on_confirm:
            self.on_confirm(final_input)

    def _on_reset_click(self, e):
        """Khôi phục trạng thái ban đầu."""
        self.txt_content.value = ""
        self.char_count_text.value = "0 ký tự"
        self._on_clear_image(None)
        self.alert_box.visible = False
        self.summary_box.visible = False
        self.current_input = None
        self.page.update()

    def build(self) -> ft.Control:
        """Trả về toàn bộ giao diện của Chức năng 1 trong một Container."""
        return ft.Container(
            content=ft.Column(
                [
                    self.header_title,
                    self.header_sub,
                    self.header_slogan,
                    ft.Container(height=10),
                    self.mode_selector,
                    ft.Container(height=10),
                    self.text_container,
                    self.image_container,
                    self.sample_container,
                    ft.Container(height=5),
                    self.pii_banner,
                    self.alert_box,
                    self.summary_box,
                    ft.Container(height=10),
                    ft.Row(
                        [
                            self.btn_confirm,
                            self.btn_reset
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=15
                    )
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=25,
            expand=True
        )
