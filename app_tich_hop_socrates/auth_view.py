"""
Module: auth_view.py
Chức năng: Giao diện Đăng nhập / Tạo tài khoản / Khôi phục mật khẩu / Quản lý hồ sơ chuẩn Web hiện đại
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Nguyên tắc thiết kế chuẩn Web:
- Bố cục Split Web Layout: Hero Banner giới thiệu sứ mệnh sư phạm bên trái & Trung tâm xác thực bên phải.
- Hỗ trợ đầy đủ các tính năng xác thực web thực thụ:
  + Đăng nhập tài khoản & Ghi nhớ phiên (Remember Me).
  + Tạo tài khoản học sinh kèm thanh đo độ mạnh mật khẩu (Password Strength Meter) & Xác nhận mật khẩu.
  + Câu hỏi bảo mật để tự Khôi phục mật khẩu khi quên (Forgot Password Recovery).
  + Chế độ Khách Trải Nghiệm Ẩn Danh (COPPA Child Privacy Safe).
  + Đăng nhập nhanh 1-chạm (Saved Profiles / Social-like Fast Login) cho học sinh mẫu & Ban Giám khảo.
  + Hộp thoại Quản lý Hồ sơ & Đổi Mật Khẩu an toàn trong phiên học.
- Tuyệt đối tương thích 100% với Flet 1.0.1+ (không dùng ft.Tabs gây crash).
"""

from typing import Callable, Optional, List, Dict, Any
import flet as ft

from app_tich_hop_socrates.auth_service import (
    AuthService,
    UserAccount,
    evaluate_password_strength
)
from app_tich_hop_socrates.parent_service import ParentService, ParentAccount
from app_tich_hop_socrates.dashboard_view import safe_open_dialog, safe_close_dialog

AVATAR_OPTIONS = [
    {"emoji": "💡", "label": "Nhà phát minh"},
    {"emoji": "🌿", "label": "Nhà sinh học"},
    {"emoji": "🔬", "label": "Nhà hóa học"},
    {"emoji": "🚀", "label": "Phi hành gia"},
    {"emoji": "⭐", "label": "Ngôi sao nhỏ"},
    {"emoji": "🦉", "label": "Cú thông thái"},
    {"emoji": "🦊", "label": "Cáo thông minh"},
    {"emoji": "🐬", "label": "Cá heo trí tuệ"},
    {"emoji": "🎨", "label": "Họa sĩ nhí"},
    {"emoji": "🏆", "label": "Nhà vô địch"},
]

SECURITY_QUESTIONS = [
    "Môn học KHTN em yêu thích nhất?",
    "Nhà khoa học em ngưỡng mộ nhất (Newton, Einstein, Pasteur)?",
    "Tên con vật nuôi hoặc đồ chơi yêu quý nhất của em?",
    "Biệt danh thời thơ ấu của em?",
    "Thí nghiệm khoa học em ấn tượng nhất?"
]


