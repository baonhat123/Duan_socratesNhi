"""
Module: mindmap_view.py
Chức năng 5: Giao diện Sơ đồ Tư duy & Tổng kết Buổi học (FR-06, FR-08, FR-09)
Đặc tả dự án: Socrates Nhí v3.0 (Tương thích Flet 1.0+)
Phiên bản Giao diện Ed-Tech 2.0 Thân thiện Học sinh THCS

Các cải tiến nâng cấp theo phản hồi của người dùng:
1. Sơ đồ mẫu dạng nhánh (Branching Mindmap Template / Tree Hub & Spoke).
2. Tự tay đúc kết: Học sinh gõ nội dung, các nhánh sơ đồ cập nhật trực tiếp theo thời gian thực (Live Preview).
3. Khái niệm Hoàn chỉnh & Kiến thức Cốt lõi Cần nhớ: Trình bày chuẩn mực SGK KHTN 7 theo từng phân môn.
4. Sổ tay Tự học của em (Personal Learning Notebook): Lưu trữ bền vững, mở xem lại mọi lúc mọi nơi.
"""

from typing import Optional, Callable, List, Dict, Any
from datetime import datetime
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
from .notebook_manager import (
    get_curated_concept_details,
    save_notebook_entry,
    load_notebook_entries,
    delete_notebook_entry
)


