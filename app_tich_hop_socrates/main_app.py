"""
Module: main_app.py
Ứng dụng Tích hợp Hoàn chỉnh Socrates Nhí (Kết hợp Chức năng 1 & Chức năng 2)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+)

Luồng trải nghiệm liền mạch:
1. Màn hình 1: Học sinh gõ đề văn bản, tải ảnh JPG/PNG qua FilePicker, hoặc chọn bài mẫu KHTN 7.
2. Học sinh nhấn "Xác nhận đề bài" -> Ứng dụng tự động chuyển cảnh mượt mà sang Màn hình 2.
3. Màn hình 2: Tự động chạy OCR + Đánh giá độ nét (nếu là ảnh) hoặc hiển thị văn bản công thức chuẩn hóa.
4. Học sinh sử dụng thanh ký hiệu KHTN nhanh (H₂O, CO₂, v², km/h, N, →) để sửa trực tiếp từng chỗ sai.
5. Học sinh nhấn "Xác nhận đề bài để bắt đầu học" -> Hoàn tất đề bài chuẩn hóa, sẵn sàng cho pha Socratic!
"""

import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft

# Nhập các thành phần từ 2 thư mục chức năng riêng biệt
from chuc_nang_1_nhap_de.input_model import ProblemInput, InputType
from chuc_nang_1_nhap_de.ui_component import ProblemInputView
from chuc_nang_2_ocr_xac_nhan.ocr_model import ConfirmedProblem
from chuc_nang_2_ocr_xac_nhan.ocr_view import OcrConfirmationView
from chuc_nang_2_ocr_xac_nhan.formula_normalizer import normalize_khtn_text

from app_tich_hop_socrates.app_state import SessionState, AppStep


