# -*- coding: utf-8 -*-
"""
Module: parent_view.py
Chức năng: Giao diện Cổng Giám Sát & Theo Dõi Tiến Độ Học Tập Dành Cho Phụ Huynh
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Các tính năng nổi bật:
- Thẻ thông tin Phụ huynh & Danh sách các con em đang theo dõi (Multi-child support).
- Nút "➕ Thêm người theo dõi": Yêu cầu tài khoản & mật khẩu của học sinh thứ 2, 3... để bảo mật.
- Nút / Thẻ "🔄 Đổi người theo dõi": Chuyển đổi linh hoạt giữa các con em chỉ với 1-chạm.
- Thống kê toàn diện về con em đang chọn:
  + Chuỗi ngày học liên tục (Streak) & Lịch 7 ngày.
  + Tiến độ 3 mạch môn học KHTN 7 (Vật lý ⚡, Hóa học 🔬, Sinh học 🌿).
  + Điểm Rubric Lập luận trung bình (0-6đ) & Huy hiệu đã đạt.
  + Nhật ký Sổ tay Tự học của con (xem những bài con đã giải và tự đúc kết).
  + Khung "Lời khuyên Sư phạm AI dành cho Ba Mẹ" giúp đồng hành hiệu quả tại nhà.
- Nút "Chuyển sang Chế độ Học sinh" & "Đăng xuất".
"""

from typing import Callable, Optional, List, Dict, Any
import flet as ft

from app_tich_hop_socrates.auth_service import AuthService, UserAccount
from app_tich_hop_socrates.parent_service import ParentService, ParentAccount
from app_tich_hop_socrates.dashboard_view import safe_open_dialog, safe_close_dialog