class LoginScreenView:
    """
    Màn hình Đăng Nhập & Cổng Xác Thực chính theo phong cách Trang Web Thực Thụ.
    """
    def __init__(
        self,
        page: ft.Page,
        on_login_success: Callable[[UserAccount], None],
        on_parent_login_success: Optional[Callable[[ParentAccount], None]] = None,
        initial_role: str = "student"
    ):
        self.page = page
        self.on_login_success = on_login_success
        self.on_parent_login_success = on_parent_login_success or (lambda p: None)
        self.active_role = initial_role  # "student" (Học sinh) hoặc "parent" (Phụ huynh)
        self.mode = "login"  # student modes: "login", "register", "forgot", "guest"
        self.parent_mode = "login"  # parent modes: "login", "register"
        self.selected_avatar = "💡"
        self.avatar_chips: List[ft.Container] = []

        # Các thành phần container chủ lực của giao diện
        self.role_selector_bar = ft.Container()
        self.role_content_container = ft.Container(expand=True)
        self.form_host = ft.Container(expand=True)

        # Trạng thái hiện/ẩn mật khẩu học sinh
        self.show_login_pass = False
        self.show_reg_pass = False
        self.show_reg_confirm = False
        self.show_forgot_pass = False
        self.show_forgot_confirm = False

        # Trạng thái hiện/ẩn mật khẩu phụ huynh
        self.show_parent_login_pass = False
        self.show_parent_reg_pass = False
        self.show_parent_stu_pass = False

        # Kiểm tra phiên đã ghi nhớ trước đó
        self.session_info = AuthService.get_session_info()
        self.remembered_user: Optional[UserAccount] = None
        if self.session_info.get("remember_me") and self.session_info.get("current_username"):
            users = AuthService.load_all_users()
            self.remembered_user = users.get(self.session_info["current_username"])

        # Trạng thái hiển thị giao diện Tài khoản đã ghi nhớ (Saved Account Hub)
        # Mặc định luôn là False để hiện trực tiếp form nhập Tên tài khoản & Mật khẩu
        self.show_saved_account = False

    def _safe_open_dialog(self, dialog: ft.AlertDialog):
        """Mở hộp thoại an toàn tương thích 100% Flet."""
        safe_open_dialog(self.page, dialog)

    def _safe_close_dialog(self, dialog: ft.AlertDialog):
        """Đóng hộp thoại an toàn tương thích 100% Flet."""
        safe_close_dialog(self.page, dialog)

    def _switch_to_manual_login(self):
        """Chuyển sang form nhập tài khoản thủ công (Đăng nhập tài khoản khác)."""
        self.show_saved_account = False
        self.mode = "login"
        self._update_tab_visuals()
        self._refresh_active_form()
        if hasattr(self, "quick_login_section") and self.quick_login_section:
            self.quick_login_section.visible = True
        self.page.update()

    def _switch_to_saved_account(self):
        """Quay lại màn hình tài khoản đã lưu."""
        self.show_saved_account = True
        self.mode = "login"
        self._update_tab_visuals()
        self._refresh_active_form()
        if hasattr(self, "quick_login_section") and self.quick_login_section:
            self.quick_login_section.visible = False
        self.page.update()

    def _forget_saved_account(self):
        """Xóa ghi nhớ tài khoản này khỏi thiết bị."""
        AuthService.clear_remembered_account()
        self.remembered_user = None
        self.show_saved_account = False
        self._refresh_active_form()
        if hasattr(self, "quick_login_section") and self.quick_login_section:
            self.quick_login_section.visible = True

        snack = ft.SnackBar(
            content=ft.Row([
                ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, color=ft.Colors.WHITE, size=16),
                ft.Text("Đã xóa lưu tài khoản trên thiết bị này! Lần sau em có thể đăng nhập lại.", color=ft.Colors.WHITE, size=12)
            ], spacing=6),
            bgcolor=ft.Colors.GREY_900
        )
        if hasattr(self.page, "open"):
            self.page.open(snack)
        else:
            self.page.snack_bar = snack
            snack.open = True
        self.page.update()

    def build(self) -> ft.Control:
        """Xây dựng giao diện Cổng Xác Thực chuẩn Web hiện đại."""
        # =====================================================================
        # 1. CỘT TRÁI: HERO SHOWCASE (Web Landing / Sứ mệnh sư phạm & Giá trị)
        # =====================================================================
        left_hero_panel = self._build_left_hero_panel()

        # =====================================================================
        # 2. CỘT PHẢI: AUTH CENTER CARD (Trung tâm Xác thực Đa năng)
        # =====================================================================
        right_auth_card = self._build_right_auth_card()

        # Ghép bố cục 2 cột kiểu Web Responsive
        web_layout = ft.ResponsiveRow([
            ft.Container(
                content=left_hero_panel,
                col={"sm": 12, "md": 12, "lg": 5, "xl": 5},
                padding=10
            ),
            ft.Container(
                content=right_auth_card,
                col={"sm": 12, "md": 12, "lg": 7, "xl": 7},
                padding=10
            )
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START)

        # Thanh chân trang Web (Footer)
        web_footer = ft.Container(
            content=ft.Row([
                ft.Text("© 2026 Socrates Nhí • Cuộc thi Sáng tạo trẻ Quốc gia AI (Bảng A)", size=11, color=ft.Colors.GREY_600),
                ft.Row([
                    ft.Icon(ft.Icons.LOCK_OUTLINE_ROUNDED, size=13, color=ft.Colors.GREEN_700),
                    ft.Text("Chuẩn An Toàn & Bảo Mật Dữ Liệu Học Sinh THCS (COPPA Safe)", size=11, color=ft.Colors.GREEN_800, weight=ft.FontWeight.W_500)
                ], spacing=4)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            padding=ft.Padding(20, 16, 20, 16),
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200))
        )

        return ft.Container(
            content=ft.Column([
                web_layout,
                ft.Container(height=10),
                web_footer
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
            expand=True,
            bgcolor="#F1F5F9",
            padding=ft.Padding(16, 16, 16, 16)
        )

    # -------------------------------------------------------------------------
    # BỘ PHẬN HERO BÊN TRÁI (LEFT HERO SHOWCASE)
    # -------------------------------------------------------------------------
    def _build_left_hero_panel(self) -> ft.Container:
        """Xây dựng bảng giới thiệu hình ảnh, triết lý Socratic và giá trị cốt lõi."""
        # Biểu tượng bóng đèn phát sáng
        logo_row = ft.Row([
            ft.Container(
                content=ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_400, size=32),
                bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
                width=56,
                height=56,
                border_radius=28,
                alignment=ft.Alignment.CENTER,
                border=ft.Border.all(2, ft.Colors.with_opacity(0.3, ft.Colors.AMBER_400)),
                shadow=ft.BoxShadow(blur_radius=14, color=ft.Colors.with_opacity(0.4, ft.Colors.AMBER_400), offset=ft.Offset(0, 4))
            ),
            ft.Column([
                ft.Text("SOCRATES NHÍ 💡", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("Trợ Lý AI Gợi Mở Tư Duy Khoa Học Tự Nhiên 7", size=11, color=ft.Colors.INDIGO_100)
            ], spacing=1)
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        tagline_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.STAR_ROUNDED, color=ft.Colors.AMBER_300, size=15),
                ft.Text("Cuộc thi Sáng tạo trẻ Quốc gia AI 2026 • Bảng A", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_200)
            ], spacing=6),
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            padding=ft.Padding(10, 5, 12, 5),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.25, ft.Colors.AMBER_300))
        )

        quote_box = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.FORMAT_QUOTE_ROUNDED, color=ft.Colors.AMBER_300, size=20),
                    ft.Text("Triết Lý Giáo Dục Socratic", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_200)
                ], spacing=4),
                ft.Text(
                    "\"Tôi không thể dạy ai bất cứ điều gì;\ntôi chỉ có thể làm cho họ suy nghĩ.\"",
                    size=13,
                    italic=True,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.WHITE
                ),
                ft.Text("— Triết gia Socrates", size=10, color=ft.Colors.INDIGO_200, text_align=ft.TextAlign.RIGHT)
            ], spacing=4),
            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
            padding=12,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE))
        )

        # 3 Thẻ Trụ cột Giá trị Sư phạm
        def make_value_card(icon, title, desc, tag_color):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=tag_color, size=20),
                        width=38,
                        height=38,
                        border_radius=19,
                        bgcolor=ft.Colors.with_opacity(0.15, tag_color),
                        alignment=ft.Alignment.CENTER
                    ),
                    ft.Column([
                        ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(desc, size=10, color=ft.Colors.INDIGO_100)
                    ], spacing=2, expand=True)
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                padding=ft.Padding(10, 8, 12, 8),
                border_radius=12,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE))
            )

        card_1 = make_value_card(
            ft.Icons.FORUM_ROUNDED,
            "Gia sư Socratic 5 Pha",
            "Gợi mở từng nấc tư duy khoa học, không giải hộ hay đọc sẵn đáp án.",
            ft.Colors.AMBER_300
        )
        card_2 = make_value_card(
            ft.Icons.SHIELD_ROUNDED,
            "Khiên An Toàn 3 Tầng (FR-07)",
            "Ngăn chặn 100% gian lận & ỷ lại vào máy tính, rèn đức tính tự lập.",
            ft.Colors.GREEN_300
        )
        card_3 = make_value_card(
            ft.Icons.AUTO_GRAPH_ROUNDED,
            "Sổ Tay & Chuỗi Học Streak",
            "Theo dõi tiến độ Vật lý, Hóa học, Sinh học và tích lũy huy hiệu danh dự.",
            ft.Colors.CYAN_300
        )

        return ft.Container(
            content=ft.Column([
                logo_row,
                tagline_badge,
                ft.Container(height=4),
                quote_box,
                ft.Container(height=4),
                ft.Text("✨ GIÁ TRỊ VƯỢT TRỘI CỦA SOCRATES NHÍ:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_200),
                card_1,
                card_2,
                card_3,
                ft.Container(height=4),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=ft.Colors.GREEN_400, size=14),
                        ft.Text("Hoạt động hoàn toàn Offline & Online • Bảo vệ thông tin học sinh 100%", size=10, color=ft.Colors.GREEN_200)
                    ], spacing=6),
                    bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_900),
                    padding=ft.Padding(8, 6, 8, 6),
                    border_radius=8
                )
            ], spacing=10),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#1E1B4B", "#312E81", "#1E293B"]
            ),
            padding=ft.Padding(24, 24, 24, 24),
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK), offset=ft.Offset(0, 6))
        )

    # -------------------------------------------------------------------------
    # BỘ PHẬN TRUNG TÂM XÁC THỰC BÊN PHẢI (RIGHT AUTH CARD)
    # -------------------------------------------------------------------------
    def _build_right_auth_card(self) -> ft.Container:
        """Xây dựng thẻ form tương tác với bộ chọn vai trò Phụ Huynh / Học Sinh."""
        # 1. Thanh chọn vai trò: Học sinh vs Phụ huynh
        if not hasattr(self, "role_selector_bar") or self.role_selector_bar is None:
            self.role_selector_bar = ft.Container()
        self._render_role_selector()

        # 2. Vùng chứa nội dung chính thay đổi theo vai trò
        if not hasattr(self, "role_content_container") or self.role_content_container is None:
            self.role_content_container = ft.Container(expand=True)
        self._refresh_role_content()

        return ft.Container(
            content=ft.Column([
                self.role_selector_bar,
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                self.role_content_container
            ], spacing=12),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(24, 20, 24, 20),
            border_radius=20,
            border=ft.Border.all(1.5, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 6))
        )

    def _render_role_selector(self):
        """Vẽ thanh chọn vai trò: Học sinh vs Phụ huynh."""
        if not hasattr(self, "role_selector_bar") or self.role_selector_bar is None:
            self.role_selector_bar = ft.Container()
        is_student = (self.active_role == "student")

        btn_student = ft.Container(
            content=ft.Row([
                ft.Text("🎒", size=20),
                ft.Column([
                    ft.Text("TÔI LÀ HỌC SINH", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900 if is_student else ft.Colors.GREY_700),
                    ft.Text("Em vào học bài & khám phá KHTN", size=10, color=ft.Colors.INDIGO_700 if is_student else ft.Colors.GREY_500)
                ], spacing=1)
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.INDIGO_50 if is_student else ft.Colors.GREY_100,
            border=ft.Border.all(2 if is_student else 1, ft.Colors.INDIGO_600 if is_student else ft.Colors.GREY_300),
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=12,
            expand=True,
            on_click=lambda _: self._switch_role("student"),
            ink=True
        )

        btn_parent = ft.Container(
            content=ft.Row([
                ft.Text("👨‍👩‍👧‍👦", size=20),
                ft.Column([
                    ft.Text("TÔI LÀ PHỤ HUYNH", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_900 if not is_student else ft.Colors.GREY_700),
                    ft.Text("Ba mẹ theo dõi tiến độ con em", size=10, color=ft.Colors.TEAL_700 if not is_student else ft.Colors.GREY_500)
                ], spacing=1)
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.TEAL_50 if not is_student else ft.Colors.GREY_100,
            border=ft.Border.all(2 if not is_student else 1, ft.Colors.TEAL_600 if not is_student else ft.Colors.GREY_300),
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=12,
            expand=True,
            on_click=lambda _: self._switch_role("parent"),
            ink=True
        )

        self.role_selector_bar.content = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.HOW_TO_REG_ROUNDED, size=16, color=ft.Colors.INDIGO_800),
                ft.Text("BẠN ĐĂNG NHẬP VỚI VAI TRÒ NÀO?", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=6),
            ft.Row([btn_student, btn_parent], spacing=10)
        ], spacing=6)

    def _switch_role(self, role: str):
        """Chuyển đổi vai trò người dùng: Học sinh hoặc Phụ huynh."""
        self.active_role = role
        self._render_role_selector()
        self._refresh_role_content()
        self.page.update()

    def _refresh_role_content(self):
        """Cập nhật nội dung thẻ xác thực theo vai trò đã chọn."""
        if not hasattr(self, "role_content_container") or self.role_content_container is None:
            self.role_content_container = ft.Container(expand=True)
        if self.active_role == "student":
            self.role_content_container.content = self._build_student_role_content()
        else:
            self.role_content_container.content = self._build_parent_role_content()

    def _build_student_role_content(self) -> ft.Control:
        """Xây dựng toàn bộ giao diện xác thực của Học Sinh."""
        self.btn_nav_login = self._create_tab_button("login", ft.Icons.LOGIN_ROUNDED, "Đăng Nhập")
        self.btn_nav_register = self._create_tab_button("register", ft.Icons.PERSON_ADD_ROUNDED, "Tạo Tài Khoản")
        self.btn_nav_guest = self._create_tab_button("guest", ft.Icons.PERSON_OUTLINE_ROUNDED, "Khách Trải Nghiệm")

        tabs_row = ft.Row([
            self.btn_nav_login,
            self.btn_nav_register,
            self.btn_nav_guest
        ], spacing=8)

        self.form_host = ft.Container(expand=True)
        self._refresh_active_form()
        self.quick_login_section = self._build_quick_login_section()
        self._update_tab_visuals()

        return ft.Column([
            tabs_row,
            ft.Divider(height=1, color=ft.Colors.GREY_200),
            self.form_host,
            ft.Divider(height=1, color=ft.Colors.GREY_200),
            self.quick_login_section
        ], spacing=12)

    def _build_parent_role_content(self) -> ft.Control:
        """Xây dựng giao diện xác thực dành riêng cho Phụ Huynh."""
        is_p_login = (self.parent_mode == "login")

        btn_p_login = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LOGIN_ROUNDED, size=15, color=ft.Colors.TEAL_800 if is_p_login else ft.Colors.GREY_600),
                ft.Text("Đăng Nhập Phụ Huynh", size=12, weight=ft.FontWeight.BOLD if is_p_login else ft.FontWeight.NORMAL, color=ft.Colors.TEAL_800 if is_p_login else ft.Colors.GREY_700)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=10,
            expand=True,
            bgcolor=ft.Colors.TEAL_50 if is_p_login else ft.Colors.GREY_100,
            border=ft.Border.all(2 if is_p_login else 1, ft.Colors.TEAL_700 if is_p_login else ft.Colors.GREY_300),
            on_click=lambda _: self._switch_parent_mode("login"),
            ink=True
        )

        btn_p_reg = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PERSON_ADD_ROUNDED, size=15, color=ft.Colors.GREEN_700 if not is_p_login else ft.Colors.GREY_600),
                ft.Text("Tạo Tài Khoản Phụ Huynh", size=12, weight=ft.FontWeight.BOLD if not is_p_login else ft.FontWeight.NORMAL, color=ft.Colors.GREEN_800 if not is_p_login else ft.Colors.GREY_700)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=10,
            expand=True,
            bgcolor=ft.Colors.GREEN_50 if not is_p_login else ft.Colors.GREY_100,
            border=ft.Border.all(2 if not is_p_login else 1, ft.Colors.GREEN_700 if not is_p_login else ft.Colors.GREY_300),
            on_click=lambda _: self._switch_parent_mode("register"),
            ink=True
        )

        p_tabs_row = ft.Row([btn_p_login, btn_p_reg], spacing=8)
        p_form = self._build_parent_login_form() if is_p_login else self._build_parent_register_form()
        p_quick = self._build_parent_quick_login_section()

        return ft.Column([
            p_tabs_row,
            ft.Divider(height=1, color=ft.Colors.GREY_200),
            p_form,
            ft.Divider(height=1, color=ft.Colors.GREY_200),
            p_quick
        ], spacing=12)

    def _switch_parent_mode(self, mode: str):
        """Chuyển đổi tab Phụ huynh."""
        self.parent_mode = mode
        self.role_content_container.content = self._build_parent_role_content()
        self.page.update()

    def _build_parent_login_form(self) -> ft.Control:
        """Form đăng nhập tài khoản Phụ huynh."""
        txt_parent_user = ft.TextField(
            label="Tên tài khoản phụ huynh",
            hint_text="Ví dụ: ph_baonhat hoặc ph_minhtriet",
            prefix_icon=ft.Icons.ACCOUNT_CIRCLE_ROUNDED,
            dense=True,
            border_radius=10
        )

        txt_parent_pass = ft.TextField(
            label="Mật khẩu phụ huynh",
            hint_text="Nhập mật khẩu (mẫu: 123)",
            prefix_icon=ft.Icons.LOCK_ROUNDED,
            password=True,
            can_reveal_password=True,
            dense=True,
            border_radius=10
        )

        msg_box = ft.Container(visible=False)

        def do_parent_login(_):
            uname = txt_parent_user.value or ""
            pwd = txt_parent_pass.value or ""

            ok, parent, msg = ParentService.authenticate_parent(uname, pwd)
            if ok and parent:
                msg_box.visible = True
                msg_box.bgcolor = ft.Colors.GREEN_50
                msg_box.border = ft.Border.all(1, ft.Colors.GREEN_300)
                msg_box.content = ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                    ft.Text(msg, size=12, color=ft.Colors.GREEN_900, weight=ft.FontWeight.W_500, expand=True)
                ], spacing=6)
                self.page.update()
                self.on_parent_login_success(parent)
            else:
                msg_box.visible = True
                msg_box.bgcolor = ft.Colors.RED_50
                msg_box.border = ft.Border.all(1, ft.Colors.RED_300)
                msg_box.content = ft.Row([
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=ft.Colors.RED_700, size=16),
                    ft.Text(msg, size=12, color=ft.Colors.RED_900, weight=ft.FontWeight.W_500, expand=True)
                ], spacing=6)
                self.page.update()

        btn_submit = ft.FilledButton(
            "ĐĂNG NHẬP VÀO CỔNG PHỤ HUYNH 👨‍👩‍👧‍👦",
            icon=ft.Icons.LOGIN_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL_800,
                color=ft.Colors.WHITE,
                padding=ft.Padding(20, 14, 20, 14),
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            width=540,
            on_click=do_parent_login
        )

        return ft.Column([
            ft.Text("Đăng nhập Cổng Phụ huynh để theo dõi tiến độ học tập KHTN 7 của con:", size=12, color=ft.Colors.GREY_700),
            txt_parent_user,
            txt_parent_pass,
            msg_box,
            btn_submit,
            ft.Row([
                ft.Text("Chưa có tài khoản phụ huynh?", size=11, color=ft.Colors.GREY_600),
                ft.TextButton(
                    "Tạo tài khoản & liên kết con em ngay 👉",
                    style=ft.ButtonStyle(color=ft.Colors.TEAL_800),
                    on_click=lambda _: self._switch_parent_mode("register")
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=4)
        ], spacing=10)

    def _build_parent_register_form(self) -> ft.Control:
        """Form tạo tài khoản Phụ huynh mới kèm xác thực con em."""
        txt_p_user = ft.TextField(
            label="Tên đăng nhập phụ huynh (viết liền)",
            hint_text="Ví dụ: ph_nguyenvan, ph_thuha...",
            prefix_icon=ft.Icons.PERSON_PIN_ROUNDED,
            dense=True,
            border_radius=10
        )

        txt_p_name = ft.TextField(
            label="Họ và tên Quý phụ huynh",
            hint_text="Ví dụ: Bác Nguyễn Văn An, Cô Trần Thu Hà...",
            prefix_icon=ft.Icons.BADGE_ROUNDED,
            dense=True,
            border_radius=10
        )

        txt_p_phone = ft.TextField(
            label="Số điện thoại liên lạc",
            hint_text="0912...",
            prefix_icon=ft.Icons.PHONE_ROUNDED,
            dense=True,
            border_radius=10
        )

        txt_p_pass = ft.TextField(
            label="Mật khẩu tài khoản phụ huynh",
            hint_text="Tối thiểu 3 ký tự",
            prefix_icon=ft.Icons.LOCK_ROUNDED,
            password=True,
            can_reveal_password=True,
            dense=True,
            border_radius=10
        )

        # Khung xác thực con em (học sinh)
        txt_stu_user = ft.TextField(
            label="Tên tài khoản con em (Học sinh)",
            hint_text="minhtriet, baonhat, baoan, huyhoang...",
            prefix_icon=ft.Icons.SCHOOL_ROUNDED,
            dense=True,
            border_radius=10
        )

        txt_stu_pass = ft.TextField(
            label="Mật khẩu của con em",
            hint_text="Mật khẩu con em đang dùng (mẫu: 123)",
            prefix_icon=ft.Icons.PASSWORD_ROUNDED,
            password=True,
            can_reveal_password=True,
            dense=True,
            border_radius=10
        )

        child_verify_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SECURITY_ROUNDED, color=ft.Colors.TEAL_800, size=16),
                    ft.Text("XÁC THỰC CON EM CẦN THEO DÕI 🎒", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_900)
                ], spacing=6),
                ft.Text("Để bảo mật quyền riêng tư học đường, Quý phụ huynh cần nhập tài khoản & mật khẩu của con em để liên kết:", size=11, color=ft.Colors.GREY_700),
                txt_stu_user,
                txt_stu_pass,
                ft.Text("💡 Sau khi tạo xong, phụ huynh có thể bấm nút 'Thêm người theo dõi' nếu muốn theo dõi thêm con thứ 2, thứ 3...", size=10, italic=True, color=ft.Colors.TEAL_800)
            ], spacing=8),
            bgcolor=ft.Colors.TEAL_50,
            padding=12,
            border_radius=10,
            border=ft.Border.all(1.5, ft.Colors.TEAL_300)
        )

        msg_box = ft.Container(visible=False)

        def do_parent_reg(_):
            pu = txt_p_user.value or ""
            pn = txt_p_name.value or ""
            pp = txt_p_phone.value or ""
            pw = txt_p_pass.value or ""
            su = txt_stu_user.value or ""
            sp = txt_stu_pass.value or ""

            ok, parent, msg = ParentService.register_parent(
                parent_username=pu,
                parent_password=pw,
                display_name=pn,
                phone_number=pp,
                student_username=su,
                student_password=sp
            )

            if ok and parent:
                msg_box.visible = True
                msg_box.bgcolor = ft.Colors.GREEN_50
                msg_box.border = ft.Border.all(1, ft.Colors.GREEN_300)
                msg_box.content = ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                    ft.Text(msg, size=12, color=ft.Colors.GREEN_900, weight=ft.FontWeight.W_500, expand=True)
                ], spacing=6)
                self.page.update()
                self.on_parent_login_success(parent)
            else:
                msg_box.visible = True
                msg_box.bgcolor = ft.Colors.RED_50
                msg_box.border = ft.Border.all(1, ft.Colors.RED_300)
                msg_box.content = ft.Row([
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=ft.Colors.RED_700, size=16),
                    ft.Text(msg, size=12, color=ft.Colors.RED_900, weight=ft.FontWeight.W_500, expand=True)
                ], spacing=6)
                self.page.update()

        btn_submit = ft.FilledButton(
            "TẠO TÀI KHOẢN PHỤ HUYNH & BẮT ĐẦU THEO DÕI 🚀",
            icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
                padding=ft.Padding(20, 14, 20, 14),
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            width=540,
            on_click=do_parent_reg
        )

        return ft.Column([
            ft.Text("Thông tin Quý phụ huynh:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
            ft.Row([txt_p_user, txt_p_name], spacing=8),
            ft.Row([txt_p_phone, txt_p_pass], spacing=8),
            child_verify_card,
            msg_box,
            btn_submit,
            ft.Row([
                ft.Text("Đã có tài khoản phụ huynh?", size=11, color=ft.Colors.GREY_600),
                ft.TextButton(
                    "Đăng nhập ngay 👉",
                    style=ft.ButtonStyle(color=ft.Colors.TEAL_800),
                    on_click=lambda _: self._switch_parent_mode("login")
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=4)
        ], spacing=10)

    def _build_parent_quick_login_section(self) -> ft.Control:
        """Đăng nhập nhanh 1-chạm cho Phụ Huynh Mẫu & Ban Giám khảo chấm thi."""
        parents = ParentService.load_all_parents()
        demo_parent_keys = ["ph_baonhat", "ph_minhtriet"]

        demo_chips = []
        for pkey in demo_parent_keys:
            p = parents.get(pkey)
            if not p:
                continue

            def make_handler(parent_obj=p):
                return lambda _: self._do_parent_quick_login(parent_obj)

            sub_info = f"Theo dõi: {', '.join(p.children_usernames)}"
            chip = ft.Container(
                content=ft.Row([
                    ft.Text(p.avatar, size=18),
                    ft.Column([
                        ft.Text(p.display_name, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_900),
                        ft.Text(sub_info, size=9, color=ft.Colors.GREY_600)
                    ], spacing=1)
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.TEAL_50,
                padding=ft.Padding(10, 6, 12, 6),
                border_radius=10,
                border=ft.Border.all(1, ft.Colors.TEAL_200),
                tooltip=f"Bấm để đăng nhập nhanh vai trò {p.display_name}",
                on_click=make_handler(),
                ink=True
            )
            demo_chips.append(chip)

        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.FLASH_ON_ROUNDED, size=16, color=ft.Colors.TEAL_800),
                ft.Text("⚡ Đăng nhập Nhanh 1-Chạm (Tài khoản Phụ huynh mẫu & Ban Giám khảo):", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800)
            ], spacing=4),
            ft.Row(demo_chips, wrap=True, spacing=8)
        ], spacing=6)

    def _do_parent_quick_login(self, parent: ParentAccount):
        """Xử lý đăng nhập nhanh phụ huynh."""
        ok, p, _ = ParentService.authenticate_parent(parent.username, "123")
        if ok and p:
            self.on_parent_login_success(p)

    def _create_tab_button(self, mode_id: str, icon, label: str) -> ft.Container:
        """Tạo nút Tab chuyển chế độ chuẩn Web."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=15),
                ft.Text(label, size=12, weight=ft.FontWeight.W_500)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=10,
            expand=True,
            on_click=lambda _: self._switch_to_mode(mode_id),
            ink=True
        )

    def _update_tab_visuals(self):
        """Cập nhật màu sắc các nút Tab theo chế độ hiện tại."""
        tabs = [
            ("login", self.btn_nav_login, ft.Colors.INDIGO_700, ft.Colors.INDIGO_50),
            ("register", self.btn_nav_register, ft.Colors.GREEN_700, ft.Colors.GREEN_50),
            ("guest", self.btn_nav_guest, ft.Colors.AMBER_800, ft.Colors.AMBER_50)
        ]

        for mode_id, tab, primary_color, light_bg in tabs:
            is_active = (self.mode == mode_id)
            row = tab.content
            icon_ctrl = row.controls[0]
            text_ctrl = row.controls[1]

            if is_active:
                tab.bgcolor = light_bg
                tab.border = ft.Border.all(2, primary_color)
                tab.shadow = ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2))
                icon_ctrl.color = primary_color
                text_ctrl.color = primary_color
                text_ctrl.weight = ft.FontWeight.BOLD
            else:
                tab.bgcolor = ft.Colors.GREY_100
                tab.border = ft.Border.all(1, ft.Colors.GREY_300)
                tab.shadow = None
                icon_ctrl.color = ft.Colors.GREY_600
                text_ctrl.color = ft.Colors.GREY_700
                text_ctrl.weight = ft.FontWeight.NORMAL

    def _switch_to_mode(self, new_mode: str):
        """Chuyển đổi trạng thái hiển thị Form."""
        self.mode = new_mode
        self._update_tab_visuals()
        self._refresh_active_form()
        self.page.update()

    def _refresh_active_form(self):
        """Nạp form tương ứng vào form_host."""
        if self.mode == "login":
            self.form_host.content = self._build_login_form()
            if hasattr(self, "quick_login_section") and self.quick_login_section:
                self.quick_login_section.visible = True
        elif self.mode == "register":
            self.form_host.content = self._build_register_form()
            if hasattr(self, "quick_login_section") and self.quick_login_section:
                self.quick_login_section.visible = True
        elif self.mode == "forgot":
            self.form_host.content = self._build_forgot_password_form()
            if hasattr(self, "quick_login_section") and self.quick_login_section:
                self.quick_login_section.visible = True
        elif self.mode == "guest":
            self.form_host.content = self._build_guest_mode_form()
            if hasattr(self, "quick_login_section") and self.quick_login_section:
                self.quick_login_section.visible = False

    # -------------------------------------------------------------------------
    # GIAO DIỆN TÀI KHOẢN ĐÃ LƯU (SAVED ACCOUNT HUB)
    # -------------------------------------------------------------------------
    def _build_saved_account_hub(self) -> ft.Control:
        """
        Màn hình Tài Khoản Đã Lưu:
        Chỉ hiển thị thông tin học sinh đã lưu kèm nút 'VÀO HỌC TIẾP' to rõ.
        TUYỆT ĐỐI KHÔNG hiển thị form nhập mật khẩu / username bên dưới.
        Cho phép bấm nút 'Đổi tài khoản khác 🔄' để chuyển sang form nhập.
        """
        u = self.remembered_user
        if not u:
            return self._build_login_form()

        # Tính chuỗi streak thực tế và kiểm tra hôm nay đã giải bài chưa
        streak_info = AuthService.get_user_streak(u.username)
        s_count = streak_info.get("streak_count", getattr(u, "streak_count", 0))
        today_studied = streak_info.get("today_studied", False)
        if today_studied:
            streak_text = f"🔥 Chuỗi {s_count} ngày (Đã giải hôm nay ✓)"
            streak_color = ft.Colors.GREEN_800
        else:
            if s_count > 0:
                streak_text = f"🔥 Chuỗi {s_count} ngày (Chưa giải hôm nay ⏳)"
                streak_color = ft.Colors.AMBER_900
            else:
                streak_text = "🔥 Chuỗi 0 ngày (Bắt đầu chuỗi mới 🌱)"
                streak_color = ft.Colors.ORANGE_800

        # Thẻ thông tin học sinh dạng Hero Card sang trọng
        avatar_box = ft.Container(
            content=ft.Text(u.avatar, size=38),
            width=68,
            height=68,
            border_radius=34,
            bgcolor=ft.Colors.WHITE,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(2.5, ft.Colors.INDIGO_300),
            shadow=ft.BoxShadow(blur_radius=14, color=ft.Colors.with_opacity(0.18, ft.Colors.INDIGO_700), offset=ft.Offset(0, 4))
        )

        user_info_col = ft.Column([
            ft.Row([
                ft.Text(u.display_name, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=12, color=ft.Colors.GREEN_700),
                        ft.Text("Đã Lưu 💾", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800)
                    ], spacing=3),
                    bgcolor=ft.Colors.GREEN_100,
                    padding=ft.Padding(6, 2, 8, 2),
                    border_radius=6,
                    border=ft.Border.all(0.8, ft.Colors.GREEN_300)
                )
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text(f"{u.grade_class} • @{u.username}", size=11, color=ft.Colors.GREY_700),
            ft.Row([
                ft.Text(streak_text, size=11, weight=ft.FontWeight.W_500, color=streak_color),
                ft.Text("•", size=11, color=ft.Colors.GREY_400),
                ft.Text(f"📓 {u.physics_count + u.chemistry_count + u.biology_count} bài học trong Sổ tay", size=11, color=ft.Colors.INDIGO_800)
            ], spacing=4)
        ], spacing=3, expand=True)

        profile_hero_card = ft.Container(
            content=ft.Row([
                avatar_box,
                user_info_col
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#EEF2FF", "#E0E7FF"]
            ),
            padding=ft.Padding(18, 16, 18, 16),
            border_radius=16,
            border=ft.Border.all(1.5, ft.Colors.INDIGO_200),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        btn_resume_study = ft.FilledButton(
            f"VÀO HỌC TIẾP VỚI {u.display_name.upper()} 🚀",
            icon=ft.Icons.ROCKET_LAUNCH_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.INDIGO_700,
                color=ft.Colors.WHITE,
                padding=ft.Padding(20, 16, 20, 16),
                shape=ft.RoundedRectangleBorder(radius=12)
            ),
            width=540,
            on_click=lambda _: self._do_quick_login(u.username)
        )

        btn_switch_other = ft.OutlinedButton(
            "Đăng nhập bằng tài khoản khác 🔄",
            icon=ft.Icons.SWITCH_ACCOUNT_ROUNDED,
            style=ft.ButtonStyle(
                color=ft.Colors.INDIGO_900,
                padding=ft.Padding(16, 12, 16, 12),
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            width=540,
            on_click=lambda _: self._switch_to_manual_login()
        )

        btn_create_new = ft.TextButton(
            "Chưa có tài khoản? Tạo tài khoản mới ✨",
            style=ft.ButtonStyle(color=ft.Colors.GREEN_800),
            on_click=lambda _: self._switch_to_mode("register")
        )

        btn_forget = ft.TextButton(
            "Xóa lưu tài khoản này khỏi máy này 🗑️",
            style=ft.ButtonStyle(color=ft.Colors.GREY_600),
            on_click=lambda _: self._forget_saved_account()
        )

        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.LOCK_PERSON_ROUNDED, size=16, color=ft.Colors.GREEN_700),
                ft.Text("Chào mừng trở lại! Tài khoản của em đã được ghi nhớ trên thiết bị này:", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_800)
            ], spacing=6),
            profile_hero_card,
            ft.Container(height=4),
            btn_resume_study,
            ft.Divider(height=1, color=ft.Colors.GREY_200),
            ft.Text("Tùy chọn khác:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
            btn_switch_other,
            ft.Row([btn_create_new, btn_forget], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
        ], spacing=10)

    # -------------------------------------------------------------------------
    # FORM 1: ĐĂNG NHẬP THỦ CÔNG (MANUAL SIGN IN FORM)
    # -------------------------------------------------------------------------
    def _build_login_form(self) -> ft.Control:
        """Xây dựng form đăng nhập tài khoản trực tiếp có Tên đăng nhập và Mật khẩu."""
        # Tên đăng nhập và mật khẩu mặc định (ưu tiên tài khoản đã đăng nhập gần nhất)
        default_username = self.remembered_user.username if self.remembered_user else "baonhat"
        default_password = "123"

        # Trường nhập Tên đăng nhập
        txt_username = ft.TextField(
            label="Tên đăng nhập (Username)",
            hint_text="Nhập tên tài khoản của em (vd: baonhat, minhtriet...)",
            prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            value=default_username,
            dense=True,
            border_radius=10
        )
        self.txt_login_username = txt_username

        # Trường nhập Mật khẩu kèm nút hiển thị/ẩn
        txt_password = ft.TextField(
            label="Mật khẩu",
            hint_text="Nhập mật khẩu (Mẫu: 123)",
            prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
            password=True,
            can_reveal_password=True,
            value=default_password,
            dense=True,
            border_radius=10
        )
        self.txt_login_password = txt_password

        # Checkbox Ghi nhớ đăng nhập
        chk_remember = ft.Checkbox(
            label="Ghi nhớ đăng nhập trên thiết bị này",
            value=True,
            active_color=ft.Colors.INDIGO_700
        )

        # Nút Quên mật khẩu
        btn_forgot = ft.TextButton(
            "Quên mật khẩu? 🔑",
            style=ft.ButtonStyle(color=ft.Colors.INDIGO_800),
            on_click=lambda _: self._switch_to_mode("forgot")
        )

        row_options = ft.Row([
            chk_remember,
            btn_forgot
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        msg_box = ft.Container(visible=False)

        def do_login(_):
            uname = (txt_username.value or "").strip()
            upass = (txt_password.value or "").strip()
            rem = bool(chk_remember.value)

            success, user, message = AuthService.authenticate(uname, upass, remember_me=rem)

            if success and user:
                if rem:
                    self.remembered_user = user
                self.show_saved_account = False
                msg_box.visible = True
                msg_box.bgcolor = ft.Colors.GREEN_50
                msg_box.border = ft.Border.all(1, ft.Colors.GREEN_300)
                msg_box.content = ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                    ft.Text(message, size=12, color=ft.Colors.GREEN_900, weight=ft.FontWeight.W_500, expand=True)
                ], spacing=6)
                self.page.update()
                # Kích hoạt đăng nhập thành công
                self.on_login_success(user)
            else:
                msg_box.visible = True
                msg_box.bgcolor = ft.Colors.RED_50
                msg_box.border = ft.Border.all(1, ft.Colors.RED_300)
                msg_box.content = ft.Row([
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=ft.Colors.RED_700, size=16),
                    ft.Text(message, size=12, color=ft.Colors.RED_900, weight=ft.FontWeight.W_500, expand=True)
                ], spacing=6)
                self.page.update()

        btn_submit = ft.FilledButton(
            "ĐĂNG NHẬP VÀO HỌC NGAY 🚀",
            icon=ft.Icons.LOGIN_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.INDIGO_700,
                color=ft.Colors.WHITE,
                padding=ft.Padding(20, 14, 20, 14),
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            width=540,
            on_click=do_login
        )

        link_to_register = ft.Row([
            ft.Text("Chưa có tài khoản?", size=12, color=ft.Colors.GREY_600),
            ft.TextButton(
                "Đăng ký tài khoản mới miễn phí 👉",
                style=ft.ButtonStyle(color=ft.Colors.INDIGO_800),
                on_click=lambda _: self._switch_to_mode("register")
            )
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)

        items = [
            ft.Text("Nhập thông tin tài khoản học sinh để bắt đầu:", size=12, color=ft.Colors.GREY_700),
            txt_username,
            txt_password,
            row_options,
            msg_box,
            btn_submit,
            link_to_register
        ]

        return ft.Column(items, spacing=10)

    # -------------------------------------------------------------------------
    # FORM 2: TẠO TÀI KHOẢN MỚI (REGISTER FORM)
    # -------------------------------------------------------------------------
    def _build_register_form(self) -> ft.Control:
        """Xây dựng form tạo tài khoản mới đầy đủ tiêu chuẩn web."""
        txt_reg_username = ft.TextField(
            label="Tên đăng nhập (Username)",
            hint_text="Viết liền không dấu, vd: quangminh7",
            prefix_icon=ft.Icons.ALTERNATE_EMAIL_ROUNDED,
            dense=True,
            border_radius=10
        )

        txt_reg_name = ft.TextField(
            label="Tên của em / Biệt danh",
            hint_text="Ví dụ: Quang Minh, Thùy Trang...",
            prefix_icon=ft.Icons.BADGE_ROUNDED,
            dense=True,
            border_radius=10
        )

        txt_reg_class = ft.TextField(
            label="Lớp & Trường (Tùy chọn)",
            hint_text="Ví dụ: Lớp 7D • THCS Chu Văn An",
            prefix_icon=ft.Icons.SCHOOL_ROUNDED,
            dense=True,
            border_radius=10
        )

        # Thanh đo độ mạnh mật khẩu (Password Strength Bar)
        strength_bar = ft.ProgressBar(value=0.0, color=ft.Colors.GREY_400, bgcolor=ft.Colors.GREY_200, height=5)
        strength_label = ft.Text("Độ mạnh: Chưa nhập", size=10, color=ft.Colors.GREY_600)
        strength_tip = ft.Text("Mật khẩu nên từ 4-6 ký tự dễ nhớ", size=10, italic=True, color=ft.Colors.GREY_500)

        def on_pass_change(e):
            val = e.control.value or ""
            eval_res = evaluate_password_strength(val)
            strength_bar.value = eval_res["percent"]
            strength_bar.color = eval_res["color"]
            strength_label.value = f"Độ mạnh: {eval_res['label']}"
            strength_label.color = eval_res["color"]
            strength_tip.value = eval_res["tips"]
            self.page.update()

        txt_reg_pass = ft.TextField(
            label="Mật khẩu bảo vệ",
            hint_text="Nhập mật khẩu của em",
            prefix_icon=ft.Icons.LOCK_ROUNDED,
            password=True,
            can_reveal_password=True,
            dense=True,
            border_radius=10,
            on_change=on_pass_change
        )

        # Xác nhận mật khẩu
        match_feedback_text = ft.Text("", size=10)

        def on_confirm_change(e):
            p1 = txt_reg_pass.value or ""
            p2 = e.control.value or ""
            if not p2:
                match_feedback_text.value = ""
            elif p1 == p2:
                match_feedback_text.value = "✓ Mật khẩu hoàn toàn trùng khớp!"
                match_feedback_text.color = ft.Colors.GREEN_700
            else:
                match_feedback_text.value = "✗ Mật khẩu chưa khớp nhau!"
                match_feedback_text.color = ft.Colors.RED_700
            self.page.update()

        txt_reg_confirm = ft.TextField(
            label="Nhập lại mật khẩu",
            hint_text="Xác nhận lại mật khẩu",
            prefix_icon=ft.Icons.LOCK_RESET_ROUNDED,
            password=True,
            can_reveal_password=True,
            dense=True,
            border_radius=10,
            on_change=on_confirm_change
        )

        # Câu hỏi bảo mật & Câu trả lời (Để khôi phục mật khẩu khi quên)
        dd_security_q = ft.Dropdown(
            label="Câu hỏi bảo mật (Để tự lấy lại mật khẩu khi quên)",
            options=[ft.dropdown.Option(q) for q in SECURITY_QUESTIONS],
            value=SECURITY_QUESTIONS[0],
            dense=True,
            border_radius=10
        )

        txt_security_ans = ft.TextField(
            label="Câu trả lời bảo mật của em",
            hint_text="Ví dụ: vat ly, con meo mimi, newton...",
            prefix_icon=ft.Icons.KEY_ROUNDED,
            dense=True,
            border_radius=10
        )

        # Bộ chọn Avatar
        self.avatar_chips.clear()
        avatar_row = ft.Row(spacing=6, wrap=True)

        def make_avatar_click(emoji: str):
            def handler(_):
                self.selected_avatar = emoji
                for item in self.avatar_chips:
                    is_cur = (item.data == emoji)
                    item.bgcolor = ft.Colors.GREEN_100 if is_cur else ft.Colors.GREY_100
                    item.border = ft.Border.all(2 if is_cur else 1, ft.Colors.GREEN_700 if is_cur else ft.Colors.GREY_300)
                self.page.update()
            return handler

        for av in AVATAR_OPTIONS:
            emoji = av["emoji"]
            is_cur = (emoji == self.selected_avatar)
            chip = ft.Container(
                content=ft.Text(emoji, size=20),
                width=38,
                height=38,
                border_radius=19,
                bgcolor=ft.Colors.GREEN_100 if is_cur else ft.Colors.GREY_100,
                border=ft.Border.all(2 if is_cur else 1, ft.Colors.GREEN_700 if is_cur else ft.Colors.GREY_300),
                alignment=ft.Alignment.CENTER,
                tooltip=av["label"],
                data=emoji,
                on_click=make_avatar_click(emoji),
                ink=True
            )
            self.avatar_chips.append(chip)
            avatar_row.controls.append(chip)

        chk_terms = ft.Checkbox(
            label="Em cam kết tự tư duy và kiên trì rèn luyện cùng Socrates Nhí 💡",
            value=True,
            active_color=ft.Colors.GREEN_700
        )

        reg_msg_box = ft.Container(visible=False)

        def do_register(_):
            uname = (txt_reg_username.value or "").strip()
            dname = (txt_reg_name.value or "").strip()
            cname = (txt_reg_class.value or "").strip()
            upass = (txt_reg_pass.value or "").strip()
            uconf = (txt_reg_confirm.value or "").strip()
            sec_q = dd_security_q.value or SECURITY_QUESTIONS[0]
            sec_ans = (txt_security_ans.value or "").strip()

            if upass != uconf:
                reg_msg_box.visible = True
                reg_msg_box.bgcolor = ft.Colors.RED_50
                reg_msg_box.border = ft.Border.all(1, ft.Colors.RED_300)
                reg_msg_box.content = ft.Row([
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=ft.Colors.RED_700, size=16),
                    ft.Text("Mật khẩu xác nhận không trùng khớp!", size=12, color=ft.Colors.RED_900, weight=ft.FontWeight.W_500, expand=True)
                ], spacing=6)
                self.page.update()
                return

            success, new_user, message = AuthService.register_account(
                username=uname,
                raw_password=upass,
                display_name=dname,
                grade_class=cname,
                avatar=self.selected_avatar,
                security_question=sec_q,
                security_answer=sec_ans,
                remember_me=False
            )

            if success and new_user:
                reg_msg_box.visible = True
                reg_msg_box.bgcolor = ft.Colors.GREEN_50
                reg_msg_box.border = ft.Border.all(1, ft.Colors.GREEN_300)
                reg_msg_box.content = ft.Row([
                    ft.Icon(ft.Icons.CELEBRATION_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                    ft.Text(message, size=12, color=ft.Colors.GREEN_900, weight=ft.FontWeight.W_500, expand=True)
                ], spacing=6)
                self.page.update()
                # Hiển thị Hộp thoại hỏi người dùng có muốn LƯU tài khoản trên máy không
                self._show_ask_save_account_dialog(new_user)
            else:
                reg_msg_box.visible = True
                reg_msg_box.bgcolor = ft.Colors.RED_50
                reg_msg_box.border = ft.Border.all(1, ft.Colors.RED_300)
                reg_msg_box.content = ft.Row([
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=ft.Colors.RED_700, size=16),
                    ft.Text(message, size=12, color=ft.Colors.RED_900, weight=ft.FontWeight.W_500, expand=True)
                ], spacing=6)
                self.page.update()

        btn_reg_submit = ft.FilledButton(
            "TẠO TÀI KHOẢN & VÀO HỌC NGAY ✨",
            icon=ft.Icons.PERSON_ADD_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
                padding=ft.Padding(20, 14, 20, 14),
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            width=540,
            on_click=do_register
        )

        link_to_login = ft.Row([
            ft.Text("Đã có tài khoản rồi?", size=12, color=ft.Colors.GREY_600),
            ft.TextButton(
                "Quay lại Đăng nhập 👉",
                style=ft.ButtonStyle(color=ft.Colors.GREEN_900),
                on_click=lambda _: self._switch_to_mode("login")
            )
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)

        return ft.Column([
            ft.Text("Đăng ký tài khoản học sinh nhanh (kích hoạt tức thì, lưu trên máy trạm):", size=12, color=ft.Colors.GREY_700),
            ft.Row([txt_reg_username, txt_reg_name], spacing=8),
            txt_reg_class,
            ft.Row([txt_reg_pass, txt_reg_confirm], spacing=8),
            ft.Column([
                ft.Row([strength_label, strength_tip], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                strength_bar,
                match_feedback_text
            ], spacing=2),
            dd_security_q,
            txt_security_ans,
            ft.Column([
                ft.Text("Chọn biểu tượng đại diện (Avatar) của em:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                avatar_row
            ], spacing=4),
            chk_terms,
            reg_msg_box,
            btn_reg_submit,
            link_to_login
        ], spacing=9)

    def _show_ask_save_account_dialog(self, new_user: UserAccount):
        """Hộp thoại hỏi người dùng có muốn LƯU tài khoản trên thiết bị này không sau khi tạo tài khoản."""
        def on_save_confirm(_):
            self._safe_close_dialog(dialog)
            AuthService.set_current_user(new_user, remember_me=True)
            self.remembered_user = new_user
            self.show_saved_account = True
            self.on_login_success(new_user)

        def on_skip_save(_):
            self._safe_close_dialog(dialog)
            AuthService.set_current_user(new_user, remember_me=False)
            self.remembered_user = None
            self.show_saved_account = False
            self.on_login_success(new_user)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Text(new_user.avatar, size=24),
                ft.Text("LƯU TÀI KHOẢN TRÊN THIẾT BỊ NÀY? 💾", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"🎉 Chúc mừng em {new_user.display_name} đã tạo tài khoản thành công!", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                    ft.Container(height=4),
                    ft.Text("Em có muốn LƯU tài khoản này trên máy tính để lần sau mở lên là tự động vào học tiếp không?", size=12, color=ft.Colors.GREY_800),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=15, color=ft.Colors.GREEN_700),
                                ft.Text("Nếu chọn LƯU: Lần sau chỉ cần bấm 'Vào Học Tiếp' là vào học ngay.", size=11, color=ft.Colors.GREY_700)
                            ], spacing=6),
                            ft.Row([
                                ft.Icon(ft.Icons.SWITCH_ACCOUNT_ROUNDED, size=15, color=ft.Colors.INDIGO_700),
                                ft.Text("Em vẫn có thể đổi sang tài khoản khác bất kỳ lúc nào!", size=11, color=ft.Colors.GREY_700)
                            ], spacing=6),
                        ], spacing=4),
                        bgcolor=ft.Colors.INDIGO_50,
                        padding=10,
                        border_radius=8,
                        border=ft.Border.all(1, ft.Colors.INDIGO_200)
                    )
                ], spacing=8),
                width=460,
                padding=6
            ),
            actions=[
                ft.OutlinedButton(
                    "Không lưu, chỉ dùng phiên này ⏳",
                    on_click=on_skip_save,
                    style=ft.ButtonStyle(color=ft.Colors.GREY_700)
                ),
                ft.FilledButton(
                    "LƯU TÀI KHOẢN NÀY 💾",
                    icon=ft.Icons.SAVE_ROUNDED,
                    on_click=on_save_confirm,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self._safe_open_dialog(dialog)

    # -------------------------------------------------------------------------
    # FORM 3: QUÊN MẬT KHẨU / KHÔI PHỤC (FORGOT PASSWORD FORM)
    # -------------------------------------------------------------------------
    def _build_forgot_password_form(self) -> ft.Control:
        """Quy trình khôi phục mật khẩu thông qua câu hỏi bảo mật chuẩn web."""
        txt_find_user = ft.TextField(
            label="Nhập Tên tài khoản của em",
            hint_text="Ví dụ: minhtriet, baonhat...",
            prefix_icon=ft.Icons.PERSON_SEARCH_ROUNDED,
            dense=True,
            border_radius=10,
            value=self.remembered_user.username if self.remembered_user else ""
        )

        question_display = ft.Text("Câu hỏi bảo mật: (Vui lòng nhập tên tài khoản bên trên)", size=12, italic=True, color=ft.Colors.GREY_600)
        txt_answer = ft.TextField(
            label="Câu trả lời bảo mật của em",
            hint_text="Nhập câu trả lời bảo mật đã đăng ký",
            prefix_icon=ft.Icons.KEY_ROUNDED,
            dense=True,
            border_radius=10
        )

        txt_new_pass = ft.TextField(
            label="Mật khẩu mới",
            hint_text="Nhập mật khẩu mới",
            prefix_icon=ft.Icons.LOCK_ROUNDED,
            password=True,
            can_reveal_password=True,
            dense=True,
            border_radius=10
        )

        txt_new_confirm = ft.TextField(
            label="Nhập lại mật khẩu mới",
            hint_text="Xác nhận lại mật khẩu mới",
            prefix_icon=ft.Icons.LOCK_RESET_ROUNDED,
            password=True,
            can_reveal_password=True,
            dense=True,
            border_radius=10
        )

        forgot_msg_box = ft.Container(visible=False)

        def on_find_user(_):
            uname = (txt_find_user.value or "").strip()
            ok, q_text, err = AuthService.get_security_question(uname)
            if ok:
                question_display.value = f"❓ Câu hỏi bảo mật của em: {q_text}"
                question_display.color = ft.Colors.INDIGO_900
                question_display.weight = ft.FontWeight.BOLD
                forgot_msg_box.visible = False
            else:
                question_display.value = f"❌ {err}"
                question_display.color = ft.Colors.RED_700
                question_display.weight = ft.FontWeight.NORMAL
            self.page.update()

        def do_reset(_):
            uname = (txt_find_user.value or "").strip()
            ans = (txt_answer.value or "").strip()
            p1 = (txt_new_pass.value or "").strip()
            p2 = (txt_new_confirm.value or "").strip()

            if not uname:
                show_msg("Vui lòng nhập tên tài khoản!", False)
                return
            if not ans:
                show_msg("Vui lòng nhập câu trả lời bảo mật!", False)
                return
            if len(p1) < 3:
                show_msg("Mật khẩu mới phải có ít nhất 3 ký tự!", False)
                return
            if p1 != p2:
                show_msg("Mật khẩu xác nhận không trùng khớp!", False)
                return

            ok, msg = AuthService.reset_password_with_question(uname, ans, p1)
            show_msg(msg, ok)
            if ok:
                # Tự động đăng nhập vào tài khoản sau khi khôi phục thành công
                success, user, _ = AuthService.authenticate(uname, p1, remember_me=True)
                if success and user:
                    self.on_login_success(user)

        def show_msg(text: str, is_ok: bool):
            forgot_msg_box.visible = True
            forgot_msg_box.bgcolor = ft.Colors.GREEN_50 if is_ok else ft.Colors.RED_50
            forgot_msg_box.border = ft.Border.all(1, ft.Colors.GREEN_300 if is_ok else ft.Colors.RED_300)
            forgot_msg_box.content = ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED if is_ok else ft.Icons.ERROR_OUTLINE_ROUNDED, color=ft.Colors.GREEN_700 if is_ok else ft.Colors.RED_700, size=16),
                ft.Text(text, size=12, color=ft.Colors.GREEN_900 if is_ok else ft.Colors.RED_900, weight=ft.FontWeight.W_500, expand=True)
            ], spacing=6)
            self.page.update()

        btn_find = ft.FilledButton("Tìm Tài Khoản 🔍", on_click=on_find_user, style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE))
        btn_confirm_reset = ft.FilledButton(
            "ĐẶT LẠI MẬT KHẨU & ĐĂNG NHẬP 🔑",
            icon=ft.Icons.KEY_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, padding=ft.Padding(20, 14, 20, 14)),
            width=540,
            on_click=do_reset
        )

        return ft.Column([
            ft.Text("Khôi phục mật khẩu qua câu hỏi bảo mật:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
            ft.Row([txt_find_user, btn_find], spacing=8),
            question_display,
            txt_answer,
            ft.Row([txt_new_pass, txt_new_confirm], spacing=8),
            forgot_msg_box,
            btn_confirm_reset,
            ft.Row([
                ft.TextButton("Quay lại màn hình Đăng nhập 👉", on_click=lambda _: self._switch_to_mode("login"), style=ft.ButtonStyle(color=ft.Colors.INDIGO_800))
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=10)

    # -------------------------------------------------------------------------
    # FORM 4: CHẾ ĐỘ KHÁCH TRẢI NGHIỆM (GUEST MODE)
    # -------------------------------------------------------------------------
    def _build_guest_mode_form(self) -> ft.Control:
        """Chế độ Khách Trải Nghiệm Ẩn Danh dành cho Giám khảo & Khách."""
        card_desc = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.VERIFIED_USER_ROUNDED, color=ft.Colors.AMBER_800, size=24),
                    ft.Text("Chế Độ Trải Nghiệm Khách Ẩn Danh (COPPA Safe)", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
                ], spacing=8),
                ft.Text(
                    "Dành riêng cho Ban Giám Khảo, Thầy Cô và Khách Trải Nghiệm muốn dùng thử ngay lập tức mà không cần tạo tài khoản hay ghi nhớ mật khẩu.",
                    size=12,
                    color=ft.Colors.GREY_800
                ),
                ft.Container(height=4),
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                    ft.Text("Không cần email, mật khẩu hay thông tin cá nhân PII.", size=11, color=ft.Colors.GREY_700)
                ], spacing=6),
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                    ft.Text("Trải nghiệm đầy đủ 5 Trạm học tập KHTN 7 và Khiên chống lộ đáp án.", size=11, color=ft.Colors.GREY_700)
                ], spacing=6),
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                    ft.Text("Dữ liệu tự động làm mới khi kết thúc phiên trải nghiệm.", size=11, color=ft.Colors.GREY_700)
                ], spacing=6),
            ], spacing=6),
            bgcolor=ft.Colors.AMBER_50,
            padding=16,
            border_radius=12,
            border=ft.Border.all(1.5, ft.Colors.AMBER_300)
        )

        def do_guest_enter(_):
            guest_user = AuthService.logout_to_guest()
            self.on_login_success(guest_user)

        btn_guest = ft.FilledButton(
            "VÀO TRẢI NGHIỆM NGAY VỚI TƯ CÁCH KHÁCH 👤",
            icon=ft.Icons.ROCKET_LAUNCH_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.AMBER_800,
                color=ft.Colors.WHITE,
                padding=ft.Padding(20, 14, 20, 14),
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            width=540,
            on_click=do_guest_enter
        )

        return ft.Column([
            card_desc,
            ft.Container(height=6),
            btn_guest,
            ft.Row([
                ft.TextButton(
                    "Hoặc đăng nhập bằng tài khoản học sinh 👉",
                    style=ft.ButtonStyle(color=ft.Colors.INDIGO_800),
                    on_click=lambda _: self._switch_to_mode("login")
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=10)

    # -------------------------------------------------------------------------
    # KHU VỰC ĐĂNG NHẬP NHANH 1-CHẠM (FAST SAVED PROFILES SECTION)
    # -------------------------------------------------------------------------
    def _build_quick_login_section(self) -> ft.Control:
        """Khu vực Đăng nhập Nhanh 1-Chạm dạng Profile Cards hiện đại."""
        all_users = AuthService.load_all_users()
        demo_usernames = ["baonhat", "minhtriet", "baoan", "huyhoang", "guest"]

        demo_chips = []
        for username in demo_usernames:
            user = all_users.get(username)
            if not user:
                continue

            def make_quick_handler(u=user):
                def _handle_click(_):
                    if hasattr(self, "txt_login_username") and self.txt_login_username:
                        self.txt_login_username.value = u.username
                    if hasattr(self, "txt_login_password") and self.txt_login_password:
                        self.txt_login_password.value = "123"
                    try:
                        self.page.update()
                    except Exception:
                        pass
                    self._do_quick_login(u.username)
                return _handle_click

            role_tag = "Tác giả" if user.username == "baonhat" else ("Vật lý" if "Vật" in user.grade_class else ("Sinh học" if "Sinh" in user.grade_class else ("Hóa học" if "Hóa" in user.grade_class else "Khách")))
            chip = ft.Container(
                content=ft.Row([
                    ft.Text(user.avatar, size=18),
                    ft.Column([
                        ft.Row([
                            ft.Text(user.display_name, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                            ft.Container(
                                content=ft.Text(role_tag, size=8, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800),
                                bgcolor=ft.Colors.INDIGO_100,
                                padding=ft.Padding(4, 1, 4, 1),
                                border_radius=4
                            )
                        ], spacing=4),
                        ft.Text(user.grade_class.split("•")[0].strip(), size=9, color=ft.Colors.GREY_600)
                    ], spacing=1)
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.INDIGO_50,
                padding=ft.Padding(10, 6, 12, 6),
                border_radius=10,
                border=ft.Border.all(1, ft.Colors.INDIGO_200),
                tooltip=f"Bấm để đăng nhập nhanh với tài khoản {user.display_name}",
                on_click=make_quick_handler(),
                ink=True
            )
            demo_chips.append(chip)

        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.FLASH_ON_ROUNDED, size=16, color=ft.Colors.AMBER_800),
                ft.Text("⚡ Đăng nhập Nhanh 1-Chạm (Học sinh mẫu & Ban Giám khảo chấm thi):", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800)
            ], spacing=4),
            ft.Row(demo_chips, wrap=True, spacing=8)
        ], spacing=6)

    def _do_quick_login(self, username: str):
        """Xử lý đăng nhập 1-chạm."""
        success, user, _ = AuthService.quick_login(username, remember_me=True)
        if success and user:
            self.on_login_success(user)


# =============================================================================
# HỘP THOẠI QUẢN LÝ TÀI KHOẢN & ĐỔI MẬT KHẨU TRONG APP (AUTH MODAL DIALOG)
# =============================================================================
class AuthModalDialog:
    """
    Hộp thoại quản lý tài khoản & đổi mật khẩu an toàn khi đang ở trong phiên học.
    100% tương thích Flet 1.0.1+.
    """
    def __init__(self, page: ft.Page, on_user_changed: Callable[[UserAccount], None], on_logout: Optional[Callable[[], None]] = None):
        self.page = page
        self.on_user_changed = on_user_changed
        self.on_logout = on_logout or (lambda: None)
        self.dialog: Optional[ft.AlertDialog] = None
        self.current_user = AuthService.get_current_user()
        self.view_tab = "profile"  # "profile" hoặc "change_password"

    def show(self):
        """Hiển thị hộp thoại tài khoản."""
        self.current_user = AuthService.get_current_user()
        self.view_tab = "profile"
        self._render_dialog()

    def _render_dialog(self):
        stats = AuthService.get_user_notebook_stats(self.current_user.username)
        all_users = AuthService.load_all_users()

        # Thẻ thông tin học sinh hiện tại
        profile_card = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(self.current_user.avatar, size=32),
                    width=54,
                    height=54,
                    border_radius=27,
                    bgcolor=ft.Colors.INDIGO_50,
                    alignment=ft.Alignment.CENTER,
                    border=ft.Border.all(2, ft.Colors.INDIGO_300)
                ),
                ft.Column([
                    ft.Row([
                        ft.Text(self.current_user.display_name, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ft.Container(
                            content=ft.Text("ĐANG ĐĂNG NHẬP", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
                            bgcolor=ft.Colors.GREEN_100,
                            padding=ft.Padding(6, 2, 6, 2),
                            border_radius=6
                        )
                    ], spacing=6),
                    ft.Text(f"{self.current_user.grade_class} • @{self.current_user.username}", size=11, color=ft.Colors.GREY_700),
                    ft.Row([
                        ft.Icon(ft.Icons.BOOKMARK_ROUNDED, size=13, color=ft.Colors.INDIGO_600),
                        ft.Text(f"Đã đúc kết {stats['total_lessons']} bài học trong Sổ tay", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_700)
                    ], spacing=4)
                ], spacing=2, expand=True)
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(14, 10, 14, 10),
            border_radius=12,
            border=ft.Border.all(1.5, ft.Colors.INDIGO_200)
        )

        # Tab view: Profile list or Change password
        body_container = ft.Container(expand=True)

        if self.view_tab == "profile":
            switch_cards = []
            for username, user in all_users.items():
                if user.username == self.current_user.username:
                    continue

                def make_handler(u=user):
                    return lambda _: self._do_switch(u.username)

                u_stats = AuthService.get_user_notebook_stats(user.username)
                card = ft.Container(
                    content=ft.Row([
                        ft.Text(user.avatar, size=22),
                        ft.Column([
                            ft.Text(user.display_name, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                            ft.Text(f"{user.grade_class.split('•')[0].strip()} • 📓 {u_stats['total_lessons']} bài", size=10, color=ft.Colors.GREY_600)
                        ], spacing=1, expand=True),
                        ft.FilledButton(
                            "Đổi sang em này",
                            style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE),
                            on_click=make_handler()
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.GREY_50,
                    padding=ft.Padding(10, 8, 10, 8),
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.GREY_200)
                )
                switch_cards.append(card)

            btn_go_change_pass = ft.OutlinedButton(
                "Đổi Mật Khẩu Tài Khoản 🔑",
                icon=ft.Icons.PASSWORD_ROUNDED,
                style=ft.ButtonStyle(color=ft.Colors.INDIGO_700),
                on_click=lambda _: self._switch_tab("change_password")
            )

            body_container.content = ft.Column([
                ft.Row([
                    ft.Text("⚡ Đổi nhanh sang tài khoản học sinh khác:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                    btn_go_change_pass
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Column(switch_cards, spacing=6, scroll=ft.ScrollMode.AUTO)
            ], spacing=10)

        else:
            # Giao diện Đổi Mật Khẩu
            txt_old_pass = ft.TextField(label="Mật khẩu hiện tại", password=True, can_reveal_password=True, dense=True, border_radius=10)
            txt_new_pass = ft.TextField(label="Mật khẩu mới", password=True, can_reveal_password=True, dense=True, border_radius=10)
            txt_new_conf = ft.TextField(label="Nhập lại mật khẩu mới", password=True, can_reveal_password=True, dense=True, border_radius=10)
            chg_msg = ft.Container(visible=False)

            def do_save_new_pass(_):
                old_p = (txt_old_pass.value or "").strip()
                new_p = (txt_new_pass.value or "").strip()
                conf_p = (txt_new_conf.value or "").strip()

                if new_p != conf_p:
                    chg_msg.visible = True
                    chg_msg.bgcolor = ft.Colors.RED_50
                    chg_msg.content = ft.Text("Mật khẩu xác nhận không khớp!", color=ft.Colors.RED_900, size=11)
                    self.page.update()
                    return

                ok, msg = AuthService.change_password(self.current_user.username, old_p, new_p)
                chg_msg.visible = True
                chg_msg.bgcolor = ft.Colors.GREEN_50 if ok else ft.Colors.RED_50
                chg_msg.content = ft.Text(msg, color=ft.Colors.GREEN_900 if ok else ft.Colors.RED_900, size=11)
                self.page.update()

            body_container.content = ft.Column([
                ft.Row([
                    ft.Text("Đổi Mật Khẩu Cho Tài Khoản:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.TextButton("Quay lại danh sách tài khoản 👈", on_click=lambda _: self._switch_tab("profile"))
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                txt_old_pass,
                txt_new_pass,
                txt_new_conf,
                chg_msg,
                ft.FilledButton(
                    "Lưu Mật Khẩu Mới 💾",
                    icon=ft.Icons.SAVE_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                    on_click=do_save_new_pass
                )
            ], spacing=8)

        content_box = ft.Container(
            content=ft.Column([
                profile_card,
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                body_container
            ], spacing=10),
            width=540,
            height=400,
            padding=ft.Padding(4, 4, 4, 4)
        )

        from app_tich_hop_socrates.dashboard_view import safe_open_dialog, safe_close_dialog

        def close_dialog(_=None):
            safe_close_dialog(self.page, self.dialog)

        def do_logout_click(_):
            close_dialog()
            self.on_logout()

        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED, color=ft.Colors.INDIGO_700, size=24),
                ft.Text("Quản Lý Tài Khoản Học Sinh Socrates Nhí", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=content_box,
            actions=[
                ft.OutlinedButton(
                    "Đăng xuất (Về màn hình Đăng nhập)",
                    icon=ft.Icons.LOGOUT_ROUNDED,
                    style=ft.ButtonStyle(color=ft.Colors.RED_600),
                    on_click=do_logout_click
                ),
                ft.FilledButton(
                    "Đóng",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_700, color=ft.Colors.WHITE),
                    on_click=close_dialog
                )
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        safe_open_dialog(self.page, self.dialog)

    def _switch_tab(self, new_tab: str):
        self.view_tab = new_tab
        self._render_dialog()

    def _do_switch(self, username: str):
        """Xử lý đổi tài khoản trong hộp thoại."""
        from app_tich_hop_socrates.dashboard_view import safe_close_dialog
        safe_close_dialog(self.page, self.dialog)

        success, user, _ = AuthService.quick_login(username, remember_me=True)
        if success and user:
            self.on_user_changed(user)


# Định nghĩa alias tương thích ngược
AuthDialogView = AuthModalDialog