class SocratesIntegratedApp:
    """
    Ứng dụng tích hợp điều phối toàn bộ hành trình tương tác của học sinh.
    """
    def __init__(self, page: ft.Page):
        self.page = page
        self.state = SessionState()

        # Cấu hình cửa sổ ứng dụng
        self.page.title = "Socrates Nhí 💡 - Trợ lý AI gợi mở tư duy KHTN (Bảng A - AI 2026)"
        self.page.theme_mode = ft.ThemeMode.LIGHT

        if hasattr(self.page, "window") and self.page.window is not None:
            try:
                self.page.window.width = 1000
                self.page.window.height = 900
            except Exception:
                pass

        # Vùng chứa giao diện chính (Dynamic Content Container)
        self.content_area = ft.Container(expand=True)

        # Xây dựng thanh định vị toàn cục (Global Stepper)
        self._build_global_navigation()

        # Hiển thị màn hình 1 ban đầu
        self.navigate_to_step_1()

    def _build_global_navigation(self):
        """Xây dựng thanh tiêu đề và thanh tiến trình xuyên suốt các bước."""
        self.app_brand = ft.Row(
            [
                ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_600, size=32),
                ft.Column(
                    [
                        ft.Text("SOCRATES NHÍ 💡", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ft.Text("Trợ lý AI hướng dẫn tự học KHTN • Cuộc thi Sáng tạo trẻ Quốc gia AI 2026", size=11, color=ft.Colors.GREY_700)
                    ],
                    spacing=2
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        self.offline_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SHIELD_ROUNDED, color=ft.Colors.GREEN_700, size=14),
                ft.Text("Chế độ Chuẩn: OpenAI-Compatible / Offline Ready", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.GREEN_900)
            ]),
            bgcolor=ft.Colors.GREEN_50,
            padding=ft.Padding(8, 4, 8, 4),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREEN_300)
        )

        # Các bước trong Stepper
        self.step_1_indicator = ft.Row([
            ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, color=ft.Colors.INDIGO_700, size=16),
            ft.Text("Bước 1: Nhập đề bài", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.INDIGO_900)
        ])

        self.step_2_indicator = ft.Row([
            ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=ft.Colors.GREY_500, size=16),
            ft.Text("Bước 2: Trích xuất & Sửa OCR", size=12, color=ft.Colors.GREY_600)
        ])

        self.step_3_indicator = ft.Row([
            ft.Icon(ft.Icons.LOCK_OUTLINE, color=ft.Colors.GREY_400, size=16),
            ft.Text("Bước 3: Gợi mở Socratic", size=12, color=ft.Colors.GREY_400)
        ])

        self.stepper_bar = ft.Container(
            content=ft.Row(
                [
                    self.step_1_indicator,
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400, size=18),
                    self.step_2_indicator,
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400, size=18),
                    self.step_3_indicator,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12
            ),
            bgcolor=ft.Colors.INDIGO_50,
            padding=10,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.INDIGO_100)
        )

        self.header_panel = ft.Container(
            content=ft.Column([
                ft.Row([self.app_brand, self.offline_badge], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=5),
                self.stepper_bar
            ], spacing=8),
            padding=ft.Padding(20, 15, 20, 5)
        )

    def _update_stepper_visuals(self, active_step: str):
        """Cập nhật giao diện Stepper theo bước hiện tại."""
        if active_step == AppStep.STEP_1_INPUT:
            self.step_1_indicator.controls[0].name = ft.Icons.RADIO_BUTTON_CHECKED
            self.step_1_indicator.controls[0].color = ft.Colors.INDIGO_700
            self.step_1_indicator.controls[1].weight = ft.FontWeight.BOLD
            self.step_1_indicator.controls[1].color = ft.Colors.INDIGO_900

            self.step_2_indicator.controls[0].name = ft.Icons.RADIO_BUTTON_UNCHECKED
            self.step_2_indicator.controls[0].color = ft.Colors.GREY_500
            self.step_2_indicator.controls[1].weight = ft.FontWeight.NORMAL
            self.step_2_indicator.controls[1].color = ft.Colors.GREY_600

        elif active_step == AppStep.STEP_2_OCR:
            self.step_1_indicator.controls[0].name = ft.Icons.CHECK_CIRCLE
            self.step_1_indicator.controls[0].color = ft.Colors.GREEN_600
            self.step_1_indicator.controls[1].color = ft.Colors.GREEN_800

            self.step_2_indicator.controls[0].name = ft.Icons.RADIO_BUTTON_CHECKED
            self.step_2_indicator.controls[0].color = ft.Colors.INDIGO_700
            self.step_2_indicator.controls[1].weight = ft.FontWeight.BOLD
            self.step_2_indicator.controls[1].color = ft.Colors.INDIGO_900

        elif active_step == AppStep.STEP_3_SOCRATIC:
            self.step_2_indicator.controls[0].name = ft.Icons.CHECK_CIRCLE
            self.step_2_indicator.controls[0].color = ft.Colors.GREEN_600
            self.step_2_indicator.controls[1].color = ft.Colors.GREEN_800

            self.step_3_indicator.controls[0].name = ft.Icons.RADIO_BUTTON_CHECKED
            self.step_3_indicator.controls[0].color = ft.Colors.INDIGO_700
            self.step_3_indicator.controls[1].weight = ft.FontWeight.BOLD
            self.step_3_indicator.controls[1].color = ft.Colors.INDIGO_900

        self.page.update()

    def navigate_to_step_1(self):
        """Hiển thị Màn hình 1: Nhập đề bài (sử dụng component chuc_nang_1_nhap_de)."""
        self.state.current_step = AppStep.STEP_1_INPUT
        self._update_stepper_visuals(AppStep.STEP_1_INPUT)

        # Tạo view từ chức năng 1 với callback tiếp nhận dữ liệu
        view_1 = ProblemInputView(
            page=self.page,
            on_confirm=self._on_step_1_confirmed
        )
        self.content_area.content = view_1.build()
        self.page.update()

    def _on_step_1_confirmed(self, problem: ProblemInput):
        """Xử lý khi học sinh hoàn thành Bước 1 -> Tự động chuyển tiếp sang Bước 2."""
        self.state.problem_input = problem
        self.navigate_to_step_2()

    def navigate_to_step_2(self):
        """Hiển thị Màn hình 2: Trích xuất OCR & Xác nhận (sử dụng component chuc_nang_2_ocr_xac_nhan)."""
        self.state.current_step = AppStep.STEP_2_OCR
        self._update_stepper_visuals(AppStep.STEP_2_OCR)

        problem = self.state.problem_input
        img_path = problem.file_path if (problem and problem.file_path) else None

        # Khởi tạo view từ chức năng 2
        view_2 = OcrConfirmationView(
            page=self.page,
            image_path=img_path,
            on_confirm=self._on_step_2_confirmed
        )

        # Nếu học sinh gõ đề bằng văn bản (không có ảnh), nạp thẳng nội dung vào editor của view 2
        if problem and problem.input_type in [InputType.TEXT, InputType.SAMPLE] and problem.text_content:
            normalized = normalize_khtn_text(problem.text_content)
            view_2.txt_editor.value = normalized
            view_2._update_live_preview(normalized)
            view_2.btn_confirm.disabled = False
            view_2.sharpness_badge.content.controls[1].value = "Đầu vào: Văn bản trực tiếp"

        # Bổ sung nút quay lại Bước 1
        btn_back_to_1 = ft.OutlinedButton(
            "Quay lại Bước 1 (Chọn lại đề bài)",
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.navigate_to_step_1()
        )

        step_2_container = ft.Column(
            [
                ft.Row([btn_back_to_1], alignment=ft.MainAxisAlignment.START),
                view_2.build()
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )

        self.content_area.content = step_2_container
        self.page.update()

    def _on_step_2_confirmed(self, confirmed_problem: ConfirmedProblem):
        """Xử lý khi học sinh hoàn thành Bước 2 (Chốt đề bài đã sửa đúng)."""
        self.state.confirmed_problem = confirmed_problem
        self._update_stepper_visuals(AppStep.STEP_3_SOCRATIC)

        # Hiển thị hộp thông báo chào đón chuyển sang Chức năng 3 & 4
        modal = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CELEBRATION, color=ft.Colors.AMBER_600),
                ft.Text("Xác nhận đề bài thành công!", weight=ft.FontWeight.BOLD)
            ]),
            content=ft.Column([
                ft.Text("Đề bài chuẩn hóa đã được lưu trữ an toàn trong phiên học:", size=13),
                ft.Container(
                    content=ft.Text(f"\"{confirmed_problem.confirmed_text}\"", italic=True, size=13),
                    bgcolor=ft.Colors.GREY_100,
                    padding=10,
                    border_radius=8
                ),
                ft.Container(height=5),
                ft.Text("📐 Công thức nhận diện: " + (", ".join(confirmed_problem.formulas) or "Đã chuẩn hóa"), size=12, color=ft.Colors.INDIGO_900),
                ft.Text("📏 Đơn vị đo: " + (", ".join(confirmed_problem.units) or "Chuẩn KHTN"), size=12, color=ft.Colors.GREEN_900),
                ft.Divider(),
                ft.Text("Sẵn sàng bước vào Bước 3: Phân loại kiến thức & Gợi mở Socratic 5 pha!", weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800)
            ], tight=True, spacing=6),
            actions=[
                ft.FilledButton(
                    "Bắt đầu học Socratic",
                    icon=ft.Icons.ROCKET_LAUNCH,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700),
                    on_click=lambda e: self._close_dialog()
                )
            ]
        )
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(modal)
        else:
            self.page.overlay.append(modal)
            modal.open = True
            self.page.update()

    def _close_dialog(self):
        if hasattr(self.page, "pop_dialog"):
            self.page.pop_dialog()
        self.page.update()

    def build(self) -> ft.Control:
        """Trả về toàn bộ khung ứng dụng hoàn chỉnh."""
        return ft.Column(
            [
                self.header_panel,
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                self.content_area
            ],
            spacing=0,
            expand=True
        )


def main(page: ft.Page):
    app = SocratesIntegratedApp(page)
    page.add(app.build())


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
    else:
        raise RuntimeError("Không tìm thấy hàm khởi chạy Flet!")