class MindmapSummaryView:
    """
    Component giao diện Flet cho Chức năng 5: Sơ đồ tư duy dạng nhánh & Sổ tay Tự học.
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
        self.core_concepts = core_concepts or ["Tốc độ chuyển động"]
        self.target_variable = target_variable or "Tốc độ v"
        self.total_turns = total_turns
        self.on_restart = on_restart
        self.is_standalone = is_standalone

        # Lấy tri thức chuẩn SGK theo đúng phân môn
        self.curated_concept = get_curated_concept_details(
            problem_text=self.problem_text,
            topic=self.topic,
            core_concepts=self.core_concepts
        )

        # Khởi tạo sơ đồ tư duy chuẩn FR-06
        self.mindmap = MindmapBuilder.build_mindmap(
            topic=self.topic,
            strand_name=self.strand_name,
            given_facts=self.given_facts,
            core_concepts=self.core_concepts,
            target_variable=self.target_variable
        )

        self.selected_stars = 5
        self.session_summary: Optional[SessionSummary] = None
        self.current_view_mode = "branch"  # "branch" (Sơ đồ nhánh) hoặc "flow" (Quy trình 5 bước)

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

        # 2. Thẻ chỉ dẫn nhiệm vụ Trạm 5
        self.mission_card = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.WORKSPACE_PREMIUM_ROUNDED, color=ft.Colors.AMBER_800, size=24),
                    bgcolor=ft.Colors.AMBER_100,
                    radius=22
                ),
                ft.Column([
                    ft.Text("Trạm 5: Sơ đồ Tư duy Dạng Nhánh & Tự Đúc Kết Buổi Học 🎓", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.INDIGO_900),
                    ft.Text(
                        "Chúc mừng em đã hoàn thành các câu hỏi gợi mở cùng Socrates Nhí! "
                        "Em hãy quan sát kiến thức chuẩn, tự tay đúc kết 3 bài học để hoàn thiện sơ đồ nhánh và lưu vào Sổ tay Tự học nhé!",
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

        # 3. THẺ KHÁI NIỆM HOÀN CHỈNH & KIẾN THỨC CỐT LÕI CẦN NHỚ (Chuẩn SGK KHTN 7)
        self.concept_card = self._build_concept_card()

        # 4. KHỐI HỌC SINH TỰ TAY ĐÚC KẾT (Input Fields - trống để học sinh tự gõ)
        self.txt_rule = ft.TextField(
            label="1. Quy tắc / Định luật em tự đúc kết sau buổi trò chuyện:",
            hint_text=f"Ví dụ: {self.curated_concept.get('suggested_rule', 'Định luật hoặc quy luật em đã rút ra')}",
            value="",
            border_radius=10,
            border_color=ft.Colors.INDIGO_200,
            focused_border_color=ft.Colors.INDIGO_600,
            cursor_color=ft.Colors.INDIGO_700,
            dense=True,
            content_padding=12,
            on_change=self._on_summary_text_changed
        )
        self.txt_pitfall = ft.TextField(
            label="2. Bẫy sai sót hoặc điểm em cần chú ý tránh:",
            hint_text=f"Ví dụ: {self.curated_concept.get('suggested_pitfall', 'Sai sót thường gặp khi vận dụng')}",
            value="",
            border_radius=10,
            border_color=ft.Colors.INDIGO_200,
            focused_border_color=ft.Colors.INDIGO_600,
            cursor_color=ft.Colors.INDIGO_700,
            dense=True,
            content_padding=12,
            on_change=self._on_summary_text_changed
        )
        self.txt_next_step = ft.TextField(
            label="3. Bước giải / Vận dụng tiếp theo của em:",
            hint_text=f"Ví dụ: {self.curated_concept.get('suggested_next_step', 'Kế hoạch hoặc bước thực hiện tiếp theo')}",
            value="",
            border_radius=10,
            border_color=ft.Colors.INDIGO_200,
            focused_border_color=ft.Colors.INDIGO_600,
            cursor_color=ft.Colors.INDIGO_700,
            dense=True,
            content_padding=12,
            on_change=self._on_summary_text_changed
        )

        # Các nhãn hiển thị trực tiếp trên nhánh sơ đồ
        self.live_branch_rule = ft.Text(
            "(Em hãy gõ vào ô 1 bên dưới để nhánh này tự cập nhật...)",
            size=11,
            italic=True,
            color=ft.Colors.INDIGO_400
        )
        self.live_branch_pitfall = ft.Text(
            "(Em hãy gõ vào ô 2 bên dưới để nhánh này tự cập nhật...)",
            size=11,
            italic=True,
            color=ft.Colors.AMBER_700
        )
        self.live_branch_next_step = ft.Text(
            "(Em hãy gõ vào ô 3 bên dưới để nhánh này tự cập nhật...)",
            size=11,
            italic=True,
            color=ft.Colors.GREEN_700
        )

        # 5. KHỐI SƠ ĐỒ TƯ DUY (Branching Mindmap Canvas)
        self.mindmap_container = ft.Container(
            content=self._build_mindmap_content(),
            bgcolor=ft.Colors.WHITE,
            padding=16,
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        # Hàng nút công cụ đúc kết nhanh
        self.summary_actions = ft.Row([
            ft.TextButton(
                "Điền mẫu gợi ý 💡",
                icon=ft.Icons.AUTO_FIX_HIGH_ROUNDED,
                on_click=self._fill_suggested_template
            ),
            ft.TextButton(
                "Xóa làm lại 🔄",
                icon=ft.Icons.CLEAR_ALL_ROUNDED,
                on_click=self._clear_inputs
            )
        ], spacing=10)

        self.summary_box = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EDIT_NOTE_ROUNDED, color=ft.Colors.INDIGO_700, size=18),
                    ft.Text("Em tự tay đúc kết bài học (Chuẩn FR-09: Khép phiên bằng tự lập luận):", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.INDIGO_900),
                ], spacing=6),
                ft.Text(
                    "💡 Khi em gõ vào 3 ô dưới đây, các nhánh trên sơ đồ tư duy phía trên sẽ tự động cập nhật trực tiếp!",
                    size=11,
                    color=ft.Colors.INDIGO_600
                ),
                self.txt_rule,
                self.txt_pitfall,
                self.txt_next_step,
                self.summary_actions
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            expand=True
        )

        # 6. KHỐI KHẢO SÁT 1–5 SAO (Survey - FR-09)
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

        # 7. BANNER BẢO MẬT & ẨN DANH (FR-08)
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

        # 8. THÔNG BÁO LƯU SỔ TAY THÀNH CÔNG
        self.saved_notice = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BOOKMARK_ADDED_ROUNDED, color=ft.Colors.GREEN_700, size=20),
                ft.Column([
                    ft.Text("🎉 Đã lưu bài học vào Sổ tay Tự học của em thành công!", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                    ft.Text("Em có thể bấm nút 'Mở Sổ tay Tự học 📖' bên cạnh để mở xem lại toàn bộ sơ đồ và khái niệm bất cứ lúc nào.", size=11, color=ft.Colors.GREEN_800)
                ], spacing=2, expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.GREEN_50,
            padding=12,
            border_radius=10,
            border=ft.Border.all(1.5, ft.Colors.GREEN_300),
            visible=False
        )

        # 9. HÀNG NÚT HÀNH ĐỘNG
        self.btn_save_notebook = ft.FilledButton(
            "Lưu vào Sổ tay Tự học của em 📓",
            icon=ft.Icons.BOOKMARK_ADDED_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, padding=16),
            on_click=self._on_save_summary
        )

        self.btn_open_notebook = ft.OutlinedButton(
            "Mở Sổ tay Tự học 📖",
            icon=ft.Icons.MENU_BOOK_ROUNDED,
            style=ft.ButtonStyle(padding=16),
            on_click=lambda _: self._open_notebook_dialog()
        )

        self.btn_new_session = ft.OutlinedButton(
            "Học bài tập mới 🔄",
            icon=ft.Icons.REFRESH_ROUNDED,
            style=ft.ButtonStyle(padding=16),
            on_click=lambda _: self.on_restart() if self.on_restart else None
        )

        self.action_row = ft.Row(
            [self.btn_save_notebook, self.btn_open_notebook, self.btn_new_session],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12
        )

    def _build_concept_card(self) -> ft.Container:
        """Xây dựng thẻ hiển thị Khái niệm Hoàn chỉnh & Kiến thức Cốt lõi Cần nhớ chuẩn SGK KHTN 7."""
        c_name = self.curated_concept.get("concept_name", self.topic)
        full_concept = self.curated_concept.get("full_concept", "Quy luật cốt lõi của bài học")
        takeaways = self.curated_concept.get("key_takeaways", [])
        formula = self.curated_concept.get("formula", "")
        pitfall = self.curated_concept.get("pitfall", "")

        takeaway_widgets = []
        for t in takeaways:
            takeaway_widgets.append(
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_600, size=15),
                    ft.Text(t, size=12, color=ft.Colors.GREY_800, expand=True)
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.START)
            )

        formula_badge = ft.Container()
        if formula:
            formula_badge = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.FUNCTIONS_ROUNDED, color=ft.Colors.INDIGO_900, size=16),
                    ft.Text(f"Quy luật / Biểu thức: {formula}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                bgcolor=ft.Colors.INDIGO_100,
                padding=ft.Padding(10, 4, 10, 4),
                border_radius=8,
                border=ft.Border.all(1, ft.Colors.INDIGO_300)
            )

        pitfall_badge = ft.Container()
        if pitfall:
            pitfall_badge = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_900, size=16),
                    ft.Text(f"Bẫy sai lầm cần nhớ: {pitfall}", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.AMBER_900, expand=True)
                ], spacing=6),
                bgcolor=ft.Colors.AMBER_50,
                padding=ft.Padding(10, 6, 10, 6),
                border_radius=8,
                border=ft.Border.all(1, ft.Colors.AMBER_300)
            )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.INDIGO_700, size=20),
                        ft.Text("Khái niệm Hoàn chỉnh & Kiến thức Cốt lõi Cần nhớ (Chuẩn SGK KHTN 7) 💡", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ], spacing=8),
                    formula_badge
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                # Khối định nghĩa hoàn chỉnh
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"📌 {c_name}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ft.Text(full_concept, size=12, color=ft.Colors.GREY_800, selectable=True)
                    ], spacing=4),
                    bgcolor=ft.Colors.INDIGO_50,
                    padding=12,
                    border_radius=10,
                    border=ft.Border.all(1, ft.Colors.INDIGO_200)
                ),

                # Các điểm cốt lõi cần nhớ
                ft.Column([
                    ft.Text("🔑 Các điểm cốt lõi cần ghi nhớ:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                    *takeaway_widgets
                ], spacing=5),

                pitfall_badge
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=14,
            border=ft.Border.all(1.5, ft.Colors.INDIGO_200),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

    def _build_mindmap_content(self) -> ft.Control:
        """Xây dựng khung hiển thị sơ đồ: cho phép chuyển giữa Sơ đồ dạng nhánh (Tree) và Sơ đồ luồng (Flow)."""
        toggle_btn = ft.TextButton(
            "Chuyển sang dạng luồng quy trình (Flow) ➡️" if self.current_view_mode == "branch" else "Chuyển sang dạng nhánh cây (Tree) 🌿",
            icon=ft.Icons.SWAP_HORIZ_ROUNDED,
            on_click=self._toggle_view_mode
        )

        header_row = ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.HUB_ROUNDED, color=ft.Colors.INDIGO_700, size=20),
                ft.Text(
                    "Sơ đồ Tư duy Dạng Nhánh (Mẫu Cây Trí Tuệ KHTN) 🌿" if self.current_view_mode == "branch" else "Sơ đồ Quy trình 5 Bước Logic (Chuẩn FR-06) ➡️",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.INDIGO_900
                ),
            ], spacing=6),
            toggle_btn
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        if self.current_view_mode == "branch":
            mindmap_body = self._build_branching_tree()
        else:
            mindmap_body = self._build_flow_cards()

        return ft.Column([
            header_row,
            ft.Text(
                "Sơ đồ tương tác: Khi em gõ 3 bài học đúc kết bên dưới, các nhánh sơ đồ sẽ hiển thị ngay lập tức!",
                size=11,
                color=ft.Colors.GREY_600
            ),
            mindmap_body
        ], spacing=10)

    def _build_branching_tree(self) -> ft.Control:
        """
        Xây dựng Sơ đồ Tư duy Dạng Nhánh (Tree / Hub & Spoke):
        Gốc (Trung tâm) -> 3 Nhánh chính tỏa ra:
        - Nhánh 1: Hiện tượng & Dữ kiện bài toán (Dữ kiện đã cho + Mục tiêu cần tìm)
        - Nhánh 2: Định luật khoa học & Em tự đúc kết (Định luật SGK + Text học sinh gõ ô 1)
        - Nhánh 3: Bẫy sai sót & Bước tiếp theo (Text học sinh gõ ô 2 + Text ô 3)
        """
        # Nút Gốc (Root Hub): Vấn đề & Chủ đề bài học
        root_node = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_400, size=24),
                ft.Text("VẤN ĐỀ TRUNG TÂM", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_70),
                ft.Text(self.mindmap.nodes[0].title, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    content=ft.Text(self.mindmap.nodes[0].subtitle, size=10, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                    padding=ft.Padding(6, 2, 6, 2),
                    border_radius=6
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            bgcolor=ft.Colors.INDIGO_900,
            padding=14,
            border_radius=14,
            border=ft.Border.all(2, ft.Colors.INDIGO_400),
            width=210,
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.18, ft.Colors.INDIGO_900), offset=ft.Offset(0, 3))
        )

        # Nhánh 1: Hiện tượng & Dữ kiện (Xanh Lam)
        facts_sub = self.mindmap.nodes[1].subtitle if len(self.mindmap.nodes) > 1 else "Dữ kiện đề bài"
        target_sub = self.mindmap.nodes[2].subtitle if len(self.mindmap.nodes) > 2 else "Mục tiêu cần tìm"

        branch_1 = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SPA_ROUNDED, color=ft.Colors.BLUE_700, size=16),
                    ft.Text("Nhánh 1: Hiện tượng & Dữ kiện", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.BLUE_900)
                ], spacing=4),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PUSH_PIN_ROUNDED, color=ft.Colors.BLUE_800, size=14),
                            ft.Text("Dữ kiện đã cho:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
                        ], spacing=4),
                        ft.Text(facts_sub, size=11, color=ft.Colors.GREY_800)
                    ], spacing=2),
                    bgcolor=ft.Colors.WHITE,
                    padding=8,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.BLUE_200)
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.FLAG_CIRCLE_ROUNDED, color=ft.Colors.BLUE_800, size=14),
                            ft.Text("Mục tiêu cần tìm:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
                        ], spacing=4),
                        ft.Text(target_sub, size=11, color=ft.Colors.GREY_800)
                    ], spacing=2),
                    bgcolor=ft.Colors.WHITE,
                    padding=8,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.BLUE_200)
                )
            ], spacing=6),
            bgcolor=ft.Colors.BLUE_50,
            padding=10,
            border_radius=12,
            border=ft.Border.all(1.5, ft.Colors.BLUE_300),
            expand=True
        )

        # Nhánh 2: Định luật & Đúc kết của em (Tím)
        concept_title = self.curated_concept.get("concept_name", "Định luật khoa học")
        concept_formula = self.curated_concept.get("formula", "")

        branch_2 = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.BOLT_ROUNDED, color=ft.Colors.PURPLE_700, size=16),
                    ft.Text("Nhánh 2: Định luật & Em tự đúc kết", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.PURPLE_900)
                ], spacing=4),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.FUNCTIONS_ROUNDED, color=ft.Colors.PURPLE_800, size=14),
                            ft.Text("Định luật chuẩn SGK:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900)
                        ], spacing=4),
                        ft.Text(f"{concept_title}" + (f" ({concept_formula})" if concept_formula else ""), size=11, color=ft.Colors.GREY_800)
                    ], spacing=2),
                    bgcolor=ft.Colors.WHITE,
                    padding=8,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.PURPLE_200)
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.EDIT_ROUNDED, color=ft.Colors.PURPLE_800, size=14),
                            ft.Text("Quy tắc em tự đúc kết:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900)
                        ], spacing=4),
                        self.live_branch_rule
                    ], spacing=2),
                    bgcolor=ft.Colors.PURPLE_100,
                    padding=8,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.PURPLE_300)
                )
            ], spacing=6),
            bgcolor=ft.Colors.PURPLE_50,
            padding=10,
            border_radius=12,
            border=ft.Border.all(1.5, ft.Colors.PURPLE_300),
            expand=True
        )

        # Nhánh 3: Bẫy sai lầm & Bước tiếp theo (Xanh ngọc / Hổ phách)
        branch_3 = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SHIELD_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                    ft.Text("Nhánh 3: Bẫy sai lầm & Tự kiểm", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.GREEN_900)
                ], spacing=4),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.WARNING_ROUNDED, color=ft.Colors.AMBER_800, size=14),
                            ft.Text("Bẫy em cần tránh:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
                        ], spacing=4),
                        self.live_branch_pitfall
                    ], spacing=2),
                    bgcolor=ft.Colors.AMBER_50,
                    padding=8,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.AMBER_300)
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.ROCKET_LAUNCH_ROUNDED, color=ft.Colors.GREEN_800, size=14),
                            ft.Text("Bước giải tiếp theo:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900)
                        ], spacing=4),
                        self.live_branch_next_step
                    ], spacing=2),
                    bgcolor=ft.Colors.GREEN_50,
                    padding=8,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.GREEN_300)
                )
            ], spacing=6),
            bgcolor=ft.Colors.TEAL_50 if hasattr(ft.Colors, "TEAL_50") else ft.Colors.GREEN_50,
            padding=10,
            border_radius=12,
            border=ft.Border.all(1.5, ft.Colors.GREEN_300),
            expand=True
        )

        branches_column = ft.Column([
            branch_1,
            branch_2,
            branch_3
        ], spacing=10, expand=True)

        connector_col = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, color=ft.Colors.INDIGO_300, size=20),
                ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, color=ft.Colors.INDIGO_300, size=20),
                ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, color=ft.Colors.INDIGO_300, size=20),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND, height=360),
            width=30
        )

        return ft.Row([
            root_node,
            connector_col,
            branches_column
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

    def _build_flow_cards(self) -> ft.Control:
        """Xây dựng Sơ đồ quy trình 5 bước logic liên tiếp (FR-06 chuẩn)."""
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

        flow_controls = []
        for i, card in enumerate(node_cards):
            flow_controls.append(card)
            if i < len(node_cards) - 1:
                flow_controls.append(
                    ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, color=ft.Colors.INDIGO_300, size=18)
                )

        return ft.Row(flow_controls, spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _toggle_view_mode(self, e):
        """Chuyển đổi giữa sơ đồ dạng nhánh và sơ đồ dạng luồng."""
        self.current_view_mode = "flow" if self.current_view_mode == "branch" else "branch"
        self.mindmap_container.content = self._build_mindmap_content()
        self.page.update()

    def _on_summary_text_changed(self, e):
        """Cập nhật nội dung trên các nhánh sơ đồ tư duy ngay khi học sinh gõ chữ (Live Preview)."""
        rule_val = (self.txt_rule.value or "").strip()
        pitfall_val = (self.txt_pitfall.value or "").strip()
        next_val = (self.txt_next_step.value or "").strip()

        if rule_val:
            self.live_branch_rule.value = f"✍️ {rule_val}"
            self.live_branch_rule.italic = False
            self.live_branch_rule.color = ft.Colors.PURPLE_900
        else:
            self.live_branch_rule.value = "(Em hãy gõ vào ô 1 bên dưới để nhánh này tự cập nhật...)"
            self.live_branch_rule.italic = True
            self.live_branch_rule.color = ft.Colors.INDIGO_400

        if pitfall_val:
            self.live_branch_pitfall.value = f"⚠️ {pitfall_val}"
            self.live_branch_pitfall.italic = False
            self.live_branch_pitfall.color = ft.Colors.AMBER_900
        else:
            self.live_branch_pitfall.value = "(Em hãy gõ vào ô 2 bên dưới để nhánh này tự cập nhật...)"
            self.live_branch_pitfall.italic = True
            self.live_branch_pitfall.color = ft.Colors.AMBER_700

        if next_val:
            self.live_branch_next_step.value = f"🚀 {next_val}"
            self.live_branch_next_step.italic = False
            self.live_branch_next_step.color = ft.Colors.GREEN_900
        else:
            self.live_branch_next_step.value = "(Em hãy gõ vào ô 3 bên dưới để nhánh này tự cập nhật...)"
            self.live_branch_next_step.italic = True
            self.live_branch_next_step.color = ft.Colors.GREEN_700

        self.page.update()

    def _fill_suggested_template(self, e):
        """Tự động điền mẫu gợi ý từ SGK để học sinh tham khảo chỉnh sửa."""
        self.txt_rule.value = self.curated_concept.get("suggested_rule", "")
        self.txt_pitfall.value = self.curated_concept.get("suggested_pitfall", "")
        self.txt_next_step.value = self.curated_concept.get("suggested_next_step", "")
        self._on_summary_text_changed(None)

    def _clear_inputs(self, e):
        """Xóa trắng các ô để học sinh tự tay viết lại từ đầu."""
        self.txt_rule.value = ""
        self.txt_pitfall.value = ""
        self.txt_next_step.value = ""
        self._on_summary_text_changed(None)

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
        """Lưu đúc kết vào Sổ tay Tự học và xuất nhật ký ẩn danh."""
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

        # 1. Lưu vào Sổ tay Tự học (Personal Notebook)
        notebook_entry = {
            "topic": self.topic,
            "strand": self.strand_name,
            "problem_text": self.problem_text,
            "concept_name": self.curated_concept.get("concept_name", self.topic),
            "full_concept": self.curated_concept.get("full_concept", ""),
            "key_takeaways": self.curated_concept.get("key_takeaways", []),
            "formula": self.curated_concept.get("formula", ""),
            "pitfall": self.curated_concept.get("pitfall", ""),
            "rule_learned": self.txt_rule.value or self.curated_concept.get("suggested_rule", ""),
            "pitfall_avoided": self.txt_pitfall.value or self.curated_concept.get("suggested_pitfall", ""),
            "next_step": self.txt_next_step.value or self.curated_concept.get("suggested_next_step", ""),
            "rating_stars": self.selected_stars,
            "feedback_comment": self.txt_feedback.value or "",
            "total_turns": self.total_turns,
            "mindmap_nodes": [
                {"title": n.title, "subtitle": n.subtitle, "formula": n.formula} for n in self.mindmap.nodes
            ]
        }

        # Gắn thông tin tài khoản học sinh tác giả
        try:
            from app_tich_hop_socrates.auth_service import AuthService
            cur_user = AuthService.get_current_user()
            notebook_entry["author_username"] = cur_user.username
            notebook_entry["author_name"] = cur_user.display_name
            notebook_entry["author_avatar"] = cur_user.avatar
            notebook_entry["author_class"] = cur_user.grade_class
        except Exception:
            pass

        save_notebook_entry(notebook_entry)

        # 2. Lưu nhật ký ẩn danh FR-08
        try:
            save_anonymous_session_log(summary)
        except Exception:
            pass

        # 3. Cập nhật giao diện
        self.saved_notice.visible = True
        self.btn_save_notebook.disabled = True
        self.btn_save_notebook.text = "Đã lưu vào Sổ tay Tự học ✓"
        self.page.update()

    def _open_notebook_dialog(self):
        """Mở Hộp thoại Sổ tay Tự học (Notebook Viewer) để học sinh tra cứu các bài học đã lưu."""
        entries = load_notebook_entries()

        # Chi tiết bài học đang xem
        detail_container = ft.Container(expand=True)

        def display_entry_detail(item: Dict[str, Any]):
            takeaways_list = []
            for t in item.get("key_takeaways", []):
                takeaways_list.append(
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_600, size=14),
                        ft.Text(t, size=11, color=ft.Colors.GREY_800, expand=True)
                    ], spacing=4)
                )

            detail_container.content = ft.Column([
                ft.Row([
                    ft.Text(item.get("topic", "Khoa học Tự nhiên 7"), size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Text(item.get("created_at", ""), size=11, color=ft.Colors.GREY_600)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                # Đề bài
                ft.Container(
                    content=ft.Column([
                        ft.Text("❓ Vấn đề / Câu hỏi nghiên cứu:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Text(item.get("problem_text", "Không có nội dung"), size=11, color=ft.Colors.GREY_900)
                    ], spacing=2),
                    bgcolor=ft.Colors.GREY_50,
                    padding=8,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.GREY_200)
                ),

                # Khái niệm hoàn chỉnh
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.INDIGO_700, size=16),
                            ft.Text(f"💡 {item.get('concept_name', 'Khái niệm chuẩn')}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ], spacing=4),
                        ft.Text(item.get("full_concept", ""), size=11, color=ft.Colors.GREY_800),
                        *takeaways_list
                    ], spacing=4),
                    bgcolor=ft.Colors.INDIGO_50,
                    padding=10,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.INDIGO_200)
                ),

                # Đúc kết của học sinh
                ft.Container(
                    content=ft.Column([
                        ft.Text("✍️ 3 Điều em đã tự đúc kết:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900),
                        ft.Text(f"1. Quy tắc vận dụng: {item.get('rule_learned', '(Chưa ghi)')}", size=11, color=ft.Colors.GREY_800),
                        ft.Text(f"2. Bẫy sai sót: {item.get('pitfall_avoided', '(Chưa ghi)')}", size=11, color=ft.Colors.GREY_800),
                        ft.Text(f"3. Bước tiếp theo: {item.get('next_step', '(Chưa ghi)')}", size=11, color=ft.Colors.GREY_800),
                    ], spacing=3),
                    bgcolor=ft.Colors.PURPLE_50,
                    padding=10,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.PURPLE_200)
                ),

                # Đánh giá
                ft.Row([
                    ft.Text(f"Đánh giá: {'⭐' * item.get('rating_stars', 5)}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900),
                    ft.Text(f"Phản hồi: {item.get('feedback_comment', 'Không có')}", size=11, italic=True, color=ft.Colors.GREY_600)
                ], spacing=10)
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

            self.page.update()

        # Danh sách bài học bên trái
        list_items = []
        if entries:
            for entry in entries:
                def make_click_handler(item_ref=entry):
                    return lambda _: display_entry_detail(item_ref)

                card = ft.Container(
                    content=ft.Column([
                        ft.Text(entry.get("concept_name", entry.get("topic", "Bài học")), size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ft.Text(entry.get("created_at", ""), size=10, color=ft.Colors.GREY_500),
                        ft.Text(f"{'⭐' * entry.get('rating_stars', 5)}", size=10, color=ft.Colors.AMBER_600)
                    ], spacing=2),
                    bgcolor=ft.Colors.WHITE,
                    padding=8,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.INDIGO_100),
                    on_click=make_click_handler(),
                    ink=True
                )
                list_items.append(card)

            # Mặc định hiển thị bài đầu tiên
            display_entry_detail(entries[0])
        else:
            list_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=ft.Colors.GREY_400, size=32),
                        ft.Text("Sổ tay đang trống!", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                        ft.Text("Hãy bấm 'Lưu vào Sổ tay Tự học' sau khi học để lưu trữ bài học nhé!", size=10, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    padding=16
                )
            )
            detail_container.content = ft.Container(
                content=ft.Text("Chọn hoặc lưu một bài học để xem chi tiết ở đây.", color=ft.Colors.GREY_500),
                alignment=ft.Alignment.CENTER
            )

        left_column = ft.Container(
            content=ft.Column(list_items, spacing=6, scroll=ft.ScrollMode.AUTO),
            width=230,
            border=ft.Border(right=ft.BorderSide(1, ft.Colors.GREY_200)),
            padding=ft.Padding(0, 0, 8, 0)
        )

        content_box = ft.Container(
            content=ft.Row([left_column, detail_container], spacing=12),
            width=760,
            height=460,
            padding=10
        )

        def close_dialog(_):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=ft.Colors.INDIGO_700, size=24),
                ft.Text("Sổ Tay Tự Học Của Em 📓", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=content_box,
            actions=[
                ft.FilledButton(
                    "Đóng Sổ Tay",
                    icon=ft.Icons.CLOSE_ROUNDED,
                    on_click=close_dialog,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def build(self) -> ft.Control:
        """Trả về toàn bộ giao diện của Chức năng 5."""
        return ft.Container(
            content=ft.Column(
                [
                    self.standalone_header,
                    self.mission_card,
                    ft.Container(height=4),
                    self.concept_card,
                    ft.Container(height=4),
                    self.mindmap_container,
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
