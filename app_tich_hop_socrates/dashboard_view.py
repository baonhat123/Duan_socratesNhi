# -*- coding: utf-8 -*-
"""
Module: dashboard_view.py
Chức năng: Giao diện Bảng Theo Dõi Học Tập, Streak & Tiến Độ Khoa Học KHTN 7
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Các tính năng chính:
- Streak (Chuỗi ngày học liên tục) kèm lịch 7 ngày trong tuần.
- Tiến độ học tập theo 3 mạch môn học: Vật lý, Hóa học, Sinh học (trên 12 bài chuẩn SGK KHTN 7).
- Thống kê Sổ tay tự học & Nút mở Sổ tay nhanh.
- Hệ thống Huy hiệu danh dự đạt được.
- Quản lý tài khoản, Đổi tài khoản & Đăng xuất (Logout).
"""

from typing import Callable, Optional, Dict, Any, List
import flet as ft

from app_tich_hop_socrates.auth_service import AuthService, UserAccount


def safe_open_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Mở hộp thoại tương thích 100% với Flet 1.0.1 và các phiên bản khác."""
    if hasattr(page, "show_dialog") and callable(getattr(page, "show_dialog")):
        try:
            page.show_dialog(dialog)
            return
        except Exception:
            pass

    if hasattr(page, "overlay") and page.overlay is not None:
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        try:
            page.update(dialog)
        except Exception:
            try:
                page.update()
            except Exception:
                pass
        return

    try:
        if hasattr(page, "open") and callable(getattr(page, "open")):
            page.open(dialog)
            return
    except Exception:
        pass

    dialog.open = True
    try:
        page.update()
    except Exception:
        pass


def safe_close_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Đóng hộp thoại tương thích 100% với Flet 1.0.1."""
    if hasattr(page, "pop_dialog") and callable(getattr(page, "pop_dialog")):
        try:
            page.pop_dialog()
            return
        except Exception:
            pass

    dialog.open = False
    try:
        dialog.update()
    except Exception:
        pass
    try:
        page.update(dialog)
    except Exception:
        try:
            page.update()
        except Exception:
            pass


