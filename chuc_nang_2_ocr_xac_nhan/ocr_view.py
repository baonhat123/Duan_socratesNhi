"""
Module: ocr_view.py
Chức năng 2 (FR-02): Giao diện Trích xuất OCR & Xác nhận/Biên tập đề bài
Đặc tả: Socrates Nhí v3.0 (Tương thích Flet 1.0+)

Giao diện chuyên nghiệp gồm:
1. Stepper tiến trình (Nhập đề -> Trích xuất OCR -> Hội thoại Socratic).
2. Bố cục đối chiếu 2 cột: Ảnh đề bài gốc (có đo độ nét) vs Ô biên tập công thức.
3. Thanh công cụ ký hiệu KHTN nhanh (H₂O, CO₂, v², km/h, m/s, N, →, °C).
4. Khung xem trước công thức trực quan (Live Preview) theo thời gian thực.
5. Cảnh báo từ chối ảnh mờ (không đoán mò theo cam kết FR-02).
6. Nút "Xác nhận đề bài" để chuyển giao dữ liệu sang bộ điều phối Socratic.
"""

from typing import Callable, Optional
import flet as ft

from .ocr_model import OcrResult, ConfirmedProblem
from .ocr_engine import process_image_ocr
from .formula_normalizer import normalize_khtn_text, extract_formulas_and_units
from .sample_images import SAMPLE_PATHS


