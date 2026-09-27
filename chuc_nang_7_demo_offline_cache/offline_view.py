"""
Module: offline_view.py
Chức năng 7: Giao diện Bảng Điều Khiển Chế Độ Demo Offline & Ngân Hàng 12 Bài Mẫu (FR-10)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+)
Phiên bản Giao diện Ed-Tech 2.0 Thân thiện Học sinh & Ban Giám Khảo
"""

from typing import Optional, Callable, List
import flet as ft

from .offline_model import NetworkMode, KnowledgeStrand, OfflineSampleProblem
from .offline_bank import get_all_offline_problems, get_offline_problem_by_id
from .offline_engine import GLOBAL_OFFLINE_ENGINE, OfflineDemoEngine


class OfflineCacheControlView:
    """
    Component giao diện Flet cho Chức năng 7: Bảng điều khiển Demo Offline & Khám phá 12 Bài Mẫu.
    """
    def __init__(
        self,
        page: ft.Page,
        engine: Optional[OfflineDemoEngine] = None,
        on_select_problem_for_study: Optional[Callable[[OfflineSampleProblem], None]] = None,
        is_standalone: bool = False
    ):
        self.page = page
        self.engine = engine or GLOBAL_OFFLINE_ENGINE
        self.on_select_problem_for_study = on_select_problem_for_study
        self.is_standalone = is_standalone

        self.selected_strand: Optional[KnowledgeStrand] = None
        self.current_problem = self.engine.select_problem(self.engine.active_problem_id) or get_all_offline_problems()[0]

        # Khởi tạo giao diện
        self._build_controls()

    def _build_controls(self):
        # 1. Header độc lập (chỉ hiện khi chạy riêng Chức năng 7)
        self.standalone_header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CLOUD_OFF_ROUNDED, color=ft.Colors.AMBER_800, size=28),
                    ft.Text("Socrates Nhí 💡", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                ]),
                ft.Text("Chức năng 7: Chế độ Demo Offline & Cache 12 Bài Mẫu KHTN 7 Đủ 5 Pha (FR-10)", size=13, color=ft.Colors.GREY_700),
                ft.Container(height=5)
            ]),
            visible=self.is_standalone
        )

        # 2. Thẻ chỉ dẫn & Quy chuẩn Hội thi
        self.mission_card = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.SECURITY_UPDATE_GOOD_ROUNDED, color=ft.Colors.AMBER_800, size=24),
                    bgcolor=ft.Colors.AMBER_100,
                    radius=22
                ),
                ft.Column([
                    ft.Text("Vận Hành Lúc Thi: Chế độ Demo Offline & Ma Trận Rủi Ro (FR-10)", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.INDIGO_900),
                    ft.Text(
                        "Khi mạng hội trường yếu hoặc API timeout (> 20s), hệ thống tự động chuyển sang lời thoại cache "
                        "đã được duyệt sư phạm cho 12 bài mẫu KHTN 7 (đủ 5 pha mỗi bài), hiển thị rõ huy hiệu offline trung thực với Ban Giám Khảo!",
                        size=12,
                        color=ft.Colors.GREY_700
                    )
                ], spacing=2, expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.AMBER_200),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        # 3. THANH ĐIỀU KHIỂN TRẠNG THÁI MẠNG (Network Status & Simulation)
        self.status_badge = ft.Container(padding=ft.Padding(12, 6, 12, 6), border_radius=12)
        self.switch_offline = ft.Switch(
            label="Kích hoạt Chế độ Demo Offline",
            value=self.engine.is_offline(),
            active_color=ft.Colors.AMBER_700,
            on_change=self._on_toggle_offline
        )

        self.btn_simulate_timeout = ft.OutlinedButton(
            "Mô phỏng Mạng Chậm / Timeout (> 20s) ⏱️",
            icon=ft.Icons.TIMER_ROUNDED,
            on_click=lambda _: self._simulate_timeout_event()
        )

        self.network_card = ft.Container(
            content=ft.Row([
                ft.Row([
                    self.status_badge,
                    self.switch_offline
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self.btn_simulate_timeout
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            bgcolor=ft.Colors.WHITE,
            padding=12,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        # 4. BỘ LỌC 3 MẠCH KIẾN THỨC
        self.strand_filter_row = ft.Row(spacing=8, wrap=True)
        self._build_strand_filters()

        # 5. LƯỚI DANH SÁCH 12 BÀI MẪU
        self.problems_grid = ft.Row(wrap=True, spacing=10)
        self._refresh_problems_grid()

        # 6. KHU VỰC DUYỆT 5 PHA LỜI THOẠI CACHE CỦA BÀI ĐANG CHỌN
        self.cached_phases_column = ft.Column(spacing=8)
        self.active_problem_title = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
        self.active_problem_desc = ft.Text("", size=12, color=ft.Colors.GREY_700)

        self.detail_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.EXPLORE_ROUNDED, color=ft.Colors.INDIGO_700, size=20),
                        self.active_problem_title
                    ], spacing=6),
                    ft.FilledButton(
                        "Bắt Đầu Học Bài Này 🚀",
                        icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE),
                        on_click=lambda _: self._load_problem_to_app()
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.active_problem_desc,
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                ft.Text("Chuỗi 5 Pha Lời Thoại Socratic Đã Duyệt Sư Phạm (Tuyệt đối không rò đáp số):", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800),
                self.cached_phases_column
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=16,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        # Cập nhật hiển thị ban đầu
        self._update_status_badge()
        self._render_selected_problem_detail()

    def _update_status_badge(self):
        """Cập nhật huy hiệu trạng thái mạng."""
        if self.engine.mode == NetworkMode.OFFLINE_DEMO:
            self.status_badge.content = ft.Row([
                ft.Icon(ft.Icons.FLASH_ON_ROUNDED, color=ft.Colors.AMBER_800, size=16),
                ft.Text("⚡ ĐANG Ở CHẾ ĐỘ DEMO OFFLINE (BẬT SẴN CHO THI)", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
            ], spacing=6)
            self.status_badge.bgcolor = ft.Colors.AMBER_50
            self.status_badge.border = ft.Border.all(1.5, ft.Colors.AMBER_400)
            self.switch_offline.value = True

        elif self.engine.mode == NetworkMode.TIMEOUT_FALLBACK:
            self.status_badge.content = ft.Row([
                ft.Icon(ft.Icons.WARNING_ROUNDED, color=ft.Colors.RED_700, size=16),
                ft.Text("⚡ CHUYỂN CACHE DO TIMEOUT (> 20S)", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_900)
            ], spacing=6)
            self.status_badge.bgcolor = ft.Colors.RED_50
            self.status_badge.border = ft.Border.all(1.5, ft.Colors.RED_300)
            self.switch_offline.value = True

        else:
            self.status_badge.content = ft.Row([
                ft.Icon(ft.Icons.WIFI_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                ft.Text("🌐 TRỰC TUYẾN (OPENAI-COMPATIBLE)", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900)
            ], spacing=6)
            self.status_badge.bgcolor = ft.Colors.GREEN_50
            self.status_badge.border = ft.Border.all(1.5, ft.Colors.GREEN_300)
            self.switch_offline.value = False

    def _on_toggle_offline(self, e):
        """Người dùng gạt công tắc chuyển đổi chế độ mạng."""
        is_on = self.switch_offline.value
        self.engine.set_force_offline(is_on)
        self._update_status_badge()
        self.page.update()

    def _simulate_timeout_event(self):
        """Mô phỏng trường hợp mạng hội trường bị treo > 20 giây."""
        self.engine.simulate_api_call_with_timeout(22.5)
        self._update_status_badge()
        self.page.open(
            ft.SnackBar(
                content=ft.Text("⏱️ Đã mô phỏng API Timeout (22.5s > 20s): Hệ thống đã tự động chuyển sang Lời thoại Cache an toàn!"),
                bgcolor=ft.Colors.AMBER_800
            )
        )
        self.page.update()

    def _build_strand_filters(self):
        """Tạo các nút lọc theo mạch kiến thức."""
        filters = [
            (None, "Tất cả 12 Bài Mẫu 📚"),
            (KnowledgeStrand.PHYSICS, "Vật lý (4 bài) ⚛️"),
            (KnowledgeStrand.CHEMISTRY, "Hóa học (4 bài) 🧪"),
            (KnowledgeStrand.BIOLOGY, "Sinh học (4 bài) 🌿"),
        ]

        self.strand_filter_row.controls.clear()
        for strand_val, label in filters:
            is_active = (self.selected_strand == strand_val)
            bg = ft.Colors.INDIGO_700 if is_active else ft.Colors.WHITE
            fg = ft.Colors.WHITE if is_active else ft.Colors.INDIGO_900
            border = ft.Colors.INDIGO_700 if is_active else ft.Colors.INDIGO_200

            btn = ft.Container(
                content=ft.Text(label, size=11, weight=ft.FontWeight.BOLD, color=fg),
                bgcolor=bg,
                border=ft.Border.all(1, border),
                border_radius=8,
                padding=ft.Padding(10, 6, 10, 6),
                on_click=lambda _, s=strand_val: self._filter_strand(s)
            )
            self.strand_filter_row.controls.append(btn)

    def _filter_strand(self, strand: Optional[KnowledgeStrand]):
        self.selected_strand = strand
        self._build_strand_filters()
        self._refresh_problems_grid()
        self.page.update()

    def _refresh_problems_grid(self):
        """Cập nhật danh sách thẻ bài toán mẫu."""
        self.problems_grid.controls.clear()
        all_probs = get_all_offline_problems()

        if self.selected_strand:
            probs = [p for p in all_probs if p.strand == self.selected_strand]
        else:
            probs = all_probs

        for p in probs:
            is_selected = (p.problem_id == self.current_problem.problem_id)

            if p.strand == KnowledgeStrand.PHYSICS:
                theme_color = ft.Colors.INDIGO_700
                theme_bg = ft.Colors.INDIGO_50
            elif p.strand == KnowledgeStrand.CHEMISTRY:
                theme_color = ft.Colors.TEAL_700
                theme_bg = ft.Colors.TEAL_50
            else:
                theme_color = ft.Colors.GREEN_700
                theme_bg = ft.Colors.GREEN_50

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(p.problem_id, size=10, weight=ft.FontWeight.BOLD, color=theme_color),
                            bgcolor=ft.Colors.WHITE,
                            padding=ft.Padding(6, 2, 6, 2),
                            border_radius=6,
                            border=ft.Border.all(1, theme_color)
                        ),
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE_ROUNDED if is_selected else ft.Icons.RADIO_BUTTON_UNCHECKED,
                            color=theme_color if is_selected else ft.Colors.GREY_400,
                            size=16
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(p.title, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900, max_lines=1),
                    ft.Text(p.target_variable, size=10, color=ft.Colors.GREY_600, max_lines=1),
                ], spacing=4),
                width=245,
                padding=10,
                bgcolor=theme_bg if is_selected else ft.Colors.WHITE,
                border=ft.Border.all(2 if is_selected else 1, theme_color if is_selected else ft.Colors.GREY_300),
                border_radius=10,
                on_click=lambda _, pid=p.problem_id: self._select_problem(pid)
            )
            self.problems_grid.controls.append(card)

    def _select_problem(self, problem_id: str):
        """Khi người dùng chọn một bài toán mẫu từ danh sách."""
        prob = self.engine.select_problem(problem_id)
        if prob:
            self.current_problem = prob
            self._refresh_problems_grid()
            self._render_selected_problem_detail()
            self.page.update()

    def _render_selected_problem_detail(self):
        """Hiển thị chi tiết đề bài và chuỗi 5 pha Socratic của bài đang chọn."""
        p = self.current_problem
        self.active_problem_title.value = f"Bài {p.problem_id}: {p.title} ({p.strand.value})"
        self.active_problem_desc.value = p.problem_text

        self.cached_phases_column.controls.clear()

        phase_titles = {
            "clarify": ("1. Pha Làm Rõ Dữ Kiện (Clarify)", ft.Icons.LOOKS_ONE_ROUNDED, ft.Colors.BLUE_700),
            "recall": ("2. Pha Gợi Nhớ Công Thức (Recall)", ft.Icons.LOOKS_TWO_ROUNDED, ft.Colors.INDIGO_700),
            "reason": ("3. Pha Lập Luận Logic (Reason)", ft.Icons.LOOKS_3_ROUNDED, ft.Colors.TEAL_700),
            "check": ("4. Pha Kiểm Tra Thứ Nguyên (Check)", ft.Icons.LOOKS_4_ROUNDED, ft.Colors.AMBER_800),
            "generalize": ("5. Pha Khái Quát Hóa (Generalize)", ft.Icons.LOOKS_5_ROUNDED, ft.Colors.GREEN_700),
        }

        for phase_key in ["clarify", "recall", "reason", "check", "generalize"]:
            if phase_key in p.cached_phases:
                dlg = p.cached_phases[phase_key]
                p_title, p_icon, p_color = phase_titles.get(phase_key, (phase_key, ft.Icons.CHECK, ft.Colors.GREY_700))

                chip_row = ft.Row([
                    ft.Text("Gợi ý phản hồi học sinh:", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                    *[
                        ft.Container(
                            content=ft.Text(f'"{r}"', size=10, color=ft.Colors.INDIGO_800),
                            bgcolor=ft.Colors.INDIGO_50,
                            border=ft.Border.all(1, ft.Colors.INDIGO_200),
                            border_radius=6,
                            padding=ft.Padding(6, 2, 6, 2)
                        )
                        for r in dlg.quick_replies
                    ]
                ], wrap=True, spacing=4) if dlg.quick_replies else ft.Container()

                phase_box = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(p_icon, color=p_color, size=18),
                            ft.Text(p_title, size=12, weight=ft.FontWeight.BOLD, color=p_color),
                        ], spacing=6),
                        ft.Text(f"💬 Phản hồi AI: {dlg.feedback}", size=11, italic=True, color=ft.Colors.GREY_800),
                        ft.Text(f"❓ Câu hỏi gợi mở: {dlg.question}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ft.Row([
                            ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_600, size=14),
                            ft.Text(f"Gợi ý vi mô (≤ 140 ký tự): {dlg.micro_hint}", size=11, color=ft.Colors.GREY_700)
                        ], spacing=4),
                        chip_row
                    ], spacing=4),
                    bgcolor=ft.Colors.GREY_50,
                    border=ft.Border.all(1, ft.Colors.GREY_200),
                    border_radius=8,
                    padding=10
                )
                self.cached_phases_column.controls.append(phase_box)

    def _load_problem_to_app(self):
        """Chuyển bài mẫu sang màn hình học tập của ứng dụng chính."""
        if self.on_select_problem_for_study:
            self.on_select_problem_for_study(self.current_problem)
        else:
            self.page.open(
                ft.SnackBar(
                    content=ft.Text(f"Đã chọn bài: {self.current_problem.title} (Mã: {self.current_problem.problem_id})!"),
                    bgcolor=ft.Colors.GREEN_700
                )
            )

    def build(self) -> ft.Control:
        """Trả về giao diện hoàn chỉnh của Chức năng 7."""
        return ft.Container(
            content=ft.Column(
                [
                    self.standalone_header,
                    self.mission_card,
                    ft.Container(height=4),
                    self.network_card,
                    ft.Container(height=4),
                    ft.Row([
                        ft.Icon(ft.Icons.VIEW_LIST_ROUNDED, color=ft.Colors.INDIGO_700, size=18),
                        ft.Text("Ngân Hàng 12 Bài Mẫu KHTN 7 Đã Soạn Bản Đồ & Lời Thoại Cache:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                    ], spacing=6),
                    self.strand_filter_row,
                    self.problems_grid,
                    ft.Container(height=6),
                    self.detail_card
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=ft.Padding(20, 10, 20, 20)
        )
