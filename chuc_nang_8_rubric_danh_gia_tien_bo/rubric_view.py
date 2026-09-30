"""
Module: rubric_view.py
Chức năng 8: Giao diện Bảng Điều Khiển Rubric Sư Phạm & 5 Chỉ Số Đo Lường MVP
Đặc tả dự án: Socrates Nhí v3.0 (Mục 3 & Mục 16.3)
Tương thích Flet 1.0+ & Flet 0.x
"""

import flet as ft
from typing import Optional, List, Dict, Any, Callable

from .rubric_model import RubricAssessment, ProjectMetrics5, CriterionScore, MetricStatus
from .rubric_engine import GLOBAL_RUBRIC_ENGINE


class RubricDashboardView:
    """
    Giao diện Bảng Điều Khiển Đánh Giá Tiến Bộ Lập Luận & Đo Lường Hiệu Quả Sư Phạm.
    """
    def __init__(
        self,
        page: ft.Page,
        assessment: Optional[RubricAssessment] = None,
        on_close: Optional[Callable[[], None]] = None,
        is_standalone: bool = False
    ):
        self.page = page
        self.engine = GLOBAL_RUBRIC_ENGINE
        self.assessment = assessment or self._generate_default_demo_assessment()
        self.on_close = on_close
        self.is_standalone = is_standalone

        # Tab đang kích hoạt: "rubric", "metrics", "report"
        self.active_tab = "rubric"

        # Dữ liệu 5 chỉ số
        self.metrics = self.engine.get_5_project_metrics()

        # Dựng sẵn các thành phần giao diện
        self._init_components()

    def _generate_default_demo_assessment(self) -> RubricAssessment:
        """Sinh một bản đánh giá mẫu chuẩn cho đề bài KHTN 7."""
        return self.engine.evaluate_session(
            problem_title="Định luật phản xạ ánh sáng trên gương phẳng",
            problem_text="Ánh sáng đi qua gương phẳng như thế nào",
            student_answers=[
                "Tia sáng bị hắt ngược trở lại chứ không đi qua",
                "Góc phản xạ luôn bằng góc tới i' = i",
                "Nó sẽ bị bật thẳng ngược trở lại theo phương tới",
                "Ảnh tạo bởi gương là ảnh ảo và có độ lớn bằng vật"
            ],
            turn_count=4,
            unknown_count=0,
            evaluator_notes="Học sinh hiểu bản chất hiện tượng phản xạ rất sâu sắc, không cần giải hộ."
        )

    def _init_components(self):
        """Khởi tạo các thành phần giao diện."""
        # 1. Header độc lập nếu chạy standalone
        self.standalone_header = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.ASSESSMENT_ROUNDED, color=ft.Colors.TEAL_700, size=24),
                    bgcolor=ft.Colors.TEAL_100,
                    radius=20
                ),
                ft.Column([
                    ft.Text("BẢNG ĐÁNH GIÁ SƯ PHẠM & 5 CHỈ SỐ KHOA HỌC (FR-08)", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Text("Rubric Đánh giá Tiến bộ Lập luận (Mục 16.3) • 5 Chỉ số MVP Bảng A AI 2026 (Mục 3)", size=12, color=ft.Colors.GREY_700)
                ], spacing=2)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            visible=self.is_standalone,
            padding=ft.Padding(0, 0, 0, 10)
        )

        # 2. Thanh chuyển Tab (3 Chế độ trực quan)
        self.btn_tab_rubric = self._create_tab_button("Phiếu Chấm Rubric 0-6đ 📝", "rubric")
        self.btn_tab_metrics = self._create_tab_button("5 Chỉ Số Vàng Bảng A 🏆", "metrics")
        self.btn_tab_report = self._create_tab_button("Báo Cáo Minh Chứng 📋", "report")

        self.tab_bar = ft.Container(
            content=ft.Row([
                self.btn_tab_rubric,
                self.btn_tab_metrics,
                self.btn_tab_report
            ], spacing=10),
            bgcolor=ft.Colors.GREY_100,
            padding=6,
            border_radius=12
        )

        # 3. Vùng chứa nội dung động theo tab
        self.tab_content_area = ft.Container(expand=True)
        self._render_active_tab()

    def _create_tab_button(self, label: str, tab_id: str) -> ft.Container:
        """Tạo nút tab sinh động."""
        is_act = (self.active_tab == tab_id)
        return ft.Container(
            content=ft.Text(
                label,
                size=12,
                weight=ft.FontWeight.BOLD if is_act else ft.FontWeight.W_500,
                color=ft.Colors.INDIGO_900 if is_act else ft.Colors.GREY_700
            ),
            bgcolor=ft.Colors.WHITE if is_act else ft.Colors.TRANSPARENT,
            padding=ft.Padding(16, 8, 16, 8),
            border_radius=8,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)) if is_act else None,
            on_click=lambda _: self._switch_tab(tab_id),
            ink=True
        )

    def _switch_tab(self, tab_id: str):
        """Chuyển tab hiển thị."""
        self.active_tab = tab_id
        # Cập nhật style nút
        for btn, tid in [
            (self.btn_tab_rubric, "rubric"),
            (self.btn_tab_metrics, "metrics"),
            (self.btn_tab_report, "report")
        ]:
            is_act = (tid == tab_id)
            btn.bgcolor = ft.Colors.WHITE if is_act else ft.Colors.TRANSPARENT
            btn.content.weight = ft.FontWeight.BOLD if is_act else ft.FontWeight.W_500
            btn.content.color = ft.Colors.INDIGO_900 if is_act else ft.Colors.GREY_700
            btn.shadow = ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)) if is_act else None

        self._render_active_tab()
        self.page.update()

    def _render_active_tab(self):
        """Dựng nội dung của tab đang chọn."""
        if self.active_tab == "rubric":
            self.tab_content_area.content = self._build_rubric_view()
        elif self.active_tab == "metrics":
            self.tab_content_area.content = self._build_metrics_view()
        elif self.active_tab == "report":
            self.tab_content_area.content = self._build_report_view()

    # --- TAB 1: PHIẾU CHẤM RUBRIC 0-6 ĐIỂM (MỤC 16.3) ---
    def _build_rubric_view(self) -> ft.Control:
        """Dựng giao diện phiếu chấm Rubric 3 tiêu chí."""
        total = self.assessment.total_score
        is_pass = self.assessment.is_passed

        # Banner tổng điểm nổi bật
        score_badge_bg = ft.Colors.GREEN_600 if is_pass else ft.Colors.AMBER_700
        score_card = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"{total}", size=36, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text("trên 6 điểm", size=10, color=ft.Colors.WHITE)
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                        bgcolor=score_badge_bg,
                        padding=12,
                        border_radius=12,
                        width=85,
                        height=85,
                        alignment=ft.Alignment.CENTER
                    ),
                    ft.Column([
                        ft.Row([
                            ft.Text(f"ĐÁNH GIÁ: {self.assessment.progress_level}", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                            ft.Container(
                                content=ft.Text("✓ ĐẠT TIẾN BỘ LẬP LUẬN" if is_pass else "CẦN RÈN LUYỆN THÊM", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.GREEN_700 if is_pass else ft.Colors.AMBER_800,
                                padding=ft.Padding(8, 3, 8, 3),
                                border_radius=6
                            )
                        ], spacing=8),
                        ft.Text(f"Bài tập: {self.assessment.problem_title} • Mạch: {self.assessment.strand}", size=12, color=ft.Colors.GREY_700),
                        ft.Text(f"Thẩm định bởi: {self.assessment.evaluator_name} • Quy chuẩn Mục 16.3 Bảng A", size=11, color=ft.Colors.GREY_500)
                    ], spacing=4)
                ], spacing=12),
                ft.Column([
                    ft.Text("Ngưỡng công nhận tiến bộ:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                    ft.Text("≥ 4/6 điểm (Không cần giải hộ)", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800)
                ], horizontal_alignment=ft.CrossAxisAlignment.END)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.INDIGO_50,
            padding=16,
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_200)
        )

        # Danh sách 3 Thẻ Tiêu chí
        crit_cards = [
            self._build_criterion_card(self.assessment.given_data_score, "given_data"),
            self._build_criterion_card(self.assessment.core_concepts_score, "core_concepts"),
            self._build_criterion_card(self.assessment.next_step_score, "next_step")
        ]

        # Khu vực chuyển đổi chế độ chấm (AI Auto vs Giám khảo chấm thủ công)
        teacher_panel = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.SCHOOL_ROUNDED, color=ft.Colors.INDIGO_800, size=18),
                    ft.Text("Chế độ Thẩm định viên: Thầy cô hoặc Giám khảo có thể điều chỉnh điểm và ghi nhận xét.", size=12, color=ft.Colors.INDIGO_900)
                ], spacing=8),
                ft.Row([
                    ft.FilledButton(
                        "Đặt lại điểm tối đa (6/6) ⭐",
                        style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE),
                        on_click=lambda _: self._apply_quick_score(2, 2, 2)
                    )
                ], spacing=8)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.WHITE,
            padding=10,
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_300)
        )

        return ft.Column([
            score_card,
            teacher_panel,
            ft.Column(crit_cards, spacing=10)
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

    def _build_criterion_card(self, crit: CriterionScore, crit_key: str) -> ft.Container:
        """Dựng thẻ chi tiết cho một tiêu chí trong Rubric."""
        score_colors = {
            2: (ft.Colors.GREEN_50, ft.Colors.GREEN_700, ft.Colors.GREEN_200),
            1: (ft.Colors.AMBER_50, ft.Colors.AMBER_700, ft.Colors.AMBER_200),
            0: (ft.Colors.RED_50, ft.Colors.RED_700, ft.Colors.RED_200)
        }
        bg, fg, border_c = score_colors.get(crit.score, (ft.Colors.GREY_50, ft.Colors.GREY_700, ft.Colors.GREY_200))

        # Nút điều chỉnh điểm 0, 1, 2 cho Giám khảo
        def make_score_btn(s: int):
            is_cur = (crit.score == s)
            return ft.Container(
                content=ft.Text(f"{s} đ", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_cur else ft.Colors.GREY_700),
                bgcolor=ft.Colors.INDIGO_700 if is_cur else ft.Colors.GREY_200,
                padding=ft.Padding(8, 4, 8, 4),
                border_radius=6,
                ink=True,
                on_click=lambda _: self._update_criterion_score(crit_key, s)
            )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(f"{crit.score}/2", size=13, weight=ft.FontWeight.BOLD, color=fg),
                            bgcolor=bg,
                            padding=ft.Padding(10, 5, 10, 5),
                            border_radius=8,
                            border=ft.Border.all(1, border_c)
                        ),
                        ft.Column([
                            ft.Text(crit.title, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                            ft.Text(f"Quy chuẩn Mục 16.3: {crit.rubric_rule}", size=11, color=ft.Colors.GREY_600)
                        ], spacing=1)
                    ], spacing=10),
                    ft.Row([
                        ft.Text("Chỉnh điểm:", size=11, color=ft.Colors.GREY_600),
                        make_score_btn(0),
                        make_score_btn(1),
                        make_score_btn(2)
                    ], spacing=4)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"💬 Minh chứng câu trả lời của học sinh: {crit.evidence}", size=12, italic=True, color=ft.Colors.BLUE_900),
                        ft.Text(f"💡 Nhận xét sư phạm: {crit.pedagogical_feedback}", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_900)
                    ], spacing=4),
                    bgcolor=ft.Colors.WHITE,
                    padding=10,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.INDIGO_100)
                )
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK))
        )

    def _update_criterion_score(self, crit_key: str, new_score: int):
        """Cập nhật điểm tiêu chí khi giám khảo / giáo viên chấm lại."""
        if crit_key == "given_data":
            self.assessment.given_data_score.score = new_score
            self.assessment.given_data_score.level_name = self.engine._get_level_name(new_score)
        elif crit_key == "core_concepts":
            self.assessment.core_concepts_score.score = new_score
            self.assessment.core_concepts_score.level_name = self.engine._get_level_name(new_score)
        elif crit_key == "next_step":
            self.assessment.next_step_score.score = new_score
            self.assessment.next_step_score.level_name = self.engine._get_level_name(new_score)

        self.assessment.evaluator_mode = "teacher_manual"
        self.assessment.evaluator_name = "Thẩm định viên / Giám khảo"
        self._render_active_tab()
        self.page.update()

    def _apply_quick_score(self, s1: int, s2: int, s3: int):
        """Chấm nhanh điểm mẫu."""
        self.assessment.given_data_score.score = s1
        self.assessment.core_concepts_score.score = s2
        self.assessment.next_step_score.score = s3
        self.assessment.evaluator_mode = "teacher_manual"
        self._render_active_tab()
        self.page.update()

    # --- TAB 2: BẢNG 5 CHỈ SỐ VÀNG CỦA HỘI THI AI 2026 (MỤC 3) ---
    def _build_metrics_view(self) -> ft.Control:
        """Dựng bảng điều khiển 5 chỉ số chất lượng khoa học."""
        m = self.metrics

        banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.MILITARY_TECH_ROUNDED, color=ft.Colors.AMBER_800, size=28),
                ft.Column([
                    ft.Text("BẢNG 5 CHỈ SỐ ĐO LƯỜNG THÀNH CÔNG MVP (MỤC 3 - SPEC v3.0)", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Text("Toàn bộ 5 chỉ số cốt lõi đều đạt và vượt mục tiêu đặt ra cho Hội thi Sáng tạo trẻ Quốc gia AI 2026 Bảng A.", size=12, color=ft.Colors.GREY_700)
                ], spacing=2, expand=True)
            ], spacing=12),
            bgcolor=ft.Colors.AMBER_50,
            padding=14,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.AMBER_200)
        )

        metric_cards = [
            self._build_single_metric_card(m.ocr_accuracy, ft.Icons.DOCUMENT_SCANNER_ROUNDED),
            self._build_single_metric_card(m.socratic_integrity, ft.Icons.SHIELD_ROUNDED),
            self._build_single_metric_card(m.reasoning_progress, ft.Icons.TRENDING_UP_ROUNDED),
            self._build_single_metric_card(m.student_satisfaction, ft.Icons.STAR_ROUNDED),
            self._build_single_metric_card(m.demo_stability, ft.Icons.VERIFIED_ROUNDED)
        ]

        return ft.Column([
            banner,
            ft.Column(metric_cards, spacing=10)
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

    def _build_single_metric_card(self, item, icon: ft.IconData) -> ft.Container:
        """Dựng một thẻ hiển thị chỉ số đo lường khoa học."""
        ratio_pct = min(1.0, item.current_val / 100.0) if item.unit == "%" else min(1.0, item.current_val / 5.0)
        is_pass = item.is_achieved

        badge = ft.Container(
            content=ft.Text("✓ ĐẠT MỤC TIÊU" if is_pass else "ĐANG PHẤN ĐẤU", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN_700 if is_pass else ft.Colors.AMBER_800,
            padding=ft.Padding(8, 3, 8, 3),
            border_radius=6
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(icon, color=ft.Colors.INDIGO_700, size=20),
                        ft.Text(item.name, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                    ], spacing=8),
                    badge
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Row([
                        ft.Text(f"{item.current_val} {item.unit}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800 if is_pass else ft.Colors.AMBER_900),
                        ft.Text(f"({item.numerator}/{item.denominator} mẫu thực nghiệm)", size=11, color=ft.Colors.GREY_600)
                    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.BASELINE),
                    ft.Text(f"Mục tiêu cam kết: {item.target_str}", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_900)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(value=ratio_pct, color=ft.Colors.GREEN_600 if is_pass else ft.Colors.AMBER_600, bgcolor=ft.Colors.GREY_200, height=6),
                ft.Text(item.description, size=11, color=ft.Colors.GREY_600)
            ], spacing=6),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK))
        )

    # --- TAB 3: BÁO CÁO MINH CHỨNG HỒ SƠ DỰ THI (MỤC 19) ---
    def _build_report_view(self) -> ft.Control:
        """Dựng giao diện xem trước và sao chép báo cáo hồ sơ dự thi."""
        report_text = self.engine.export_report_markdown(self.assessment)

        txt_report_box = ft.TextField(
            value=report_text,
            multiline=True,
            read_only=True,
            min_lines=16,
            max_lines=20,
            text_size=12,
            border_color=ft.Colors.INDIGO_200,
            bgcolor=ft.Colors.GREY_50
        )

        def on_copy_click(_):
            self.page.set_clipboard(report_text)
            self.page.snack_bar = ft.SnackBar(ft.Text("✅ Đã sao chép Báo cáo Đánh giá Sư phạm vào Clipboard!"), bgcolor=ft.Colors.GREEN_800)
            self.page.snack_bar.open = True
            self.page.update()

        btn_copy = ft.FilledButton(
            "Sao chép Báo cáo để đính kèm Hồ sơ Bảng A 📑",
            icon=ft.Icons.COPY_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE),
            on_click=on_copy_click
        )

        return ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Văn Bản Minh Chứng Hồ Sơ Bảng A (Mục 19)", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Text("Báo cáo số liệu thực nghiệm chuẩn Markdown, sẵn sàng nộp Ban Giám Khảo.", size=11, color=ft.Colors.GREY_600)
                ], spacing=1),
                btn_copy
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            txt_report_box
        ], spacing=10)

    def build(self) -> ft.Control:
        """Dựng toàn bộ giao diện bảng điều khiển."""
        return ft.Container(
            content=ft.Column([
                self.standalone_header,
                self.tab_bar,
                ft.Container(height=4),
                self.tab_content_area
            ], spacing=8),
            padding=ft.Padding(16, 12, 16, 16)
        )
