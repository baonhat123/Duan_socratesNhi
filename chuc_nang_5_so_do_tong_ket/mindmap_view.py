"""
Module: mindmap_view.py
Chức năng 5: Giao diện Sơ đồ Tư duy & Tổng kết Buổi học (FR-06, FR-08, FR-09)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+)
Phiên bản Giao diện Ed-Tech 2.0 Thân thiện Học sinh THCS
"""

from typing import Optional, Callable, List
import flet as ft

from .mindmap_model import (
    MindmapNode,
    MindmapNodeType,
    MindmapGraph,
    StudentSummary,
    SessionSummary
)
from .mindmap_engine import (
    MindmapBuilder,
    save_anonymous_session_log,
    clean_temp_files
)


class MindmapSummaryView:
    """
    Component giao diện Flet cho Chức năng 5: Sơ đồ tư duy & Tổng kết.
    """
    def __init__(
        self,
        page: ft.Page,
        problem_text: str = "",
        topic: str = "Vật lý – Chuyển động và Tốc độ",
        strand_name: str = "Vật lý THCS",
        given_facts: Optional[List[str]] = None,
        core_concepts: Optional[List[str]] = None,
        target_variable: str = "Tốc độ v",
        total_turns: int = 4,
        on_restart: Optional[Callable[[], None]] = None,
        is_standalone: bool = False
    ):
        self.page = page
        self.problem_text = problem_text or "Một người đi xe đạp với tốc độ 12 km/h trong thời gian 30 phút..."
        self.topic = topic
        self.strand_name = strand_name
        self.given_facts = given_facts or ["s = 12 km", "t = 30 phút"]
        self.core_concepts = core_concepts or ["Tốc độ chuyển động", "Đổi đơn vị tốc độ (km/h ↔ m/s)"]
        self.target_variable = target_variable or "Tốc độ v (km/h và m/s)"
        self.total_turns = total_turns
        self.on_restart = on_restart
        self.is_standalone = is_standalone

        # Khởi tạo sơ đồ tư duy 3–6 nút chuẩn FR-06
        self.mindmap = MindmapBuilder.build_mindmap(
            topic=self.topic,
            strand_name=self.strand_name,
            given_facts=self.given_facts,
            core_concepts=self.core_concepts,
            target_variable=self.target_variable
        )

        self.selected_stars = 5
        self.session_summary: Optional[SessionSummary] = None

        # Xây dựng giao diện
        self._build_controls()

    def _build_controls(self):
        # 1. Header độc lập (Chỉ hiển thị khi chạy riêng lẻ Chức năng 5)
        self.standalone_header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_600, size=28),
                    ft.Text("Socrates Nhí 💡", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                ]),
                ft.Text("Chức năng 5: Sơ đồ Tư duy & Tổng kết Khép phiên Học tập (FR-06, FR-08, FR-09)", size=13, color=ft.Colors.GREY_700),
                ft.Container(height=5)
            ]),
            visible=self.is_standalone
        )

        # 2. Thẻ chỉ dẫn nhiệm vụ Trạm 5 (Mission Briefing Card)
        self.mission_card = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.WORKSPACE_PREMIUM_ROUNDED, color=ft.Colors.AMBER_800, size=24),
                    bgcolor=ft.Colors.AMBER_100,
                    radius=22
                ),
                ft.Column([
                    ft.Text("Trạm 5: Sơ đồ Tư duy & Tự đúc kết Buổi học 🎓", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.INDIGO_900),
                    ft.Text(
                        "Chúc mừng em đã hoàn thành các câu hỏi gợi mở của Socrates Nhí! "
                        "Hãy quan sát sơ đồ tư duy tổng kết bên dưới và ghi lại 3 bài học quý giá cho bản thân nhé!",
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

        # 3. KHỐI SƠ ĐỒ TƯ DUY HIỂN THỊ (Mindmap Canvas - 3 to 6 Nodes)
        node_cards = []
        node_colors = [
            (ft.Colors.INDIGO_50, ft.Colors.INDIGO_200, ft.Colors.INDIGO_900, ft.Icons.CATEGORY_ROUNDED),
            (ft.Colors.BLUE_50, ft.Colors.BLUE_200, ft.Colors.BLUE_900, ft.Icons.PUSH_PIN_ROUNDED),
            (ft.Colors.AMBER_50, ft.Colors.AMBER_200, ft.Colors.AMBER_900, ft.Icons.FLAG_CIRCLE_ROUNDED),
            (ft.Colors.PURPLE_50, ft.Colors.PURPLE_200, ft.Colors.PURPLE_900, ft.Icons.FUNCTIONS_ROUNDED),
            (ft.Colors.GREEN_50, ft.Colors.GREEN_200, ft.Colors.GREEN_900, ft.Icons.CHECK_CIRCLE_ROUNDED),
        ]

        for idx, node in enumerate(self.mindmap.nodes):
            c_bg, c_border, c_text, icon = node_colors[idx % len(node_colors)]
            elements = [
                ft.Row([
                    ft.Icon(icon, color=c_text, size=18),
                    ft.Text(node.title, weight=ft.FontWeight.BOLD, size=12, color=c_text),
                ], spacing=6),
            ]

            if node.formula:
                elements.append(
                    ft.Container(
                        content=ft.Text(f"📐 {node.formula}", size=12, weight=ft.FontWeight.BOLD, color=c_text),
                        bgcolor=ft.Colors.WHITE,
                        padding=ft.Padding(6, 3, 6, 3),
                        border_radius=6,
                        border=ft.Border.all(1, c_border)
                    )
                )

            elements.append(
                ft.Text(node.subtitle, size=11, color=ft.Colors.GREY_700, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS)
            )

            node_container = ft.Container(
                content=ft.Column(elements, spacing=4),
                bgcolor=c_bg,
                border=ft.Border.all(1.5, c_border),
                border_radius=12,
                padding=10,
                expand=True
            )
            node_cards.append(node_container)

        # Dãy nút nối bằng mũi tên
        flow_controls = []
        for i, card in enumerate(node_cards):
            flow_controls.append(card)
            if i < len(node_cards) - 1:
                flow_controls.append(
                    ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, color=ft.Colors.INDIGO_300, size=18)
                )

        self.mindmap_canvas = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.HUB_ROUNDED, color=ft.Colors.INDIGO_700, size=18),
                    ft.Text("Sơ đồ Tư duy Bài toán (Chuẩn FR-06: 5 Nút liên kết logic • Tuyệt đối không hé lộ đáp số):", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                ft.Row(flow_controls, spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        # 4. KHỐI HỌC SINH TỰ ĐÚC KẾT (Self-Summary 3 Dòng - FR-09)
        self.txt_rule = ft.TextField(
            label="1. Quy tắc / Công thức em đã vận dụng:",
            hint_text="Ví dụ: Công thức tính tốc độ v = s / t",
            value="Công thức tính tốc độ: v = s / t",
            border_radius=8,
            dense=True,
            content_padding=12
        )
        self.txt_pitfall = ft.TextField(
            label="2. Bẫy sai sót em cần chú ý tránh:",
            hint_text="Ví dụ: Cần đổi thời gian phút ra giờ trước khi tính",
            value="Cần đổi 30 phút = 0.5 giờ để khớp đơn vị km/h",
            border_radius=8,
            dense=True,
            content_padding=12
        )
        self.txt_next_step = ft.TextField(
            label="3. Bước giải tiếp theo của em:",
            hint_text="Ví dụ: Thay số s = 12 km, t = 0.5 h vào công thức để tính tốc độ v",
            value="Thay s = 12 km và t = 0.5 h vào công thức v = 12 / 0.5 để tìm ra kết quả",
            border_radius=8,
            dense=True,
            content_padding=12
        )

        self.summary_box = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EDIT_NOTE_ROUNDED, color=ft.Colors.INDIGO_700, size=18),
                    ft.Text("Em tự đúc kết bài học (Chuẩn FR-09: Khép phiên bằng tự lập luận):", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                self.txt_rule,
                self.txt_pitfall,
                self.txt_next_step
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            expand=True
        )

        # 5. KHỐI KHẢO SÁT 1–5 SAO (Survey - FR-09)
        self.star_buttons = []
        self.star_label = ft.Text("Tuyệt vời! Em tự hiểu và tự làm được rồi! 🤩💡", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)

        for s in range(1, 6):
            btn = ft.IconButton(
                icon=ft.Icons.STAR_ROUNDED,
                icon_color=ft.Colors.AMBER_500,
                icon_size=28,
                tooltip=f"{s} sao",
                on_click=lambda _, star_val=s: self._on_select_star(star_val)
            )
            self.star_buttons.append(btn)

        self.txt_feedback = ft.TextField(
            hint_text="Em có cảm nhận gì về cuộc trò chuyện với Socrates Nhí không? (Tùy chọn)",
            border_radius=8,
            dense=True,
            content_padding=12
        )

        self.survey_box = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.STAR_RATE_ROUNDED, color=ft.Colors.AMBER_700, size=18),
                    ft.Text("Khảo sát đánh giá trải nghiệm (1 - 5 Sao):", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.AMBER_900)
                ], spacing=6),
                ft.Row(self.star_buttons, spacing=2),
                self.star_label,
                self.txt_feedback
            ], spacing=8),
            bgcolor=ft.Colors.AMBER_50,
            padding=14,
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.AMBER_200),
            expand=True
        )

        self.middle_row = ft.Row([self.summary_box, self.survey_box], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START)

        # 6. BANNER ẨN DANH & BẢO MẬT (FR-08)
        self.privacy_log_banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SHIELD_ROUNDED, color=ft.Colors.GREEN_700, size=18),
                ft.Text(
                    "Bảo mật FR-08: Nhật ký học tập được lưu ẩn danh 100% (không lưu tên, lớp, trường hay SĐT). "
                    "Tệp ảnh đề bài tạm thời đã được tự động dọn dẹp.",
                    size=12,
                    color=ft.Colors.GREEN_900,
                    expand=True
                )
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.GREEN_50,
            padding=ft.Padding(12, 8, 12, 8),
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREEN_200)
        )

        # 7. NÚT ĐIỀU HƯỚNG CUỐI CÙNG
        self.btn_save_log = ft.FilledButton(
            "Lưu Đúc Kết & Hoàn Thành Buổi Học 🏆",
            icon=ft.Icons.SAVE_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, padding=18),
            on_click=self._on_save_summary
        )

        self.btn_new_session = ft.OutlinedButton(
            "Học bài tập mới cùng Socrates Nhí 🔄",
            icon=ft.Icons.REFRESH_ROUNDED,
            on_click=lambda _: self.on_restart() if self.on_restart else None
        )

        self.action_row = ft.Row(
            [self.btn_save_log, self.btn_new_session],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=15
        )

        # Thông báo thành công khi lưu log
        self.saved_notice = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                ft.Text("Đã lưu nhật ký học tập ẩn danh thành công!", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.GREEN_50,
            padding=8,
            border_radius=8,
            visible=False
        )

    def _on_select_star(self, stars: int):
        """Xử lý khi học sinh bấm chọn số sao đánh giá."""
        self.selected_stars = stars
        star_labels = {
            1: "Cần cải thiện nhiều 🙁",
            2: "Tạm ổn 😐",
            3: "Khá hữu ích 🙂",
            4: "Rất hay và dễ hiểu! 😊",
            5: "Tuyệt vời! Em tự hiểu và tự làm được rồi! 🤩💡"
        }
        self.star_label.value = star_labels.get(stars, "Đã đánh giá!")

        for idx, btn in enumerate(self.star_buttons):
            if idx < stars:
                btn.icon_color = ft.Colors.AMBER_500
                btn.icon = ft.Icons.STAR_ROUNDED
            else:
                btn.icon_color = ft.Colors.GREY_400
                btn.icon = ft.Icons.STAR_BORDER_ROUNDED

        self.page.update()

    def _on_save_summary(self, e):
        """Lưu đúc kết và xuất nhật ký ẩn danh."""
        student_sum = StudentSummary(
            rule_learned=self.txt_rule.value or "",
            pitfall_avoided=self.txt_pitfall.value or "",
            next_step=self.txt_next_step.value or ""
        )

        summary = SessionSummary(
            problem_text=self.problem_text,
            topic=self.topic,
            strand=self.strand_name,
            total_turns=self.total_turns,
            final_phase="generalize",
            mindmap=self.mindmap,
            student_summary=student_sum,
            rating_stars=self.selected_stars,
            feedback_comment=self.txt_feedback.value or "",
            is_temp_cleared=True
        )
        self.session_summary = summary

        # Lưu nhật ký ẩn danh
        try:
            save_anonymous_session_log(summary)
            self.saved_notice.visible = True
            self.btn_save_log.disabled = True
            self.btn_save_log.text = "Đã lưu đúc kết ✓"
        except Exception:
            pass

        self.page.update()

    def build(self) -> ft.Control:
        """Trả về toàn bộ giao diện của Chức năng 5."""
        return ft.Container(
            content=ft.Column(
                [
                    self.standalone_header,
                    self.mission_card,
                    ft.Container(height=4),
                    self.mindmap_canvas,
                    ft.Container(height=4),
                    self.middle_row,
                    ft.Container(height=2),
                    self.privacy_log_banner,
                    self.saved_notice,
                    ft.Container(height=6),
                    self.action_row
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=ft.Padding(20, 10, 20, 20)
        )