class StudentDashboardModal:
    """
    Hộp thoại Dashboard theo dõi Streak, Tiến độ và Tài khoản học sinh.
    """
    def __init__(
        self,
        page: ft.Page,
        current_user: UserAccount,
        on_open_notebook: Optional[Callable[[], None]] = None,
        on_switch_account: Optional[Callable[[], None]] = None,
        on_logout: Optional[Callable[[], None]] = None
    ):
        self.page = page
        self.user = current_user
        self.on_open_notebook = on_open_notebook
        self.on_switch_account = on_switch_account
        self.on_logout = on_logout
        self.dialog: Optional[ft.AlertDialog] = None

    def show(self):
        """Hiển thị Dashboard dưới dạng AlertDialog toàn diện."""
        streak_data = AuthService.get_user_streak(self.user.username)
        progress_data = AuthService.get_user_progress(self.user.username)

        # ---------------------------------------------------------
        # 1. THẺ HỒ SƠ HỌC SINH (PROFILE BANNER)
        # ---------------------------------------------------------
        profile_banner = ft.Container(
            content=ft.Row([
                # Avatar tròn lớn
                ft.Container(
                    content=ft.Text(self.user.avatar, size=32),
                    width=60,
                    height=60,
                    border_radius=30,
                    bgcolor=ft.Colors.WHITE,
                    alignment=ft.Alignment.CENTER,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), offset=ft.Offset(0, 2))
                ),
                # Tên & Lớp
                ft.Column([
                    ft.Row([
                        ft.Text(self.user.display_name, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ft.Container(
                            content=ft.Text(f"@{self.user.username}", size=11, color=ft.Colors.INDIGO_700, weight=ft.FontWeight.W_500),
                            bgcolor=ft.Colors.INDIGO_100,
                            padding=ft.Padding(6, 2, 6, 2),
                            border_radius=6
                        )
                    ], spacing=8),
                    ft.Text(self.user.grade_class or "Học sinh THCS", size=12, color=ft.Colors.GREY_700),
                    ft.Text(f"Tham gia: {self.user.created_at or 'Học kỳ I 2026'}", size=11, color=ft.Colors.GREY_500)
                ], spacing=2, expand=True),
                # Huy hiệu tóm tắt
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("🔥", size=18),
                            ft.Text(f"{streak_data['streak_count']} Ngày", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
                        ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Text("Chuỗi liên tục", size=10, color=ft.Colors.AMBER_800, weight=ft.FontWeight.W_500)
                    ], spacing=1, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.AMBER_100,
                    padding=ft.Padding(12, 8, 12, 8),
                    border_radius=12,
                    border=ft.Border.all(1.5, ft.Colors.AMBER_400)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.INDIGO_50,
            padding=ft.Padding(16, 14, 16, 14),
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_200)
        )

        # ---------------------------------------------------------
        # 2. KHỐI STREAK & LỊCH 7 NGÀY TRONG TUẦN
        # ---------------------------------------------------------
        week_days_row = []
        for day in streak_data["week_days"]:
            is_studied = day["studied"]
            is_today = day["is_today"]
            
            if is_studied:
                day_bg = ft.Colors.AMBER_500
                day_border = ft.Colors.AMBER_600
                day_text_color = ft.Colors.WHITE
                status_icon = ft.Text("🔥", size=14)
            else:
                day_bg = ft.Colors.GREY_100
                day_border = ft.Colors.GREY_300
                day_text_color = ft.Colors.GREY_600
                status_icon = ft.Text("○", size=14, color=ft.Colors.GREY_400)

            week_days_row.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(day["label"], size=11, weight=ft.FontWeight.BOLD, color=day_text_color),
                        status_icon,
                        ft.Text("Hôm nay" if is_today else day["date"].split("-")[-1], size=9, color=day_text_color)
                    ], spacing=2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=day_bg,
                    border=ft.Border.all(2 if is_today else 1, ft.Colors.INDIGO_700 if is_today else day_border),
                    border_radius=10,
                    width=48,
                    height=64,
                    shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.15, ft.Colors.AMBER_500), offset=ft.Offset(0, 2)) if is_studied else None
                )
            )

        streak_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED, color=ft.Colors.AMBER_600, size=20),
                    ft.Text("CHUỖI NGÀY HỌC LIÊN TỤC (STREAK)", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Container(
                        content=ft.Text(f"Kỷ lục: {streak_data['max_streak']} ngày 🏆", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_800),
                        bgcolor=ft.Colors.AMBER_50,
                        padding=ft.Padding(8, 2, 8, 2),
                        border_radius=8
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(
                    f"🔥 Tuyệt vời! Em đã học liên tục {streak_data['streak_count']} ngày! Học đều đặn mỗi ngày giúp tư duy phản xạ khoa học phát triển vượt trội.",
                    size=11,
                    color=ft.Colors.GREY_700
                ),
                ft.Row(week_days_row, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_200)
        )

        # ---------------------------------------------------------
        # 3. KHỐI TIẾN ĐỘ HỌC TẬP 3 MẠCH KHTN 7
        # ---------------------------------------------------------
        progress_val = progress_data["progress_percent"] / 100.0

        def domain_chip(icon_str: str, label: str, completed: int, total: int, color_theme: str):
            colors_map = {
                "blue": (ft.Colors.BLUE_50, ft.Colors.BLUE_200, ft.Colors.BLUE_800, ft.Colors.BLUE_600),
                "purple": (ft.Colors.PURPLE_50, ft.Colors.PURPLE_200, ft.Colors.PURPLE_800, ft.Colors.PURPLE_600),
                "green": (ft.Colors.GREEN_50, ft.Colors.GREEN_200, ft.Colors.GREEN_800, ft.Colors.GREEN_600),
            }
            bg, border, text_c, bar_c = colors_map.get(color_theme, colors_map["blue"])
            pct = int((completed / total) * 100) if total > 0 else 0

            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(icon_str, size=16),
                        ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color=text_c)
                    ], spacing=4),
                    ft.Text(f"{completed}/{total} bài ({pct}%)", size=11, color=text_c, weight=ft.FontWeight.W_500),
                    ft.ProgressBar(value=completed / total, color=bar_c, bgcolor=ft.Colors.WHITE, height=6)
                ], spacing=4),
                bgcolor=bg,
                border=ft.Border.all(1, border),
                border_radius=10,
                padding=10,
                expand=True
            )

        progress_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.TRENDING_UP_ROUNDED, color=ft.Colors.INDIGO_700, size=20),
                    ft.Text("TIẾN ĐỘ HỌC TẬP KHOA HỌC TỰ NHIÊN 7", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Text(f"{progress_data['total_completed']}/{progress_data['total_target']} Bài ({progress_data['progress_percent']}%)", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(value=progress_val, color=ft.Colors.INDIGO_600, bgcolor=ft.Colors.INDIGO_100, height=8),
                ft.Row([
                    domain_chip("⚡", "Vật lý", progress_data["physics_completed"], 4, "blue"),
                    domain_chip("🧪", "Hóa học", progress_data["chemistry_completed"], 4, "purple"),
                    domain_chip("🌿", "Sinh học", progress_data["biology_completed"], 4, "green"),
                ], spacing=8),
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.TIMER_OUTLINED, size=14, color=ft.Colors.GREY_600),
                        ft.Text(f"Thời gian tự học: {progress_data['total_study_minutes']} phút", size=11, color=ft.Colors.GREY_700)
                    ], spacing=4),
                    ft.Row([
                        ft.Icon(ft.Icons.STAR_ROUNDED, size=16, color=ft.Colors.AMBER_500),
                        ft.Text(f"Điểm Rubric TB: {progress_data['avg_rubric']}/6.0", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                    ], spacing=4),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_200)
        )

        # ---------------------------------------------------------
        # 4. KHỐI SỔ TAY TỰ HỌC NHANH (NOTEBOOK SHORTCUT)
        # ---------------------------------------------------------
        def open_notebook_action(_):
            safe_close_dialog(self.page, self.dialog)
            if self.on_open_notebook:
                self.on_open_notebook()

        notebook_shortcut = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=ft.Colors.CYAN_800, size=24),
                        bgcolor=ft.Colors.CYAN_100,
                        width=44,
                        height=44,
                        border_radius=22,
                        alignment=ft.Alignment.CENTER
                    ),
                    ft.Column([
                        ft.Text("SỔ TAY TỰ HỌC CỦA EM 📓", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_900),
                        ft.Text(f"Đã lưu trữ {progress_data['notebook_count']} bài học và sơ đồ nhánh", size=11, color=ft.Colors.CYAN_800)
                    ], spacing=2)
                ], spacing=10),
                ft.FilledButton(
                    "Mở Sổ Tay Tự Học 📖",
                    icon=ft.Icons.AUTO_STORIES_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_800, color=ft.Colors.WHITE),
                    on_click=open_notebook_action
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.CYAN_50,
            border=ft.Border.all(1.5, ft.Colors.CYAN_300),
            border_radius=12,
            padding=12
        )

        # ---------------------------------------------------------
        # 5. KHỐI HUY HIỆU DANH DỰ (ACHIEVEMENT BADGES)
        # ---------------------------------------------------------
        badge_chips = []
        for b in progress_data["badges"]:
            is_unlocked = b["unlocked"]
            badge_chips.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(b["icon"], size=16),
                        ft.Column([
                            ft.Text(b["name"], size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900 if is_unlocked else ft.Colors.GREY_500),
                            ft.Text(b["desc"], size=9, color=ft.Colors.GREY_600 if is_unlocked else ft.Colors.GREY_400)
                        ], spacing=0)
                    ], spacing=6),
                    bgcolor=ft.Colors.WHITE if is_unlocked else ft.Colors.GREY_100,
                    border=ft.Border.all(1, ft.Colors.AMBER_300 if is_unlocked else ft.Colors.GREY_300),
                    border_radius=8,
                    padding=ft.Padding(8, 4, 8, 4)
                )
            )

        badge_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.MILITARY_TECH_ROUNDED, color=ft.Colors.AMBER_600, size=18),
                    ft.Text("HUY HIỆU DANH DỰ ĐẠT ĐƯỢC", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                ft.Row(badge_chips, wrap=True, spacing=6)
            ], spacing=6),
            bgcolor=ft.Colors.WHITE,
            padding=12,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_200)
        )

        # ---------------------------------------------------------
        # 6. KHỐI TÀI KHOẢN & ĐĂNG XUẤT (ACCOUNT ACTIONS)
        # ---------------------------------------------------------
        def switch_account_action(_):
            safe_close_dialog(self.page, self.dialog)
            if self.on_switch_account:
                self.on_switch_account()

        def logout_action(_):
            safe_close_dialog(self.page, self.dialog)
            if self.on_logout:
                self.on_logout()

        # Toàn bộ nội dung cuộn được
        dialog_content = ft.Container(
            content=ft.Column([
                profile_banner,
                streak_card,
                progress_card,
                notebook_shortcut,
                badge_section,
            ], spacing=12, scroll=ft.ScrollMode.AUTO),
            width=680,
            height=580,
            padding=ft.Padding(4, 0, 4, 0)
        )

        # Dialog
        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.ANALYTICS_ROUNDED, color=ft.Colors.INDIGO_700, size=24),
                ft.Text("Bảng Theo Dõi Học Tập & Streak 📊", size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=dialog_content,
            actions=[
                ft.Row([
                    ft.Row([
                        ft.OutlinedButton(
                            "Đổi Tài Khoản 🔄",
                            icon=ft.Icons.SWITCH_ACCOUNT_ROUNDED,
                            on_click=switch_account_action
                        ),
                        ft.OutlinedButton(
                            "Đăng Xuất",
                            icon=ft.Icons.LOGOUT_ROUNDED,
                            style=ft.ButtonStyle(color=ft.Colors.RED_700),
                            on_click=logout_action
                        ),
                    ], spacing=8),
                    ft.FilledButton(
                        "Đóng",
                        icon=ft.Icons.CLOSE_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE),
                        on_click=lambda _: safe_close_dialog(self.page, self.dialog)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, expand=True)
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        safe_open_dialog(self.page, self.dialog)