class OcrConfirmationView:
    """
    Component giao diện Flet cho Chức năng 2: Trích xuất & Xác nhận OCR
    """
    def __init__(
        self,
        page: ft.Page,
        image_path: Optional[str] = None,
        on_confirm: Optional[Callable[[ConfirmedProblem], None]] = None
    ):
        self.page = page
        self.current_image_path = image_path or SAMPLE_PATHS.get("co_hoc", "")
        self.on_confirm = on_confirm
        self.current_ocr_result: Optional[OcrResult] = None
        self.confirmed_problem: Optional[ConfirmedProblem] = None

        # Khởi tạo giao diện
        self._build_controls()

        # Tự động chạy OCR cho ảnh ban đầu
        if self.current_image_path:
            self.load_image_and_run_ocr(self.current_image_path)

    def _build_controls(self):
        # 1. Header & Tiến trình (Stepper)
        self.header_title = ft.Text(
            "Socrates Nhí 💡",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.INDIGO_700
        )
        self.header_sub = ft.Text(
            "Bước 2: Trích xuất OCR & Xác nhận nội dung công thức KHTN",
            size=14,
            color=ft.Colors.GREY_700
        )

        self.stepper_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=16),
                        ft.Text("1. Nhập đề bài", size=12, color=ft.Colors.GREEN_800, weight=ft.FontWeight.BOLD)
                    ]),
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=ft.Colors.GREY_400),
                    ft.Row([
                        ft.Icon(ft.Icons.EDIT_DOCUMENT, color=ft.Colors.INDIGO_700, size=16),
                        ft.Text("2. Trích xuất & Sửa OCR (Hiện tại)", size=12, color=ft.Colors.INDIGO_800, weight=ft.FontWeight.BOLD)
                    ]),
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=ft.Colors.GREY_400),
                    ft.Row([
                        ft.Icon(ft.Icons.PSYCHOLOGY_OUTLINED, color=ft.Colors.GREY_400, size=16),
                        ft.Text("3. Hội thoại Socratic", size=12, color=ft.Colors.GREY_500)
                    ]),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            ),
            bgcolor=ft.Colors.INDIGO_50,
            padding=10,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.INDIGO_100)
        )

        # 2. Bộ chọn ảnh mẫu kiểm thử nhanh (Dropdown test)
        sample_options = [
            ft.DropdownOption(key=SAMPLE_PATHS["co_hoc"], text="1. Ảnh chữ in rõ nét (Vật lý chuyển động)"),
            ft.DropdownOption(key=SAMPLE_PATHS["vat_ly"], text="2. Ảnh công thức Vật lý (v², km/h, N)"),
            ft.DropdownOption(key=SAMPLE_PATHS["hoa_hoc"], text="3. Ảnh phương trình Hóa học (H₂O, CO₂, quang hợp)"),
            ft.DropdownOption(key=SAMPLE_PATHS["blurry"], text="4. Ảnh mờ cố ý (Test từ chối không đoán mò)")
        ]
        self.sample_selector = ft.Dropdown(
            label="Thử nghiệm nhanh với bộ ảnh mẫu checklist mục 12",
            options=sample_options,
            value=self.current_image_path,
            on_select=self._on_sample_changed
        )

        # 3. CỘT TRÁI: Ảnh đề bài gốc & Đánh giá độ nét
        self.img_display = ft.Image(
            src=self.current_image_path,
            fit=ft.BoxFit.CONTAIN,
            border_radius=8,
            height=240
        )
        self.sharpness_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LENS, color=ft.Colors.GREEN_600, size=12),
                ft.Text("Độ nét ảnh: Đang tính toán...", size=12, weight=ft.FontWeight.BOLD)
            ]),
            padding=ft.Padding(8, 4, 8, 4),
            border_radius=6,
            bgcolor=ft.Colors.GREEN_50,
            border=ft.Border.all(1, ft.Colors.GREEN_200)
        )
        self.left_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("Ảnh đề bài gốc", weight=ft.FontWeight.BOLD, size=14),
                                self.sharpness_badge
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Divider(),
                        ft.Container(
                            content=self.img_display,
                            alignment=ft.Alignment.CENTER,
                            padding=5
                        ),
                        ft.Text(
                            "💡 Quy tắc FR-02: Nếu ảnh quá mờ hoặc nhòe chữ, ứng dụng sẽ yêu cầu chụp lại để tránh đoán mò.",
                            size=11,
                            color=ft.Colors.GREY_600,
                            italic=True
                        )
                    ],
                    spacing=8
                ),
                padding=12
            )
        )

        # 4. CỘT PHẢI: Thanh công cụ ký hiệu KHTN & Trình soạn thảo
        quick_symbols = [
            ("H₂O", "H₂O"), ("CO₂", "CO₂"), ("O₂", "O₂"), ("→", " → "),
            ("v²", "v²"), ("km/h", " km/h"), ("m/s", " m/s"), ("N", " N"),
            ("°C", "°C"), ("g", " g"), ("kg", " kg"), ("²", "²"), ("³", "³")
        ]
        symbol_buttons = [
            ft.TextButton(
                sym[0],
                style=ft.ButtonStyle(
                    padding=6,
                    bgcolor=ft.Colors.INDIGO_50,
                    color=ft.Colors.INDIGO_900
                ),
                on_click=lambda _, val=sym[1]: self._insert_symbol(val)
            )
            for sym in quick_symbols
        ]

        self.symbol_toolbar = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.KEYBOARD_ALT_OUTLINED, size=14, color=ft.Colors.INDIGO_700),
                            ft.Text("Thanh ký hiệu KHTN nhanh (Bấm để chèn vào vị trí con trỏ):", size=12, weight=ft.FontWeight.W_500)
                        ],
                        spacing=5
                    ),
                    ft.Row(
                        symbol_buttons,
                        wrap=True,
                        spacing=5
                    )
                ],
                spacing=6
            ),
            bgcolor=ft.Colors.GREY_50,
            padding=8,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.GREY_300)
        )

        # Ô soạn thảo văn bản OCR trực tiếp
        self.txt_editor = ft.TextField(
            label="Nội dung trích xuất (Học sinh có thể chỉnh sửa trực tiếp từng chỗ sai)",
            multiline=True,
            min_lines=6,
            max_lines=10,
            on_change=self._on_text_edited
        )

        # Live Preview xem trước công thức định dạng chuẩn
        self.live_preview_text = ft.Text("", size=13, weight=ft.FontWeight.W_400)
        self.live_preview_box = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.VISIBILITY_OUTLINED, size=14, color=ft.Colors.BLUE_700),
                    ft.Text("Xem trước hiển thị chuẩn hóa (Live Formula Preview):", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
                ]),
                self.live_preview_text
            ], spacing=4),
            bgcolor=ft.Colors.BLUE_50,
            border=ft.Border.all(1, ft.Colors.BLUE_200),
            border_radius=8,
            padding=10
        )

        # Thẻ hiển thị các đại lượng / công thức phát hiện được
        self.detected_tags_row = ft.Row([], wrap=True, spacing=6)
        self.detected_tags_box = ft.Container(
            content=ft.Column([
                ft.Text("Đại lượng & Khái niệm phát hiện:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                self.detected_tags_row
            ], spacing=4),
            visible=False
        )

        self.right_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("Văn bản & Công thức KHTN nhận diện", weight=ft.FontWeight.BOLD, size=14),
                                ft.TextButton("Khôi phục bản gốc OCR", icon=ft.Icons.RESTORE, on_click=self._on_restore_original)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        self.symbol_toolbar,
                        self.txt_editor,
                        self.live_preview_box,
                        self.detected_tags_box
                    ],
                    spacing=8
                ),
                padding=12
            )
        )

        # 5. Thông báo cảnh báo hoặc từ chối ảnh mờ
        self.alert_text = ft.Text("", size=13, weight=ft.FontWeight.W_500)
        self.alert_box = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_700),
                self.alert_text
            ]),
            bgcolor=ft.Colors.RED_50,
            border=ft.Border.all(1, ft.Colors.RED_300),
            padding=12,
            border_radius=8,
            visible=False
        )

        # 6. Thông báo thành công sau khi xác nhận
        self.success_box = ft.Container(
            visible=False,
            bgcolor=ft.Colors.GREEN_50,
            border=ft.Border.all(1, ft.Colors.GREEN_300),
            border_radius=8,
            padding=15
        )

        # 7. Nút hành động chính
        self.btn_confirm = ft.FilledButton(
            "Xác nhận đề bài này để bắt đầu học",
            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.INDIGO_700,
                color=ft.Colors.WHITE,
                padding=18
            ),
            on_click=self._on_confirm_click
        )

    def load_image_and_run_ocr(self, image_path: str):
        """Tiến hành kiểm tra độ nét và trích xuất OCR từ tệp ảnh."""
        self.current_image_path = image_path
        self.img_display.src = image_path

        # Thực thi OCR engine
        ocr_res = process_image_ocr(image_path)
        self.current_ocr_result = ocr_res

        # Cập nhật huy hiệu độ nét
        sharpness = ocr_res.sharpness_score
        if ocr_res.is_blurry:
            self.sharpness_badge.content.controls[0].color = ft.Colors.RED_600
            self.sharpness_badge.content.controls[1].value = f"Độ nét: {sharpness}% (Quá mờ)"
            self.sharpness_badge.bgcolor = ft.Colors.RED_50
            self.sharpness_badge.border = ft.Border.all(1, ft.Colors.RED_200)

            # Hiển thị thông báo từ chối ảnh mờ
            self._show_alert(ocr_res.error_message or "Ảnh quá mờ, không thể đọc chính xác!")
            self.txt_editor.value = ""
            self.live_preview_text.value = "(Không có nội dung do ảnh quá mờ)"
            self.btn_confirm.disabled = True
            self.detected_tags_box.visible = False
        else:
            self.sharpness_badge.content.controls[0].color = ft.Colors.GREEN_600
            self.sharpness_badge.content.controls[1].value = f"Độ nét: {sharpness}% (Rõ nét)"
            self.sharpness_badge.bgcolor = ft.Colors.GREEN_50
            self.sharpness_badge.border = ft.Border.all(1, ft.Colors.GREEN_200)

            self.alert_box.visible = False
            self.btn_confirm.disabled = False
            self.txt_editor.value = ocr_res.formatted_text
            self._update_live_preview(ocr_res.formatted_text)

        self.success_box.visible = False
        self.page.update()

    def _on_sample_changed(self, e):
        """Xử lý khi học sinh chọn ảnh mẫu khác."""
        val = self.sample_selector.value
        if val:
            self.load_image_and_run_ocr(val)

    def _insert_symbol(self, symbol_text: str):
        """Chèn nhanh ký hiệu KHTN vào ô soạn thảo."""
        current_val = self.txt_editor.value or ""
        self.txt_editor.value = current_val + symbol_text
        self._update_live_preview(self.txt_editor.value)
        self.page.update()

    def _on_text_edited(self, e):
        """Xử lý khi học sinh gõ sửa trực tiếp văn bản đề bài."""
        current_val = self.txt_editor.value or ""
        self._update_live_preview(current_val)
        self.page.update()

    def _update_live_preview(self, text: str):
        """Cập nhật khung xem trước và các tag đại lượng."""
        normalized = normalize_khtn_text(text)
        self.live_preview_text.value = normalized if normalized else "(Chưa có nội dung đề bài)"

        formulas, units = extract_formulas_and_units(normalized)
        chips = []
        for f in formulas[:4]:
            chips.append(
                ft.Container(
                    content=ft.Text(f"📐 {f}", size=11, color=ft.Colors.INDIGO_900),
                    bgcolor=ft.Colors.INDIGO_50,
                    padding=ft.Padding(6, 2, 6, 2),
                    border_radius=4
                )
            )
        for u in units[:4]:
            chips.append(
                ft.Container(
                    content=ft.Text(f"📏 {u}", size=11, color=ft.Colors.GREEN_900),
                    bgcolor=ft.Colors.GREEN_50,
                    padding=ft.Padding(6, 2, 6, 2),
                    border_radius=4
                )
            )

        if chips:
            self.detected_tags_row.controls = chips
            self.detected_tags_box.visible = True
        else:
            self.detected_tags_box.visible = False

    def _on_restore_original(self, e):
        """Khôi phục lại nội dung ban đầu từ OCR."""
        if self.current_ocr_result and not self.current_ocr_result.is_blurry:
            self.txt_editor.value = self.current_ocr_result.formatted_text
            self._update_live_preview(self.current_ocr_result.formatted_text)
            self.page.update()

    def _show_alert(self, message: str):
        self.alert_text.value = message
        self.alert_box.visible = True
        self.success_box.visible = False
        self.page.update()

    def _on_confirm_click(self, e):
        """
        Học sinh nhấn 'Xác nhận đề bài để bắt đầu học'.
        Đóng gói ConfirmedProblem hoàn chỉnh.
        """
        final_text = (self.txt_editor.value or "").strip()
        if not final_text:
            self._show_alert("Nội dung đề bài không được để trống! Em hãy kiểm tra lại nhé.")
            return

        normalized_final = normalize_khtn_text(final_text)
        formulas, units = extract_formulas_and_units(normalized_final)

        was_edited = False
        orig_text = ""
        if self.current_ocr_result:
            orig_text = self.current_ocr_result.raw_text
            was_edited = (final_text != self.current_ocr_result.formatted_text)

        confirmed = ConfirmedProblem(
            original_text=orig_text,
            confirmed_text=normalized_final,
            was_edited=was_edited,
            formulas=formulas,
            units=units,
            source_type="image",
            image_path=self.current_image_path
        )
        self.confirmed_problem = confirmed

        # Hiển thị thông báo thành công
        self.alert_box.visible = False
        edit_status = "Đã chỉnh sửa công thức chuẩn xác" if was_edited else "Giữ nguyên bản nhận dạng"
        self.success_box.content = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_700),
                ft.Text("ĐÃ XÁC NHẬN ĐỀ BÀI THÀNH CÔNG (FR-02)!", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900)
            ]),
            ft.Text(f"• Trạng thái biên tập: {edit_status}", size=12, color=ft.Colors.GREEN_800),
            ft.Text(f"• Nội dung chốt: \"{normalized_final[:100]}...\"", size=12, italic=True),
            ft.Text(
                "Dữ liệu đã sẵn sàng chuyển giao cho Chức năng 3 (Phân loại kiến thức) & Chức năng 4 (Chu trình Socratic 5 pha)!",
                size=12,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.GREEN_900
            )
        ], spacing=4)
        self.success_box.visible = True
        self.page.update()

        # Gọi callback bàn giao
        if self.on_confirm:
            self.on_confirm(confirmed)

    def build(self) -> ft.Control:
        """Trả về toàn bộ giao diện của Chức năng 2."""
        return ft.Container(
            content=ft.Column(
                [
                    self.header_title,
                    self.header_sub,
                    self.stepper_banner,
                    ft.Container(height=5),
                    self.sample_selector,
                    ft.Container(height=5),
                    # Bố cục 2 khối đối chiếu
                    self.left_card,
                    self.right_card,
                    self.alert_box,
                    self.success_box,
                    ft.Container(height=10),
                    ft.Row(
                        [self.btn_confirm],
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=25,
            expand=True
        )
