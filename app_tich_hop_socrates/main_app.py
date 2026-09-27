"""
Module: main_app.py
Ứng dụng Tích hợp Hoàn chỉnh Socrates Nhí (Kết hợp Đầy đủ Chức năng 1, 2, 3, 4 & 5)
Phiên bản Giao diện Ed-Tech 2.0 Thân thiện Học sinh THCS
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Hành trình tương tác hoàn chỉnh xuyên suốt 5 Trạm Khám Phá:
1. Trạm 1: Tiếp nhận đề bài (Văn bản, Tải ảnh JPG/PNG <= 5MB, hoặc Đề mẫu KHTN 7).
2. Trạm 2: Trích xuất OCR & Soát lỗi công thức KHTN (Đo độ nét, Đối chiếu 2 cột, Thanh ký hiệu nhanh).
3. Trạm 3: Phân loại kiến thức bài toán & Bản đồ khái niệm cốt lõi (Cơ học, Hóa học, Sinh học, Lỗi thường gặp).
4. Trạm 4: Hội thoại Socratic gợi mở tư duy 5 pha (clarify -> recall -> reason -> check -> generalize) không phát đáp án sẵn!
5. Trạm 5: Sơ đồ Tư duy 3–6 nút & Khung tự đúc kết 3 dòng, Khảo sát 1–5 sao, Nhật ký ẩn danh (FR-06, FR-08, FR-09).
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import flet as ft

# Nhập các thành phần từ các thư mục chức năng độc lập
from chuc_nang_1_nhap_de.input_model import ProblemInput, InputType
from chuc_nang_1_nhap_de.ui_component import ProblemInputView

from chuc_nang_2_ocr_xac_nhan.ocr_model import ConfirmedProblem
from chuc_nang_2_ocr_xac_nhan.ocr_view import OcrConfirmationView
from chuc_nang_2_ocr_xac_nhan.formula_normalizer import normalize_khtn_text

from chuc_nang_3_phan_loai_kien_thuc.classifier_model import ClassificationResult
from chuc_nang_3_phan_loai_kien_thuc.classifier_view import KnowledgeClassifierView

from chuc_nang_4_hoi_thoai_socratic.socratic_view import SocraticChatView
from chuc_nang_4_hoi_thoai_socratic.socratic_model import SocraticPhase

from chuc_nang_5_so_do_tong_ket.mindmap_view import MindmapSummaryView
from chuc_nang_6_guardrail_chong_ro_dap_an.guardrail_view import GuardrailPlaygroundView
from chuc_nang_7_demo_offline_cache.offline_view import OfflineCacheControlView
from chuc_nang_7_demo_offline_cache.offline_engine import GLOBAL_OFFLINE_ENGINE

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
        self.page.bgcolor = ft.Colors.GREY_50

        if hasattr(self.page, "window") and self.page.window is not None:
            try:
                self.page.window.width = 1140
                self.page.window.height = 920
            except Exception:
                pass

        # Vùng chứa giao diện chính (Dynamic Content Container)
        self.content_area = ft.Container(expand=True)

        # Xây dựng thanh định vị toàn cục (Global Stepper)
        self._build_global_navigation()

        # Khởi đầu ở Bước 1: Nhập đề bài
        self.navigate_to_step_1()

    def _create_station_pill(self, step_num: int, title: str, subtitle: str) -> ft.Container:
        """Tạo thẻ giao diện cho một Trạm trong lộ trình 5 bước."""
        circle_badge = ft.Container(
            content=ft.Text(str(step_num), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
            width=24,
            height=24,
            border_radius=12,
            bgcolor=ft.Colors.GREY_200,
            alignment=ft.Alignment.CENTER
        )

        title_text = ft.Text(title, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800)
        subtitle_text = ft.Text(subtitle, size=9, color=ft.Colors.GREY_500)

        pill = ft.Container(
            content=ft.Row([
                circle_badge,
                ft.Column([title_text, subtitle_text], spacing=0)
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(8, 6, 8, 6),
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            bgcolor=ft.Colors.WHITE,
            expand=True
        )
        return pill

    def _build_global_navigation(self):
        """Xây dựng thanh tiêu đề và thanh tiến trình lộ trình 5 trạm sinh động."""
        self.app_brand = ft.Row(
            [
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_600, size=24),
                    bgcolor=ft.Colors.AMBER_100,
                    radius=20
                ),
                ft.Column(
                    [
                        ft.Text("SOCRATES NHÍ 💡", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ft.Text("Trợ lý AI gợi mở tư duy KHTN THCS • Cuộc thi Sáng tạo trẻ Quốc gia AI 2026", size=11, color=ft.Colors.GREY_700)
                    ],
                    spacing=1
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )

        self.pedagogy_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.INDIGO_700, size=14),
                ft.Text("Gia sư Socratic 5 Pha", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ]),
            bgcolor=ft.Colors.INDIGO_50,
            padding=ft.Padding(10, 5, 10, 5),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.INDIGO_200)
        )

        self.offline_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BOLT_ROUNDED, color=ft.Colors.AMBER_800, size=15),
                ft.Text("⚡ Demo Offline (12 Bài) 📚", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
            ]),
            bgcolor=ft.Colors.AMBER_50,
            padding=ft.Padding(10, 5, 10, 5),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.AMBER_300),
            tooltip="Bấm để mở Bảng điều khiển Demo Offline & Khám phá 12 bài mẫu KHTN 7 (FR-10)",
            on_click=lambda _: self._open_offline_dashboard()
        )

        self.guardrail_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SHIELD_ROUNDED, color=ft.Colors.GREEN_700, size=14),
                ft.Text("Khiên An Toàn 3 Tầng 🛡️", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900)
            ]),
            bgcolor=ft.Colors.GREEN_50,
            padding=ft.Padding(10, 5, 10, 5),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREEN_300),
            tooltip="Bấm để mở Bảng kiểm định & thử nghiệm bẻ khóa AI 3 tầng (FR-07)",
            on_click=lambda _: self._open_guardrail_dashboard()
        )

        # 3 Bước Khám phá Thân thiện với Học sinh
        self.pill_step_1 = self._create_station_pill(1, "Bước 1: Đặt câu hỏi", "Gõ câu hỏi / Mẫu / Chụp ảnh")
        self.pill_step_2 = self._create_station_pill(2, "Bước 2: Gia sư Socratic", "Gợi mở & Trao đổi trực tiếp 💬")
        self.pill_step_3 = self._create_station_pill(3, "Bước 3: Sơ đồ & Đúc kết", "Bản đồ tư duy & Tự đúc kết 🌟")

        self.station_pills = [
            self.pill_step_1,
            self.pill_step_2,
            self.pill_step_3
        ]

        arrow_icon = lambda: ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color=ft.Colors.INDIGO_300, size=18)

        self.stepper_bar = ft.Container(
            content=ft.Row(
                [
                    self.pill_step_1,
                    arrow_icon(),
                    self.pill_step_2,
                    arrow_icon(),
                    self.pill_step_3,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8
            ),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(12, 8, 12, 8),
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        self.header_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.app_brand,
                    ft.Row([self.pedagogy_badge, self.offline_btn, self.guardrail_btn], spacing=8)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=2),
                self.stepper_bar
            ], spacing=6),
            padding=ft.Padding(20, 12, 20, 6)
        )

    def _update_stepper_visuals(self, active_step: str):
        """Cập nhật giao diện Stepper 3 bước thân thiện học sinh."""
        # active_idx: 0 cho Nhập đề/OCR, 1 cho Gia sư Socratic, 2 cho Tổng kết
        if active_step in [AppStep.STEP_1_INPUT, AppStep.STEP_2_OCR]:
            active_idx = 0
        elif active_step in [AppStep.STEP_4_SOCRATIC, AppStep.STEP_3_CLASSIFIER]:
            active_idx = 1
        else:
            active_idx = 2

        orig_subs = [
            "Gõ câu hỏi / Mẫu / Chụp ảnh",
            "Gợi mở & Trao đổi trực tiếp 💬",
            "Bản đồ tư duy & Tự đúc kết 🌟"
        ]

        for idx, pill in enumerate(self.station_pills):
            row = pill.content
            badge = row.controls[0]
            texts = row.controls[1]
            title_text = texts.controls[0]
            sub_text = texts.controls[1]

            if idx < active_idx:
                # Đã hoàn thành (Completed) -> Xanh ngọc tươi sáng
                pill.bgcolor = ft.Colors.GREEN_50
                pill.border = ft.Border.all(1.5, ft.Colors.GREEN_300)
                pill.shadow = None
                badge.bgcolor = ft.Colors.GREEN_600
                badge.content = ft.Icon(ft.Icons.CHECK_ROUNDED, color=ft.Colors.WHITE, size=14)
                title_text.color = ft.Colors.GREEN_900
                title_text.weight = ft.FontWeight.BOLD
                sub_text.color = ft.Colors.GREEN_700
                sub_text.value = "✓ Đã hoàn thành"

            elif idx == active_idx:
                # Đang hoạt động (Active) -> Màu Indigo nổi bật có bóng mờ
                pill.bgcolor = ft.Colors.INDIGO_600
                pill.border = ft.Border.all(1.5, ft.Colors.INDIGO_700)
                pill.shadow = ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.25, ft.Colors.INDIGO_700), offset=ft.Offset(0, 2))
                badge.bgcolor = ft.Colors.WHITE
                badge.content = ft.Text(str(idx + 1), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800)
                title_text.color = ft.Colors.WHITE
                title_text.weight = ft.FontWeight.BOLD
                sub_text.color = ft.Colors.INDIGO_100
                sub_text.value = "🎯 Đang ở đây"

            else:
                # Chưa tới (Upcoming) -> Xám nhạt thanh lịch
                pill.bgcolor = ft.Colors.WHITE
                pill.border = ft.Border.all(1, ft.Colors.GREY_300)
                pill.shadow = None
                badge.bgcolor = ft.Colors.GREY_100
                badge.content = ft.Text(str(idx + 1), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600)
                title_text.color = ft.Colors.GREY_700
                title_text.weight = ft.FontWeight.W_500
                sub_text.color = ft.Colors.GREY_500
                sub_text.value = orig_subs[idx]
                pill.shadow = None
                badge.bgcolor = ft.Colors.GREY_100
                badge.content = ft.Text(str(idx + 1), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600)
                title_text.color = ft.Colors.GREY_700
                title_text.weight = ft.FontWeight.W_500
                sub_text.color = ft.Colors.GREY_500
                sub_text.value = orig_subs[idx]

        self.page.update()

    def _open_guardrail_dashboard(self):
        """Mở Bảng Điều Khiển An Toàn & Thử Nghiệm Bẻ Khóa AI (FR-07)."""
        playground = GuardrailPlaygroundView(page=self.page, is_standalone=False)

        def close_dialog(_):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.SHIELD_ROUNDED, color=ft.Colors.GREEN_700, size=24),
                ft.Text("Bảng Điều Khiển An Toàn & Thử Nghiệm Bẻ Khóa AI (FR-07)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=playground.build(),
                width=850,
                height=580,
            ),
            actions=[
                ft.FilledButton(
                    "Đóng bảng điều khiển",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _open_offline_dashboard(self):
        """Mở Bảng Điều Khiển Demo Offline & Ngân hàng 12 Bài Mẫu KHTN 7 (FR-10)."""
        def on_study_prob(prob):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

            # Nạp bài toán vào ứng dụng và vào thẳng trao đổi với Gia sư Socratic
            normalized_text = normalize_khtn_text(prob.problem_text)
            self.state.problem_input = ProblemInput(
                input_type=InputType.SAMPLE,
                text_content=prob.problem_text,
                is_confirmed=True
            )
            self.state.confirmed_problem = ConfirmedProblem(
                original_text=prob.problem_text,
                confirmed_text=normalized_text,
                source_type="sample"
            )
            from chuc_nang_3_phan_loai_kien_thuc.classifier_engine import KnowledgeClassifier
            self.state.classification_result = KnowledgeClassifier().classify_problem(normalized_text)
            self.navigate_to_step_4()

        view_7 = OfflineCacheControlView(
            page=self.page,
            on_select_problem_for_study=on_study_prob,
            is_standalone=False
        )

        def close_dialog(_):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CLOUD_OFF_ROUNDED, color=ft.Colors.AMBER_800, size=24),
                ft.Text("Bảng Điều Khiển Chế Độ Demo Offline (FR-10)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=view_7.build(),
                width=900,
                height=620,
            ),
            actions=[
                ft.FilledButton(
                    "Đóng bảng điều khiển",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def navigate_to_step_1(self):
        """Hiển thị Bước 1: Tiếp nhận đề bài."""
        self.state.current_step = AppStep.STEP_1_INPUT
        self._update_stepper_visuals(AppStep.STEP_1_INPUT)

        view_1 = ProblemInputView(
            page=self.page,
            on_confirm=self._on_step_1_confirmed,
            is_standalone=False
        )
        self.content_area.content = view_1.build()
        self.page.update()

    def _on_step_1_confirmed(self, problem: ProblemInput):
        """Khi học sinh gửi câu hỏi hoặc đề bài."""
        self.state.problem_input = problem

        # Nếu là ảnh chụp: Cho phép xem lại nhanh nội dung nhận diện từ ảnh
        if problem.input_type == InputType.IMAGE:
            self.navigate_to_step_2()
        else:
            # Gõ văn bản trực tiếp hoặc chọn bài mẫu: BỎ QUA HOÀN TOÀN OCR!
            # Tự động chuẩn hóa và phân tích kiến thức KHTN 7 trong nền
            normalized_text = normalize_khtn_text(problem.text_content)
            self.state.confirmed_problem = ConfirmedProblem(
                original_text=problem.text_content,
                confirmed_text=normalized_text,
                source_type="text"
            )
            from chuc_nang_3_phan_loai_kien_thuc.classifier_engine import KnowledgeClassifier
            self.state.classification_result = KnowledgeClassifier().classify_problem(normalized_text)

            # VÀO THẲNG PHÒNG TRAO ĐỔI VỚI GIA SƯ SOCRATIC!
            self.navigate_to_step_4()

    def navigate_to_step_2(self):
        """Hiển thị Xác nhận chữ nhận dạng từ ảnh chụp (Chỉ dành cho tải ảnh)."""
        self.state.current_step = AppStep.STEP_2_OCR
        self._update_stepper_visuals(AppStep.STEP_2_OCR)

        problem = self.state.problem_input
        img_path = problem.file_path if (problem and problem.file_path) else None

        view_2 = OcrConfirmationView(
            page=self.page,
            image_path=img_path,
            on_confirm=self._on_step_2_confirmed,
            is_standalone=False
        )

        btn_back_to_1 = ft.OutlinedButton(
            "Quay lại đặt câu hỏi / Chọn lại đề",
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            on_click=lambda _: self.navigate_to_step_1()
        )

        step_2_container = ft.Column(
            [
                ft.Row([btn_back_to_1], alignment=ft.MainAxisAlignment.START),
                view_2.build()
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO
        )

        self.content_area.content = step_2_container
        self.page.update()

    def _on_step_2_confirmed(self, confirmed_problem: ConfirmedProblem):
        """Khi học sinh xác nhận văn bản từ ảnh -> Vào thẳng trò chuyện với Gia sư!"""
        self.state.confirmed_problem = confirmed_problem
        from chuc_nang_3_phan_loai_kien_thuc.classifier_engine import KnowledgeClassifier
        self.state.classification_result = KnowledgeClassifier().classify_problem(confirmed_problem.confirmed_text)
        self.navigate_to_step_4()

    def _show_concept_map_dialog(self):
        """Mở modal Bản đồ Khái niệm & Cảnh báo lỗi thường gặp (Chức năng 3)."""
        problem_text = self.state.confirmed_problem.confirmed_text if self.state.confirmed_problem else ""

        def close_dialog(_=None):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        view_3 = KnowledgeClassifierView(
            page=self.page,
            problem_text=problem_text,
            on_proceed_to_socratic=lambda _: close_dialog(),
            on_back=lambda: close_dialog(),
            is_standalone=False
        )

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.MAP_ROUNDED, color=ft.Colors.INDIGO_700, size=24),
                ft.Text("Bản Đồ Khái Niệm & Cảnh Báo Lỗi Thường Gặp (FR-03)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=view_3.build(),
                width=880,
                height=580,
            ),
            actions=[
                ft.FilledButton(
                    "Đã hiểu, quay lại trò chuyện cùng Gia sư",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def navigate_to_step_3(self, confirmed_problem: ConfirmedProblem):
        """Dự phòng xem Bản đồ Khái niệm toàn trang nếu cần."""
        self._show_concept_map_dialog()

    def _on_step_3_proceed(self, classification_result: ClassificationResult):
        self.state.classification_result = classification_result
        self.navigate_to_step_4()

    def navigate_to_step_4(self):
        """Hiển thị Bước 2: Chu trình đối thoại cùng Gia sư Socrates Nhí."""
        self.state.current_step = AppStep.STEP_4_SOCRATIC
        self._update_stepper_visuals(AppStep.STEP_4_SOCRATIC)

        problem_text = self.state.confirmed_problem.confirmed_text if self.state.confirmed_problem else ""

        chat_view = SocraticChatView(
            page=self.page,
            problem_text=problem_text,
            on_session_complete=self._on_socratic_session_complete,
            is_standalone=False
        )

        btn_back_to_1 = ft.OutlinedButton(
            "Đặt câu hỏi khác / Chọn đề mới 📝",
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            on_click=lambda _: self.navigate_to_step_1()
        )

        btn_to_summary = ft.FilledButton(
            "Xem Sơ đồ Tư duy & Đúc kết (Bước 3) 🌟",
            icon=ft.Icons.WORKSPACE_PREMIUM_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            on_click=lambda _: self.navigate_to_step_5()
        )

        c_res = self.state.classification_result
        topic_title = c_res.topic if c_res else "Khoa học Tự nhiên 7"
        concepts_str = ", ".join(c_res.core_concepts) if (c_res and c_res.core_concepts) else "Quy luật KHTN"

        info_badge = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.INDIGO_700, size=16),
                    ft.Text(f"💡 {topic_title} • Khái niệm: {concepts_str}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                ft.TextButton(
                    "Xem Bản đồ Khái niệm 🗺️",
                    on_click=lambda _: self._show_concept_map_dialog()
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.INDIGO_50,
            padding=ft.Padding(12, 6, 12, 6),
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.INDIGO_200)
        )

        step_4_container = ft.Column(
            [
                ft.Row([btn_back_to_1, btn_to_summary], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                info_badge,
                chat_view.build()
            ],
            spacing=8,
            expand=True
        )

        self.content_area.content = step_4_container
        self.page.update()

    def _on_socratic_session_complete(self, summary_data: dict):
        """Xử lý khi học sinh hoàn thành toàn bộ chu trình Socratic -> Tự động chuyển sang Trạm 5!"""
        print(f"[Hoàn thành toàn bộ phiên] Lượt: {summary_data.get('turn_count')} - Pha: {summary_data.get('next_phase')}")
        self.navigate_to_step_5(turn_count=summary_data.get("turn_count", 4))

    def navigate_to_step_5(self, turn_count: int = 4):
        """Hiển thị Bước 5: Sơ đồ Tư duy & Tổng kết Khép phiên Học tập (Chức năng 5)."""
        self.state.current_step = AppStep.STEP_5_MINDMAP
        self._update_stepper_visuals(AppStep.STEP_5_MINDMAP)

        problem_text = self.state.confirmed_problem.confirmed_text if self.state.confirmed_problem else ""
        c_res = self.state.classification_result

        topic = c_res.topic if c_res else "Vật lý – Chuyển động và Tốc độ"
        strand = c_res.strand.value if c_res else "Vật lý THCS"
        facts = c_res.given_facts if c_res else ["s = 12 km", "t = 30 phút"]
        concepts = c_res.core_concepts if c_res else ["Tốc độ chuyển động"]
        target = c_res.target_variable if c_res else "Tốc độ v"

        view_5 = MindmapSummaryView(
            page=self.page,
            problem_text=problem_text,
            topic=topic,
            strand_name=strand,
            given_facts=facts,
            core_concepts=concepts,
            target_variable=target,
            total_turns=turn_count,
            on_restart=self.navigate_to_step_1,
            is_standalone=False
        )

        btn_back_to_4 = ft.OutlinedButton(
            "Quay lại trao đổi cùng Gia sư 💬",
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            on_click=lambda _: self.navigate_to_step_4()
        )

        step_5_container = ft.Column(
            [
                ft.Row([btn_back_to_4], alignment=ft.MainAxisAlignment.START),
                view_5.build()
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO
        )

        self.content_area.content = step_5_container
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