class ParentPortalView:
    """
    Giao diện làm việc chính của Phụ huynh: Theo dõi tiến độ con em.
    """
    def __init__(
        self,
        page: ft.Page,
        parent: ParentAccount,
        on_switch_to_student: Callable[[UserAccount], None],
        on_logout: Callable[[], None]
    ):
        self.page = page
        self.parent = parent
        self.on_switch_to_student = on_switch_to_student
        self.on_logout = on_logout

        # Lấy học sinh hiện đang active
        self.active_child: Optional[UserAccount] = ParentService.get_active_child(self.parent)

        # Vùng chứa nội dung động chi tiết của con
        self.child_detail_container = ft.Container()
        self.child_selector_row = ft.Row(spacing=10, wrap=True)

    def build(self) -> ft.Control:
        """Xây dựng toàn bộ giao diện Cổng Phụ Huynh."""
        # 1. Thanh tiêu đề Phụ Huynh (Parent Header)
        header = self._build_header()

        # 2. Thanh Quản lý Con em (Child Selector Bar)
        selector_bar = self._build_child_selector_bar()

        # 3. Nội dung tiến độ chi tiết của con đang chọn
        self._refresh_child_detail()

        portal_layout = ft.Column([
            header,
            ft.Container(height=8),
            selector_bar,
            ft.Container(height=12),
            self.child_detail_container,
            ft.Container(height=16),
            self._build_footer()
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

        return ft.Container(
            content=portal_layout,
            expand=True,
            bgcolor="#F8FAFC",
            padding=ft.Padding(16, 12, 16, 16)
        )

    def _build_header(self) -> ft.Container:
        """Xây dựng thanh tiêu đề Cổng Phụ Huynh."""
        brand = ft.Row([
            ft.Container(
                content=ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.WHITE, size=24),
                bgcolor=ft.Colors.AMBER_500,
                width=42,
                height=42,
                border_radius=21,
                alignment=ft.Alignment.CENTER,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.35, ft.Colors.AMBER_500), offset=ft.Offset(0, 2))
            ),
            ft.Column([
                ft.Row([
                    ft.Text("SOCRATES NHÍ 💡", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.FAMILY_RESTROOM_ROUNDED, color=ft.Colors.TEAL_800, size=14),
                            ft.Text("CỔNG PHỤ HUYNH ĐỒNG HÀNH 👨‍👩‍👧‍👦", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_900)
                        ], spacing=4),
                        bgcolor=ft.Colors.TEAL_50,
                        padding=ft.Padding(8, 4, 10, 4),
                        border_radius=10,
                        border=ft.Border.all(1, ft.Colors.TEAL_300)
                    )
                ], spacing=8),
                ft.Text("Bảng giám sát tiến độ & rèn luyện tư duy khoa học KHTN 7 cho con em", size=11, color=ft.Colors.GREY_600)
            ], spacing=2)
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # Thông tin phụ huynh & các nút hành động
        parent_chip = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(self.parent.avatar, size=16),
                    width=30,
                    height=30,
                    border_radius=15,
                    bgcolor=ft.Colors.TEAL_100,
                    alignment=ft.Alignment.CENTER
                ),
                ft.Column([
                    ft.Text(self.parent.display_name, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_900),
                    ft.Text(f"@{self.parent.username} • {self.parent.phone_number or 'Phụ huynh'}", size=10, color=ft.Colors.GREY_600)
                ], spacing=0)
            ], spacing=6),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(8, 4, 12, 4),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.TEAL_200)
        )

        btn_switch_student = ft.FilledButton(
            "Vào Học Cùng Con 🎒",
            icon=ft.Icons.SCHOOL_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE),
            on_click=lambda _: self._on_click_study_with_child()
        )

        btn_logout = ft.OutlinedButton(
            "Đăng xuất",
            icon=ft.Icons.LOGOUT_ROUNDED,
            style=ft.ButtonStyle(color=ft.Colors.RED_700),
            on_click=lambda _: self._confirm_parent_logout()
        )

        return ft.Container(
            content=ft.Row([
                brand,
                ft.Row([parent_chip, btn_switch_student, btn_logout], spacing=8, wrap=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(16, 12, 16, 12),
            border_radius=16,
            border=ft.Border.all(1, ft.Colors.INDIGO_50),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 3))
        )

    def _confirm_parent_logout(self):
        """Hộp thoại xác nhận đăng xuất cổng phụ huynh."""
        def do_logout(_):
            safe_close_dialog(self.page, dialog)
            self.on_logout()

        def do_cancel(_):
            safe_close_dialog(self.page, dialog)

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.LOGOUT_ROUNDED, color=ft.Colors.RED_700, size=24),
                ft.Text("Xác nhận đăng xuất 🚪", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_900)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Quý phụ huynh {self.parent.display_name} có chắc chắn muốn đăng xuất không? 👋", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                    ft.Text("• Phiên làm việc sẽ kết thúc và ứng dụng sẽ quay về màn hình Đăng nhập.", size=12, color=ft.Colors.GREY_700),
                ], spacing=6),
                width=420,
                padding=8
            ),
            actions=[
                ft.OutlinedButton("Ở lại theo dõi", on_click=do_cancel, style=ft.ButtonStyle(color=ft.Colors.INDIGO_900)),
                ft.FilledButton(
                    "Đăng xuất ngay 🚪",
                    icon=ft.Icons.LOGOUT_ROUNDED,
                    on_click=do_logout,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        safe_open_dialog(self.page, dialog)

    def _build_child_selector_bar(self) -> ft.Container:
        """Xây dựng thanh chọn/đổi con em và nút thêm người theo dõi."""
        self._refresh_child_chips()

        btn_add_child = ft.FilledButton(
            "➕ Thêm Người Theo Dõi (Thêm Con)",
            icon=ft.Icons.PERSON_ADD_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            tooltip="Liên kết thêm con em học sinh khác bằng tài khoản & mật khẩu của con",
            on_click=lambda _: self._open_add_child_dialog()
        )

        top_row = ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.PEOPLE_ALT_ROUNDED, color=ft.Colors.INDIGO_700, size=20),
                ft.Text("Danh Sách Con Em Đang Theo Dõi:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
            ], spacing=6),
            btn_add_child
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([
                top_row,
                ft.Container(height=4),
                self.child_selector_row
            ], spacing=4),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(16, 12, 16, 12),
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

    def _refresh_child_chips(self):
        """Cập nhật các thẻ con em trong thanh công cụ."""
        self.child_selector_row.controls.clear()
        children = ParentService.get_parent_children(self.parent)

        if not children:
            self.child_selector_row.controls.append(
                ft.Text("Chưa có con em nào được liên kết. Vui lòng bấm 'Thêm Người Theo Dõi' bên phải.", size=12, italic=True, color=ft.Colors.AMBER_800)
            )
            return

        for child in children:
            is_active = (self.active_child and self.active_child.username == child.username)
            card = self._create_child_chip(child, is_active)
            self.child_selector_row.controls.append(card)

    def _create_child_chip(self, child: UserAccount, is_active: bool) -> ft.Container:
        """Tạo một thẻ con em bấm được để đổi người theo dõi."""
        bg_color = ft.Colors.INDIGO_600 if is_active else ft.Colors.GREY_50
        border_color = ft.Colors.INDIGO_700 if is_active else ft.Colors.GREY_300
        text_color = ft.Colors.WHITE if is_active else ft.Colors.GREY_800
        sub_color = ft.Colors.INDIGO_100 if is_active else ft.Colors.GREY_600

        def on_click(_):
            self._switch_to_child(child.username)

        badge_content = [
            ft.Text(child.avatar, size=16),
            ft.Column([
                ft.Row([
                    ft.Text(child.display_name, size=12, weight=ft.FontWeight.BOLD, color=text_color),
                    ft.Container(
                        content=ft.Text("Đang xem" if is_active else "Bấm để đổi", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_active else ft.Colors.GREY_700),
                        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.WHITE) if is_active else ft.Colors.GREY_200,
                        padding=ft.Padding(5, 1, 5, 1),
                        border_radius=4
                    )
                ], spacing=6),
                ft.Text(f"{child.grade_class} • @{child.username}", size=10, color=sub_color)
            ], spacing=1)
        ]

        return ft.Container(
            content=ft.Row(badge_content, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=bg_color,
            padding=ft.Padding(10, 6, 12, 6),
            border_radius=12,
            border=ft.Border.all(1.5, border_color),
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.12, ft.Colors.INDIGO_700), offset=ft.Offset(0, 2)) if is_active else None,
            on_click=on_click,
            ink=True,
            tooltip=f"Bấm để xem tiến độ của em {child.display_name}"
        )

    def _switch_to_child(self, child_username: str):
        """Xử lý đổi người theo dõi sang con em khác."""
        ok, msg, stu = ParentService.switch_active_child(self.parent.username, child_username)
        if ok and stu:
            self.active_child = stu
            self._refresh_child_chips()
            self._refresh_child_detail()
            self.page.update()

            snack = ft.SnackBar(
                content=ft.Row([
                    ft.Text(stu.avatar, size=18),
                    ft.Text(f"Đã chuyển sang theo dõi con em: {stu.display_name} 🌟", color=ft.Colors.WHITE, size=12)
                ], spacing=6),
                bgcolor=ft.Colors.INDIGO_900
            )
            if hasattr(self.page, "open"):
                self.page.open(snack)
            else:
                self.page.snack_bar = snack
                snack.open = True
            self.page.update()

    def _refresh_child_detail(self):
        """Vẽ lại toàn bộ nội dung phân tích tiến độ của con em đang active."""
        if not self.active_child:
            self.child_detail_container.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PERSON_SEARCH_ROUNDED, size=48, color=ft.Colors.GREY_400),
                    ft.Text("Chưa chọn học sinh nào để theo dõi.", size=14, color=ft.Colors.GREY_600),
                    ft.FilledButton("Thêm con em ngay", icon=ft.Icons.PERSON_ADD_ROUNDED, on_click=lambda _: self._open_add_child_dialog())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=40,
                alignment=ft.Alignment.CENTER
            )
            return

        child = self.active_child
        stats = ParentService.get_child_detailed_stats(child.username, self.parent)

        # -------------------------------------------------------------
        # 1. BANNER ĐÁNH GIÁ CHỈ TIÊU & MỤC TIÊU HỌC TẬP (TARGET BANNER)
        # -------------------------------------------------------------
        target_banner = self._build_target_evaluation_banner(stats)

        # -------------------------------------------------------------
        # 2. HÀNG 4 THẺ SỐ LIỆU VÀNG: GIỜ HỌC, CHUỖI, BÀI ĐÃ GIẢI, RUBRIC
        # -------------------------------------------------------------
        kpi_row = self._build_kpi_cards(stats)

        # -------------------------------------------------------------
        # 3. HÀNG 2: TIẾN ĐỘ 3 PHÂN MÔN & THỜI GIAN HỌC 7 NGÀY TRONG TUẦN
        # -------------------------------------------------------------
        strand_and_calendar = ft.ResponsiveRow([
            ft.Container(
                content=self._build_strand_progress_panel(stats),
                col={"sm": 12, "md": 12, "lg": 6, "xl": 6}
            ),
            ft.Container(
                content=self._build_weekly_hours_calendar_panel(stats),
                col={"sm": 12, "md": 12, "lg": 6, "xl": 6}
            )
        ], spacing=16)

        # -------------------------------------------------------------
        # 4. HÀNG 3: BẢNG ĐIỂM KIỂM TRA NĂNG LỰC CON EM (TRẮC NGHIỆM & TỰ LUẬN)
        # -------------------------------------------------------------
        quiz_mastery_panel = self._build_quiz_mastery_panel(child, stats)

        # -------------------------------------------------------------
        # 5. HÀNG 4: SỔ TAY BÀI HỌC ĐÃ GIẢI & PHÂN TÍCH ĐỘC LẬP / SƯ PHẠM
        # -------------------------------------------------------------
        notebook_and_coaching = ft.ResponsiveRow([
            ft.Container(
                content=self._build_notebook_history_panel(child, stats),
                col={"sm": 12, "md": 12, "lg": 7, "xl": 7}
            ),
            ft.Container(
                content=self._build_parent_coaching_panel(child, stats),
                col={"sm": 12, "md": 12, "lg": 5, "xl": 5}
            )
        ], spacing=16)

        self.child_detail_container.content = ft.Column([
            target_banner,
            ft.Container(height=4),
            kpi_row,
            ft.Container(height=4),
            strand_and_calendar,
            ft.Container(height=4),
            quiz_mastery_panel,
            ft.Container(height=4),
            notebook_and_coaching
        ], spacing=10)

    def _build_target_evaluation_banner(self, stats: dict) -> ft.Container:
        """Thẻ Banner Đánh giá Trạng thái Chỉ tiêu học tập hôm nay & tuần này."""
        is_met = stats["is_daily_target_met"]
        today_mins = stats["today_minutes"]

        if is_met:
            bg_colors = ["#ECFDF5", "#D1FAE5"]
            border_color = ft.Colors.GREEN_400
            title_color = ft.Colors.GREEN_900
            badge_icon = ft.Icons.WORKSPACE_PREMIUM_ROUNDED
            icon_color = ft.Colors.GREEN_700
        elif today_mins > 0:
            bg_colors = ["#FFFBEB", "#FEF3C7"]
            border_color = ft.Colors.AMBER_400
            title_color = ft.Colors.AMBER_900
            badge_icon = ft.Icons.HOURGLASS_TOP_ROUNDED
            icon_color = ft.Colors.AMBER_700
        else:
            bg_colors = ["#F8FAFC", "#F1F5F9"]
            border_color = ft.Colors.BLUE_GREY_300
            title_color = ft.Colors.BLUE_GREY_900
            badge_icon = ft.Icons.NOTIFICATIONS_ACTIVE_ROUNDED
            icon_color = ft.Colors.BLUE_GREY_700

        # Lời khen đã gửi (nếu có)
        encouragement_widget = ft.Container(visible=False)
        if stats.get("encouragement"):
            enc = stats["encouragement"]
            encouragement_widget = ft.Container(
                content=ft.Row([
                    ft.Text(enc.get("badge", "⭐"), size=20),
                    ft.Column([
                        ft.Text(f"💌 Lời nhắn từ Ba Mẹ: \"{enc.get('text', '')}\"", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_900),
                        ft.Text(f"Gửi lúc: {enc.get('date', '')} • Người gửi: {enc.get('sender', 'Phụ huynh')}", size=9, color=ft.Colors.TEAL_700)
                    ], spacing=1, expand=True)
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.WHITE,
                padding=ft.Padding(10, 6, 12, 6),
                border_radius=10,
                border=ft.Border.all(1, ft.Colors.TEAL_300),
                visible=True
            )

        btn_settings = ft.FilledButton(
            "Cài Đặt Chỉ Tiêu ⚙️",
            icon=ft.Icons.TUNE_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE),
            tooltip="Tùy chỉnh mục tiêu số phút học mỗi ngày và số bài mỗi tuần cho con",
            on_click=lambda _: self._open_target_settings_dialog()
        )

        btn_cheer = ft.FilledButton(
            "Gửi Lời Khen & Huy Hiệu 💌",
            icon=ft.Icons.VOLUNTEER_ACTIVISM_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.TEAL_800, color=ft.Colors.WHITE),
            tooltip="Gửi lời động viên ấm áp và tặng huy hiệu danh dự cho con em",
            on_click=lambda _: self._open_send_encouragement_dialog()
        )

        header_row = ft.Row([
            ft.Row([
                ft.Container(
                    content=ft.Icon(badge_icon, color=ft.Colors.WHITE, size=24),
                    bgcolor=icon_color,
                    width=44,
                    height=44,
                    border_radius=22,
                    alignment=ft.Alignment.CENTER,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.3, icon_color), offset=ft.Offset(0, 2))
                ),
                ft.Column([
                    ft.Row([
                        ft.Text(f"{stats['daily_badge']} {stats['daily_status']}", size=15, weight=ft.FontWeight.BOLD, color=title_color),
                        ft.Container(
                            content=ft.Text(f"Hôm nay: {stats['today_hours_str']}", size=11, weight=ft.FontWeight.BOLD, color=title_color),
                            bgcolor=ft.Colors.with_opacity(0.2, border_color),
                            padding=ft.Padding(8, 2, 8, 2),
                            border_radius=6
                        )
                    ], spacing=8),
                    ft.Text(stats["daily_msg"], size=12, color=ft.Colors.GREY_800, weight=ft.FontWeight.W_500)
                ], spacing=2)
            ], spacing=12),
            ft.Row([btn_settings, btn_cheer], spacing=8)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        targets_row = ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.FLAG_ROUNDED, size=14, color=ft.Colors.INDIGO_700),
                    ft.Text(f"Chỉ tiêu ngày: {stats['daily_target_minutes']} phút (Đạt {stats['daily_target_percent']}%)", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_900)
                ], spacing=4),
                bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
                padding=ft.Padding(8, 4, 10, 4),
                border_radius=8
            ),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.DATE_RANGE_ROUNDED, size=14, color=ft.Colors.PURPLE_700),
                    ft.Text(f"Chỉ tiêu tuần: {stats['days_studied_count']}/{stats['weekly_days_target']} ngày học ({stats['weekly_percent']}%)", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.PURPLE_900)
                ], spacing=4),
                bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
                padding=ft.Padding(8, 4, 10, 4),
                border_radius=8
            ),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.TASK_ALT_ROUNDED, size=14, color=ft.Colors.GREEN_700),
                    ft.Text(f"Mục tiêu bài giải: {stats['total_solved']}/{stats['weekly_lesson_target']} bài", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.GREEN_900)
                ], spacing=4),
                bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
                padding=ft.Padding(8, 4, 10, 4),
                border_radius=8
            )
        ], spacing=8, wrap=True)

        return ft.Container(
            content=ft.Column([
                header_row,
                targets_row,
                encouragement_widget
            ], spacing=10),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=bg_colors
            ),
            padding=ft.Padding(16, 14, 16, 14),
            border_radius=16,
            border=ft.Border.all(1.5, border_color),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 3))
        )

    def _build_kpi_cards(self, stats: dict) -> ft.Container:
        """Tạo hàng 4 thẻ KPI phản ánh đầy đủ giờ học, chuỗi ngày, số bài giải, rubric."""
        def make_kpi(icon, val_text, label_text, sub_text, bg_color, border_color, icon_color, extra_ctrl=None):
            content_col = [
                ft.Text(val_text, size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                ft.Text(label_text, size=11, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                ft.Text(sub_text, size=10, color=ft.Colors.GREY_500)
            ]
            if extra_ctrl:
                content_col.append(extra_ctrl)

            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=icon_color, size=24),
                        width=46,
                        height=46,
                        border_radius=23,
                        bgcolor=ft.Colors.with_opacity(0.18, icon_color),
                        alignment=ft.Alignment.CENTER
                    ),
                    ft.Column(content_col, spacing=1)
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=bg_color,
                padding=ft.Padding(14, 12, 14, 12),
                border_radius=14,
                border=ft.Border.all(1, border_color)
            )

        # 1. Thời gian học trong 1 ngày (mấy giờ)
        p_val = min(stats["daily_target_percent"] / 100.0, 1.0)
        daily_bar = ft.ProgressBar(value=p_val, color=ft.Colors.BLUE_700, bgcolor=ft.Colors.BLUE_100, height=5)
        card_1 = make_kpi(
            ft.Icons.ACCESS_TIME_ROUNDED,
            stats["today_hours_str"],
            "Thời Gian Học Hôm Nay",
            f"~{stats['today_hours']} giờ • Chỉ tiêu: {stats['daily_target_minutes']}p",
            ft.Colors.BLUE_50,
            ft.Colors.BLUE_200,
            ft.Colors.BLUE_700,
            extra_ctrl=daily_bar
        )

        # 2. Chuỗi học liên tiếp là bao nhiêu (Streak)
        card_2 = make_kpi(
            ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
            f"{stats['streak_count']} Ngày Liên Tiếp",
            "Chuỗi Ngày Tự Học",
            f"Kỷ lục: {stats['max_streak']} ngày • Chuyên cần 100%",
            ft.Colors.AMBER_50,
            ft.Colors.AMBER_200,
            ft.Colors.AMBER_800
        )

        # 3. Số bài đã giải & Thống kê môn học
        card_3 = make_kpi(
            ft.Icons.FACT_CHECK_ROUNDED,
            f"{stats['total_solved']} Bài Đã Giải",
            "Số Bài Đã Giải Quyết",
            f"Lý: {stats['physics_solved']} • Hóa: {stats['chemistry_solved']} • Sinh: {stats['biology_solved']}",
            ft.Colors.GREEN_50,
            ft.Colors.GREEN_200,
            ft.Colors.GREEN_700
        )

        # 4. Điểm Rubric lập luận & năng lực
        card_4 = make_kpi(
            ft.Icons.ASSESSMENT_ROUNDED,
            f"{stats['avg_rubric_score']} / 6.0 Điểm",
            "Điểm Lập Luận Rubric",
            "Năng lực: Tự tin suy luận bản chất",
            ft.Colors.PURPLE_50,
            ft.Colors.PURPLE_200,
            ft.Colors.PURPLE_700
        )

        return ft.ResponsiveRow([
            ft.Container(content=card_1, col={"sm": 6, "md": 6, "lg": 3, "xl": 3}),
            ft.Container(content=card_2, col={"sm": 6, "md": 6, "lg": 3, "xl": 3}),
            ft.Container(content=card_3, col={"sm": 6, "md": 6, "lg": 3, "xl": 3}),
            ft.Container(content=card_4, col={"sm": 6, "md": 6, "lg": 3, "xl": 3}),
        ], spacing=12)

    def _build_strand_progress_panel(self, stats: dict) -> ft.Container:
        """Bảng tiến độ học tập 3 phân môn KHTN 7."""
        def make_strand_bar(icon, name, completed, total, color, bg_light):
            pct = min(completed / total, 1.0)
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Row([
                            ft.Text(icon, size=16),
                            ft.Text(name, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900)
                        ], spacing=6),
                        ft.Text(f"{completed}/{total} Bài ({int(pct * 100)}%)", size=11, weight=ft.FontWeight.BOLD, color=color)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.ProgressBar(value=pct, color=color, bgcolor=bg_light, height=8)
                ], spacing=6),
                padding=ft.Padding(10, 8, 10, 8),
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                border=ft.Border.all(1, ft.Colors.GREY_200)
            )

        bar_phys = make_strand_bar("💡", "Phân môn Vật lý (Tốc độ, Chuyển động, Sóng âm)", stats["physics_solved"], 4, ft.Colors.AMBER_700, ft.Colors.AMBER_100)
        bar_chem = make_strand_bar("🔬", "Phân môn Hóa học (Nguyên tử, Phân tử, Hóa trị)", stats["chemistry_solved"], 4, ft.Colors.PURPLE_700, ft.Colors.PURPLE_100)
        bar_bio = make_strand_bar("🌿", "Phân môn Sinh học (Quang hợp, Hô hấp tế bào)", stats["biology_solved"], 4, ft.Colors.GREEN_700, ft.Colors.GREEN_100)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.AUTO_GRAPH_ROUNDED, color=ft.Colors.INDIGO_700, size=20),
                    ft.Text("Tiến Độ Học Tập 3 Mạch Khoa Học Tự Nhiên 7", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                ft.Text("Phân bố số bài con đã giải theo Chương trình Giáo dục Phổ thông 2018:", size=11, color=ft.Colors.GREY_600),
                bar_phys,
                bar_chem,
                bar_bio,
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=ft.Colors.GREEN_700, size=15),
                        ft.Text(f"Tổng cộng đã giải: {stats['total_solved']} bài • Đạt {int((stats['total_solved']/12)*100)}% toàn bộ chương trình KHTN 7 chuẩn SGK.", size=10, color=ft.Colors.GREEN_900)
                    ], spacing=6),
                    bgcolor=ft.Colors.GREEN_50,
                    padding=ft.Padding(8, 6, 8, 6),
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.GREEN_200)
                )
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            padding=16,
            border_radius=16,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

    def _build_weekly_hours_calendar_panel(self, stats: dict) -> ft.Container:
        """Bảng lịch tuần & thời gian học từng ngày (trong 1 ngày học được mấy giờ/phút)."""
        days_row = ft.Row(spacing=6, wrap=True)
        total_weekly_mins = sum(d["minutes"] for d in stats.get("detailed_week", []))

        for d in stats.get("detailed_week", []):
            is_studied = d.get("studied", False)
            is_today = d.get("is_today", False)
            mins = d.get("minutes", 0)

            if is_studied:
                box_bg = ft.Colors.AMBER_500
                text_col = ft.Colors.WHITE
                status_icon = ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED, size=14, color=ft.Colors.WHITE)
                time_badge = ft.Text(f"{mins}p", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            else:
                box_bg = ft.Colors.GREY_100
                text_col = ft.Colors.GREY_600
                status_icon = ft.Text("·", size=14, color=ft.Colors.GREY_400)
                time_badge = ft.Text("0p", size=9, color=ft.Colors.GREY_400)

            border = ft.Border.all(2, ft.Colors.INDIGO_600) if is_today else ft.Border.all(1, ft.Colors.GREY_300)

            day_card = ft.Container(
                content=ft.Column([
                    ft.Text(d["label"], size=10, weight=ft.FontWeight.BOLD, color=text_col),
                    status_icon,
                    time_badge,
                    ft.Text(d["date"][-2:], size=8, color=text_col)
                ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=box_bg,
                width=42,
                height=72,
                border_radius=8,
                border=border,
                alignment=ft.Alignment.CENTER,
                tooltip=f"{d.get('full_name', '')}: {d.get('hours_str', '0p')} học tập"
            )
            days_row.controls.append(day_card)

        avg_daily = round(total_weekly_mins / max(stats.get("days_studied_count", 1), 1))

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, color=ft.Colors.AMBER_800, size=20),
                    ft.Text("Thời Gian Học Từng Ngày Trong Tuần (Lịch 7 Ngày)", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                ft.Text("Theo dõi số giờ/phút con học tập mỗi ngày để đảm bảo thói quen tự học:", size=11, color=ft.Colors.GREY_600),
                ft.Container(content=days_row, padding=ft.Padding(0, 4, 0, 4)),
                ft.Row([
                    ft.Container(width=10, height=10, bgcolor=ft.Colors.AMBER_500, border_radius=3),
                    ft.Text("Đã học", size=10, color=ft.Colors.GREY_700),
                    ft.Container(width=8),
                    ft.Container(width=10, height=10, bgcolor=ft.Colors.GREY_200, border_radius=3),
                    ft.Text("Nghỉ", size=10, color=ft.Colors.GREY_700),
                    ft.Container(width=8),
                    ft.Container(width=10, height=10, border=ft.Border.all(1.5, ft.Colors.INDIGO_600), border_radius=3),
                    ft.Text("Hôm nay", size=10, color=ft.Colors.GREY_700)
                ], spacing=4),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INSIGHTS_ROUNDED, size=14, color=ft.Colors.INDIGO_700),
                        ft.Text(f"Tổng tuần này: {total_weekly_mins} phút (~{round(total_weekly_mins/60, 1)} giờ) • Trung bình mỗi ngày học: ~{avg_daily} phút/ngày.", size=10, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_900)
                    ], spacing=6),
                    bgcolor=ft.Colors.INDIGO_50,
                    padding=ft.Padding(8, 6, 8, 6),
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.INDIGO_200)
                )
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=16,
            border_radius=16,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

    def _build_quiz_mastery_panel(self, child: UserAccount, stats: dict) -> ft.Container:
        """Bảng Giám sát Điểm Kiểm tra Củng cố & Năng lực Lập luận của con (Trắc nghiệm + Tự luận)."""
        quiz_stats = stats.get("quiz_stats", {})
        total_q = quiz_stats.get("total_quizzes", 0)
        avg_s = quiz_stats.get("average_score", 0.0)
        mastery_lvl = quiz_stats.get("mastery_level", "Chưa làm bài kiểm tra nào")
        recent_records = quiz_stats.get("recent_records", [])

        # Thẻ tóm tắt năng lực
        card_score = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("⭐", size=18),
                    ft.Text(f"{avg_s:.1f} / 10đ" if total_q > 0 else "Chưa có điểm", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900)
                ], spacing=6),
                ft.Text("Điểm Kiểm Tra Trung Bình", size=11, color=ft.Colors.PURPLE_800),
                ft.Container(
                    content=ft.Text(mastery_lvl, size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900),
                    bgcolor=ft.Colors.PURPLE_100,
                    padding=ft.Padding(6, 2, 6, 2),
                    border_radius=6
                )
            ], spacing=2),
            bgcolor=ft.Colors.PURPLE_50,
            padding=12,
            border_radius=12,
            border=ft.Border.all(1.5, ft.Colors.PURPLE_300),
            expand=True
        )

        card_total = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📝", size=18),
                    ft.Text(f"{total_q} Bài", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                ft.Text("Số Bài Đã Kiểm Tra Củng Cố", size=11, color=ft.Colors.INDIGO_800),
                ft.Text(f"Đạt Giỏi/Xuất sắc: {quiz_stats.get('excellent_count', 0)} bài", size=10, color=ft.Colors.GREEN_800, weight=ft.FontWeight.W_500)
            ], spacing=2),
            bgcolor=ft.Colors.INDIGO_50,
            padding=12,
            border_radius=12,
            border=ft.Border.all(1.5, ft.Colors.INDIGO_300),
            expand=True
        )

        # Danh sách các bài kiểm tra gần nhất
        if not recent_records:
            history_content = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE_ROUNDED, color=ft.Colors.AMBER_800, size=20),
                    ft.Column([
                        ft.Text("Con chưa làm bài kiểm tra củng cố nào gần đây.", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900),
                        ft.Text("Sau mỗi buổi học ở Trạm 5 hoặc khi bắt đầu ngày mới, con sẽ được làm bài kiểm tra 3 phút gồm 3 câu trắc nghiệm + 1 câu tự luận để đánh giá năng lực.", size=10, color=ft.Colors.AMBER_800)
                    ], spacing=2, expand=True)
                ], spacing=10),
                bgcolor=ft.Colors.AMBER_50,
                padding=12,
                border_radius=10,
                border=ft.Border.all(1, ft.Colors.AMBER_300)
            )
        else:
            quiz_item_controls = []
            for r in recent_records[:3]:
                d_date = r.get("created_at", "").split("T")[0]
                q_score = r.get("score", 0.0)
                score_color = ft.Colors.GREEN_700 if q_score >= 8.0 else (ft.Colors.AMBER_800 if q_score >= 6.0 else ft.Colors.RED_700)
                q_type_str = "Kiểm tra sau bài học" if r.get("quiz_type") == "post_lesson" else "Ôn tập ngày mới 🔁"

                item_card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(f"{q_score:.1f}đ", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    bgcolor=score_color,
                                    padding=ft.Padding(8, 3, 8, 3),
                                    border_radius=8
                                ),
                                ft.Column([
                                    ft.Text(r.get("topic", "KHTN 7"), size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                                    ft.Text(f"{q_type_str} • {d_date} • {r.get('badge_earned', '')}", size=10, color=ft.Colors.GREY_600)
                                ], spacing=1)
                            ], spacing=8),
                            ft.Container(
                                content=ft.Text(f"Tự luận: {r.get('essay_score', 0):.1f}/4.0đ", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900),
                                bgcolor=ft.Colors.PURPLE_50,
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=6,
                                border=ft.Border.all(1, ft.Colors.PURPLE_200)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(
                            content=ft.Text(f"💬 Nhận xét của Gia sư AI: \"{r.get('essay_feedback', '')}\"", size=10.5, italic=True, color=ft.Colors.INDIGO_900),
                            bgcolor=ft.Colors.INDIGO_50,
                            padding=8,
                            border_radius=8
                        )
                    ], spacing=6),
                    bgcolor=ft.Colors.WHITE,
                    padding=10,
                    border_radius=10,
                    border=ft.Border.all(1, ft.Colors.GREY_200)
                )
                quiz_item_controls.append(item_card)

            history_content = ft.Column(quiz_item_controls, spacing=8)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.ASSIGNMENT_TURNED_IN_ROUNDED, color=ft.Colors.PURPLE_800, size=20),
                        ft.Text("KẾT QUẢ KIỂM TRA NĂNG LỰC CON EM (TRẮC NGHIỆM & TỰ LUẬN) 📝", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900)
                    ], spacing=6),
                    ft.Text("Đánh giá thực chất mức độ hiểu sâu kiến thức", size=10, color=ft.Colors.GREY_600, italic=True)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([card_score, card_total], spacing=12),
                ft.Text("Nhật ký các bài kiểm tra củng cố gần nhất của con:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                history_content
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            padding=16,
            border_radius=16,
            border=ft.Border.all(1, ft.Colors.INDIGO_50),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 3))
        )

    def _build_notebook_history_panel(self, child: UserAccount, stats: dict) -> ft.Container:
        """Bảng lịch sử Sổ tay Tự học (danh sách các bài con đã giải quyết)."""
        entries = stats.get("recent_entries", [])
        list_items = ft.Column(spacing=8)

        if not entries:
            list_items.controls.append(
                ft.Container(
                    content=ft.Text("Con chưa lưu bài học nào vào Sổ tay. Khi con hoàn thành chu trình 5 pha, bài học sẽ xuất hiện ở đây.", size=11, italic=True, color=ft.Colors.GREY_600),
                    padding=20
                )
            )
        else:
            for item in entries[:5]:
                topic = item.get("topic", "Bài học KHTN")
                date_str = item.get("created_at", "")
                takeaways = item.get("key_takeaways", [])
                score = item.get("rubric_score", 5)

                entry_card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=15, color=ft.Colors.GREEN_700),
                                ft.Text(topic, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                            ], spacing=6),
                            ft.Container(
                                content=ft.Text(f"Rubric: {score}/6đ", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900),
                                bgcolor=ft.Colors.PURPLE_100,
                                padding=ft.Padding(5, 2, 5, 2),
                                border_radius=4
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"Thời gian: {date_str}", size=10, color=ft.Colors.GREY_500),
                        ft.Column([
                            ft.Text(f"• {t}", size=10, color=ft.Colors.GREY_800) for t in takeaways[:2]
                        ], spacing=2)
                    ], spacing=4),
                    bgcolor=ft.Colors.GREY_50,
                    padding=10,
                    border_radius=10,
                    border=ft.Border.all(1, ft.Colors.GREY_200)
                )
                list_items.controls.append(entry_card)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=ft.Colors.CYAN_800, size=20),
                    ft.Text(f"Danh Sách Bài Học Con Đã Giải Quyết ({len(entries)} Bài)", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                ft.Text("Xem các kiến thức trọng tâm con đã tự suy luận và đúc kết thành công:", size=11, color=ft.Colors.GREY_600),
                list_items
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=16,
            border_radius=16,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

    def _build_parent_coaching_panel(self, child: UserAccount, stats: dict) -> ft.Container:
        """Khung Phân tích Tư duy Độc lập & Lời khuyên Sư phạm AI dành cho Phụ huynh."""
        tips = [
            f"🛡️ Chỉ số Tư duy Độc lập: {stats.get('self_reliance_percent', 88)}%. Con tự suy luận công thức và quy luật, tuyệt đối không bị ỷ lại AI đọc sẵn bài giải nhờ Khiên An Toàn 3 Tầng.",
            f"⏰ Khung giờ học ưa thích: {stats.get('preferred_study_time', '19:30 - 20:30')}. Thói quen học tập khoa học, tập trung tốt và không thức khuya.",
            f"🌟 Khen ngợi nỗ lực: Em {child.display_name} đã rèn luyện được tinh thần tự giác cao. Ba mẹ hãy dùng tính năng 'Gửi Lời Khen' để tặng huy hiệu động viên con nhé!"
        ]

        coaching_items = [
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.TEAL_800, size=15),
                        ft.Text(t.split(":")[0], size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_900)
                    ], spacing=6),
                    ft.Text(t.split(":", 1)[1].strip() if ":" in t else t, size=11, color=ft.Colors.GREY_800)
                ], spacing=3),
                bgcolor=ft.Colors.TEAL_50,
                padding=10,
                border_radius=8,
                border=ft.Border.all(1, ft.Colors.TEAL_200)
            ) for t in tips
        ]

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.TIPS_AND_UPDATES_ROUNDED, color=ft.Colors.TEAL_800, size=20),
                    ft.Text("Phân Tích Thói Quen & Lời Khuyên Cho Ba Mẹ 💡", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                ft.Text("Phương pháp đồng hành tích cực giúp con phát triển tư duy tự lập:", size=11, color=ft.Colors.GREY_600),
                ft.Column(coaching_items, spacing=8)
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=16,
            border_radius=16,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

    # -------------------------------------------------------------------------
    # HỘP THOẠI: CÀI ĐẶT CHỈ TIÊU HỌC TẬP (TARGET SETTINGS MODAL)
    # -------------------------------------------------------------------------
    def _open_target_settings_dialog(self):
        """Mở popup cho phép phụ huynh tùy chỉnh chỉ tiêu học tập của con."""
        current_daily = self.parent.daily_target_minutes or 45
        current_weekly = self.parent.weekly_target_lessons or 5

        dd_daily = ft.Dropdown(
            label="Chỉ tiêu thời gian học mỗi ngày",
            value=str(current_daily),
            options=[
                ft.dropdown.Option("30", "30 Phút / Ngày (Mức cơ bản)"),
                ft.dropdown.Option("45", "45 Phút / Ngày (Khuyến nghị chuẩn)"),
                ft.dropdown.Option("60", "60 Phút / Ngày (1 Giờ tập trung)"),
                ft.dropdown.Option("90", "90 Phút / Ngày (1.5 Giờ nâng cao)")
            ],
            dense=True
        )

        dd_weekly = ft.Dropdown(
            label="Chỉ tiêu số bài giải mỗi tuần",
            value=str(current_weekly),
            options=[
                ft.dropdown.Option("3", "3 Bài / Tuần (Thong thả ôn tập)"),
                ft.dropdown.Option("5", "5 Bài / Tuần (Khuyến nghị chuẩn SGK)"),
                ft.dropdown.Option("7", "7 Bài / Tuần (Mỗi ngày 1 bài)")
            ],
            dense=True
        )

        def close_dialog(_):
            safe_close_dialog(self.page, dialog)

        def save_targets(_):
            daily_val = int(dd_daily.value or 45)
            weekly_val = int(dd_weekly.value or 5)

            ParentService.update_parent_targets(self.parent.username, daily_val, weekly_val)
            self.parent.daily_target_minutes = daily_val
            self.parent.weekly_target_lessons = weekly_val

            safe_close_dialog(self.page, dialog)
            self._refresh_child_detail()
            self.page.update()

            snack = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.WHITE, size=18),
                    ft.Text(f"Đã lưu chỉ tiêu mới: {daily_val} phút/ngày và {weekly_val} bài/tuần! 🎯", color=ft.Colors.WHITE, size=12)
                ], spacing=6),
                bgcolor=ft.Colors.INDIGO_900
            )
            if hasattr(self.page, "open"):
                self.page.open(snack)
            else:
                self.page.snack_bar = snack
                snack.open = True
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.TUNE_ROUNDED, color=ft.Colors.INDIGO_700, size=24),
                ft.Text("Cài Đặt Chỉ Tiêu Học Tập Cho Con ⚙️", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Ba mẹ có thể điều chỉnh mục tiêu rèn luyện hàng ngày và hàng tuần để phù hợp với thời khóa biểu thực tế của con:",
                        size=12,
                        color=ft.Colors.GREY_700
                    ),
                    ft.Container(height=4),
                    dd_daily,
                    dd_weekly,
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE_ROUNDED, color=ft.Colors.AMBER_800, size=14),
                            ft.Text("Mức khuyến nghị sư phạm: 45 phút/ngày giúp rèn luyện sâu mà không gây mỏi mắt.", size=10, color=ft.Colors.AMBER_900)
                        ], spacing=4),
                        bgcolor=ft.Colors.AMBER_50,
                        padding=ft.Padding(8, 6, 8, 6),
                        border_radius=8
                    )
                ], spacing=10, tight=True),
                width=460
            ),
            actions=[
                ft.OutlinedButton("Hủy bỏ", on_click=close_dialog),
                ft.FilledButton(
                    "Lưu chỉ tiêu 💾",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE),
                    on_click=save_targets
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        safe_open_dialog(self.page, dialog)

    # -------------------------------------------------------------------------
    # HỘP THOẠI: GỬI LỜI KHEN & HUY HIỆU TỪ BA MẸ (ENCOURAGEMENT MODAL)
    # -------------------------------------------------------------------------
    def _open_send_encouragement_dialog(self):
        """Mở popup gửi lời khen và tặng huy hiệu từ ba mẹ."""
        txt_note = ft.TextField(
            label="Lời nhắn gửi yêu thương của Ba Mẹ",
            hint_text="Ví dụ: Ba mẹ rất tự hào vì con đã kiên trì 5 ngày liên tục! Cố lên con nhé!",
            prefix_icon=ft.Icons.EDIT_NOTE_ROUNDED,
            multiline=True,
            min_lines=2,
            max_lines=3,
            dense=True
        )

        dd_badge = ft.Dropdown(
            label="Chọn huy hiệu Ba Mẹ trao tặng",
            value="⭐",
            options=[
                ft.dropdown.Option("⭐", "⭐ Ngôi Sao Chăm Chỉ"),
                ft.dropdown.Option("🥇", "🥇 Con Ngoan Tự Lập"),
                ft.dropdown.Option("💡", "💡 Nhà Bác Học Nhí"),
                ft.dropdown.Option("🚀", "🚀 Tên Lửa Bứt Phá"),
                ft.dropdown.Option("🏆", "🏆 Quán Quân Kiên Trì")
            ],
            dense=True
        )

        def close_dialog(_):
            safe_close_dialog(self.page, dialog)

        def send_note(_):
            msg_text = txt_note.value or "Ba mẹ rất tự hào về nỗ lực tự học của con hôm nay!"
            badge_icon = dd_badge.value or "⭐"

            if self.active_child:
                ParentService.send_encouragement(
                    self.parent.username,
                    self.active_child.username,
                    msg_text,
                    badge_icon
                )
                safe_close_dialog(self.page, dialog)
                self._refresh_child_detail()
                self.page.update()

                snack = ft.SnackBar(
                    content=ft.Row([
                        ft.Text(badge_icon, size=18),
                        ft.Text(f"Đã gửi lời khen và tặng huy hiệu cho em {self.active_child.display_name}! 💌", color=ft.Colors.WHITE, size=12)
                    ], spacing=6),
                    bgcolor=ft.Colors.TEAL_900
                )
                if hasattr(self.page, "open"):
                    self.page.open(snack)
                else:
                    self.page.snack_bar = snack
                    snack.open = True
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.VOLUNTEER_ACTIVISM_ROUNDED, color=ft.Colors.TEAL_800, size=24),
                ft.Text("Gửi Lời Khen & Tặng Huy Hiệu Từ Ba Mẹ 💌", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"Gửi những lời động viên tích cực đến em {self.active_child.display_name if self.active_child else 'con'}. Lời nhắn này sẽ xuất hiện trên màn hình học tập của con:",
                        size=12,
                        color=ft.Colors.GREY_700
                    ),
                    ft.Container(height=4),
                    txt_note,
                    dd_badge
                ], spacing=10, tight=True),
                width=460
            ),
            actions=[
                ft.OutlinedButton("Hủy bỏ", on_click=close_dialog),
                ft.FilledButton(
                    "Gửi Lời Khen Cho Con 🚀",
                    icon=ft.Icons.SEND_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.TEAL_800, color=ft.Colors.WHITE),
                    on_click=send_note
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        safe_open_dialog(self.page, dialog)

    def _build_footer(self) -> ft.Container:
        """Chân trang Cổng Phụ huynh."""
        return ft.Container(
            content=ft.Row([
                ft.Text("© 2026 Socrates Nhí • Cổng Phụ Huynh Đồng Hành (Cuộc thi Sáng tạo trẻ Quốc gia AI)", size=11, color=ft.Colors.GREY_600),
                ft.Row([
                    ft.Icon(ft.Icons.SECURITY_ROUNDED, color=ft.Colors.GREEN_700, size=13),
                    ft.Text("Dữ liệu được lưu trữ an toàn & mã hóa bảo mật trên máy", size=11, color=ft.Colors.GREEN_800)
                ], spacing=4)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            padding=ft.Padding(12, 10, 12, 10),
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200))
        )

    # -------------------------------------------------------------------------
    # HỘP THOẠI: THÊM NGƯỜI THEO DÕI (ADD CHILD MODAL)
    # -------------------------------------------------------------------------
    def _open_add_child_dialog(self):
        """Mở popup yêu cầu nhập tài khoản và mật khẩu của con em để liên kết thêm."""
        txt_stu_user = ft.TextField(
            label="Tên tài khoản học sinh (viết liền)",
            hint_text="minhtriet, baoan, baonhat, huyhoang...",
            prefix_icon=ft.Icons.PERSON_ROUNDED,
            text_size=13,
            dense=True
        )

        txt_stu_pass = ft.TextField(
            label="Mật khẩu của học sinh",
            password=True,
            can_reveal_password=True,
            hint_text="Nhập mật khẩu con đang dùng (mẫu: 123)",
            prefix_icon=ft.Icons.LOCK_ROUNDED,
            text_size=13,
            dense=True
        )

        msg_error = ft.Text("", size=11, color=ft.Colors.RED_600)

        def close_dialog(_):
            safe_close_dialog(self.page, dialog)

        def on_confirm_add(_):
            uname = txt_stu_user.value or ""
            pwd = txt_stu_pass.value or ""

            ok, msg, new_child = ParentService.add_child_to_parent(
                self.parent.username,
                uname,
                pwd
            )

            if ok and new_child:
                safe_close_dialog(self.page, dialog)
                self.active_child = new_child
                self._refresh_child_chips()
                self._refresh_child_detail()
                self.page.update()

                snack = ft.SnackBar(
                    content=ft.Row([
                        ft.Text(new_child.avatar, size=18),
                        ft.Text(msg, color=ft.Colors.WHITE, size=12)
                    ], spacing=6),
                    bgcolor=ft.Colors.GREEN_800
                )
                if hasattr(self.page, "open"):
                    self.page.open(snack)
                else:
                    self.page.snack_bar = snack
                    snack.open = True
                self.page.update()
            else:
                msg_error.value = f"❌ {msg}"
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.PERSON_ADD_ALT_1_ROUNDED, color=ft.Colors.GREEN_700, size=24),
                ft.Text("Thêm Người Theo Dõi (Liên Kết Con Em) 🎒", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Để bảo mật thông tin học tập và quyền riêng tư của học sinh, Quý phụ huynh vui lòng nhập chính xác Tên tài khoản và Mật khẩu của con em cần theo dõi:",
                        size=12,
                        color=ft.Colors.GREY_700
                    ),
                    ft.Container(height=4),
                    txt_stu_user,
                    txt_stu_pass,
                    msg_error,
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=ft.Colors.BLUE_700, size=14),
                            ft.Text("Gợi ý tài khoản học sinh mẫu: minhtriet, baoan, baonhat (mật khẩu: 123)", size=10, color=ft.Colors.BLUE_900)
                        ], spacing=4),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=ft.Padding(8, 6, 8, 6),
                        border_radius=8
                    )
                ], spacing=10, tight=True),
                width=460
            ),
            actions=[
                ft.OutlinedButton("Hủy bỏ", on_click=close_dialog),
                ft.FilledButton(
                    "Xác nhận & Thêm ➕",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                    on_click=on_confirm_add
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        safe_open_dialog(self.page, dialog)

    def _on_click_study_with_child(self):
        """Chuyển sang phòng học cùng con em đang active."""
        if self.active_child:
            self.on_switch_to_student(self.active_child)
        else:
            first_child = ParentService.get_active_child(self.parent)
            if first_child:
                self.on_switch_to_student(first_child)
