"""
Module: auth_view.py
Chức năng: Giao diện Đăng nhập / Tạo tài khoản / Đổi tài khoản cho Học sinh THCS
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Lưu ý kỹ thuật:
- Hoàn toàn KHÔNG sử dụng ft.Tabs / ft.Tab (đã thay đổi API trong Flet 1.0.1 gây lỗi unexpected keyword argument 'text').
- Sử dụng Custom Segmented Button & Container Switches hoàn toàn tương thích và đẹp mắt.
- Mới mở app: Hiển thị Màn hình Đăng nhập (Login Screen).
- Nếu chưa có tài khoản: Cho phép Tạo tài khoản mới tức thì (tạm thời không cần gửi email).
- Hỗ trợ Đăng nhập Nhanh 1-Chạm dành cho Giám khảo & Thuyết trình viên.
"""

from typing import Callable, Optional, List, Dict, Any
import flet as ft

from app_tich_hop_socrates.auth_service import AuthService, UserAccount

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


class LoginScreenView:
    """
    Màn hình Đăng Nhập & Chào Mừng chính khi mở ứng dụng Socrates Nhí.
    """
    def __init__(self, page: ft.Page, on_login_success: Callable[[UserAccount], None]):
        self.page = page
        self.on_login_success = on_login_success
        self.mode = "login"  # "login" hoặc "register"
        self.selected_avatar = "💡"
        self.avatar_chips: List[ft.Container] = []

    def build(self) -> ft.Control:
        """Xây dựng toàn bộ giao diện màn hình Đăng nhập / Tạo tài khoản."""
        # Logo & Thương hiệu ứng dụng
        brand_header = ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.WHITE, size=32),
                    bgcolor=ft.Colors.AMBER_500,
                    width=56,
                    height=56,
                    border_radius=28,
                    alignment=ft.Alignment.CENTER,
                    shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.4, ft.Colors.AMBER_500), offset=ft.Offset(0, 3))
                ),
                ft.Column([
                    ft.Text("SOCRATES NHÍ 💡", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Text("Trợ lý AI gợi mở tư duy KHTN THCS • Cuộc thi Sáng tạo trẻ Quốc gia AI 2026", size=12, color=ft.Colors.GREY_700)
                ], spacing=2)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=14),
            ft.Text(
                "✨ Hỏi đúng cách • Nghĩ sâu sắc • Tự đúc kết tri thức khoa học ✨",
                size=13,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.INDIGO_700,
                text_align=ft.TextAlign.CENTER
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        # Container chứa Form động (Đăng nhập hoặc Tạo tài khoản)
        self.form_container = ft.Container(expand=True)

        # Thanh chuyển đổi chế độ [Đăng Nhập] | [Tạo Tài Khoản Mới]
        self.btn_tab_login = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LOGIN_ROUNDED, size=16, color=ft.Colors.INDIGO_900),
                ft.Text("Đăng Nhập", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(16, 10, 16, 10),
            border_radius=10,
            border=ft.Border.all(2, ft.Colors.INDIGO_600),
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
            expand=True,
            on_click=lambda _: self._switch_mode("login"),
            ink=True
        )

        self.btn_tab_register = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PERSON_ADD_ROUNDED, size=16, color=ft.Colors.GREY_600),
                ft.Text("Tạo Tài Khoản Mới", size=13, weight=ft.FontWeight.NORMAL, color=ft.Colors.GREY_700)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            bgcolor=ft.Colors.GREY_100,
            padding=ft.Padding(16, 10, 16, 10),
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            expand=True,
            on_click=lambda _: self._switch_mode("register"),
            ink=True
        )

        switch_bar = ft.Row([self.btn_tab_login, self.btn_tab_register], spacing=10)

        # Render form ban đầu (mặc định là Login)
        self._render_current_form()

        # Thẻ Đăng nhập Nhanh 1-Chạm (Dành cho Giám khảo / Khách trải nghiệm)
        quick_login_section = self._build_quick_login_section()

        # Khung thẻ đăng nhập chính giữa màn hình
        main_card = ft.Container(
            content=ft.Column([
                switch_bar,
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                self.form_container,
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                quick_login_section
            ], spacing=12),
            width=580,
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(24, 20, 24, 20),
            border_radius=18,
            border=ft.Border.all(1.5, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 6))
        )

        return ft.Container(
            content=ft.Column([
                brand_header,
                ft.Container(height=8),
                main_card
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12, scroll=ft.ScrollMode.AUTO),
            alignment=ft.Alignment.TOP_CENTER,
            padding=ft.Padding(20, 20, 20, 30),
            expand=True,
            bgcolor="#F8FAFC"
        )

    def _switch_mode(self, new_mode: str):
        """Chuyển đổi giữa chế độ Đăng nhập và Tạo tài khoản."""
        self.mode = new_mode
        if new_mode == "login":
            self.btn_tab_login.bgcolor = ft.Colors.WHITE
            self.btn_tab_login.border = ft.Border.all(2, ft.Colors.INDIGO_600)
            self.btn_tab_login.shadow = ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2))
            self.btn_tab_login.content.controls[0].color = ft.Colors.INDIGO_900
            self.btn_tab_login.content.controls[1].color = ft.Colors.INDIGO_900
            self.btn_tab_login.content.controls[1].weight = ft.FontWeight.BOLD

            self.btn_tab_register.bgcolor = ft.Colors.GREY_100
            self.btn_tab_register.border = ft.Border.all(1, ft.Colors.GREY_300)
            self.btn_tab_register.shadow = None
            self.btn_tab_register.content.controls[0].color = ft.Colors.GREY_600
            self.btn_tab_register.content.controls[1].color = ft.Colors.GREY_700
            self.btn_tab_register.content.controls[1].weight = ft.FontWeight.NORMAL
        else:
            self.btn_tab_register.bgcolor = ft.Colors.WHITE
            self.btn_tab_register.border = ft.Border.all(2, ft.Colors.GREEN_600)
            self.btn_tab_register.shadow = ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2))
            self.btn_tab_register.content.controls[0].color = ft.Colors.GREEN_900
            self.btn_tab_register.content.controls[1].color = ft.Colors.GREEN_900
            self.btn_tab_register.content.controls[1].weight = ft.FontWeight.BOLD

            self.btn_tab_login.bgcolor = ft.Colors.GREY_100
            self.btn_tab_login.border = ft.Border.all(1, ft.Colors.GREY_300)
            self.btn_tab_login.shadow = None
            self.btn_tab_login.content.controls[0].color = ft.Colors.GREY_600
            self.btn_tab_login.content.controls[1].color = ft.Colors.GREY_700
            self.btn_tab_login.content.controls[1].weight = ft.FontWeight.NORMAL

        self._render_current_form()
        self.page.update()

    def _render_current_form(self):
        """Hiển thị nội dung form tương ứng."""
        if self.mode == "login":
            self.form_container.content = self._build_login_form()
        else:
            self.form_container.content = self._build_register_form()

    def _build_login_form(self) -> ft.Control:
        """Form Đăng nhập tài khoản."""
        txt_username = ft.TextField(
            label="Tên đăng nhập (Username)",
            hint_text="Nhập tên tài khoản của em (vd: minhtriet, baoan...)",
            prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            value="minhtriet",
            dense=True,
            border_radius=10
        )

        txt_password = ft.TextField(
            label="Mật khẩu",
            hint_text="Nhập mật khẩu (Mẫu: 123)",
            prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
            password=True,
            can_reveal_password=True,
            value="123",
            dense=True,
            border_radius=10
        )

        msg_box = ft.Container(visible=False)

        def do_login(_):
            uname = (txt_username.value or "").strip()
            upass = (txt_password.value or "").strip()
            success, user, message = AuthService.authenticate(uname, upass)

            if success and user:
                msg_box.visible = True
                msg_box.bgcolor = ft.Colors.GREEN_50
                msg_box.border = ft.Border.all(1, ft.Colors.GREEN_300)
                msg_box.content = ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                    ft.Text(message, size=12, color=ft.Colors.GREEN_900, weight=ft.FontWeight.W_500)
                ], spacing=6)
                self.page.update()
                # Kích hoạt callback đăng nhập thành công vào app chính
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
                "Tạo tài khoản mới tại đây 👉",
                style=ft.ButtonStyle(color=ft.Colors.INDIGO_800),
                on_click=lambda _: self._switch_mode("register")
            )
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)

        return ft.Column([
            ft.Text("Chào mừng em đến với Socrates Nhí! Vui lòng đăng nhập:", size=12, color=ft.Colors.GREY_700),
            txt_username,
            txt_password,
            msg_box,
            btn_submit,
            link_to_register,
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=14, color=ft.Colors.INDIGO_800),
                    ft.Text("Tài khoản mẫu: minhtriet / Mật khẩu: 123 (hoặc chọn 1-chạm bên dưới)", size=11, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                bgcolor=ft.Colors.INDIGO_50,
                padding=ft.Padding(10, 6, 10, 6),
                border_radius=8,
                border=ft.Border.all(1, ft.Colors.INDIGO_200)
            )
        ], spacing=10)

    def _build_register_form(self) -> ft.Control:
        """Form Tạo tài khoản học sinh mới (không cần gửi email)."""
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

        txt_reg_pass = ft.TextField(
            label="Mật khẩu bảo vệ",
            hint_text="Nhập mật khẩu dễ nhớ của em",
            prefix_icon=ft.Icons.LOCK_ROUNDED,
            password=True,
            can_reveal_password=True,
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

        reg_msg_box = ft.Container(visible=False)

        def do_register(_):
            uname = (txt_reg_username.value or "").strip()
            dname = (txt_reg_name.value or "").strip()
            cname = (txt_reg_class.value or "").strip()
            upass = (txt_reg_pass.value or "").strip()

            success, new_user, message = AuthService.register_account(
                username=uname,
                raw_password=upass,
                display_name=dname,
                grade_class=cname,
                avatar=self.selected_avatar
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
                # Kích hoạt callback vào app chính
                self.on_login_success(new_user)
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
                on_click=lambda _: self._switch_mode("login")
            )
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)

        return ft.Column([
            ft.Text("Đăng ký tài khoản học sinh nhanh (kích hoạt tức thì, không cần email):", size=12, color=ft.Colors.GREY_700),
            ft.Row([txt_reg_username, txt_reg_name], spacing=8),
            ft.Row([txt_reg_class, txt_reg_pass], spacing=8),
            ft.Column([
                ft.Text("Chọn biểu tượng đại diện của em:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                avatar_row
            ], spacing=4),
            reg_msg_box,
            btn_reg_submit,
            link_to_login
        ], spacing=10)

    def _build_quick_login_section(self) -> ft.Control:
        """Khu vực Đăng nhập Nhanh 1-Chạm cho Giám khảo & Khách."""
        all_users = AuthService.load_all_users()

        demo_chips = []
        for username in ["minhtriet", "baoan", "huyhoang", "guest"]:
            user = all_users.get(username)
            if not user:
                continue

            def make_quick_handler(u=user):
                return lambda _: self._do_quick_login(u.username)

            chip = ft.Container(
                content=ft.Row([
                    ft.Text(user.avatar, size=16),
                    ft.Column([
                        ft.Text(user.display_name, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ft.Text(user.grade_class.split("•")[0].strip(), size=9, color=ft.Colors.GREY_600)
                    ], spacing=0)
                ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.INDIGO_50,
                padding=ft.Padding(10, 6, 12, 6),
                border_radius=10,
                border=ft.Border.all(1, ft.Colors.INDIGO_200),
                tooltip=f"Đăng nhập 1-chạm với tài khoản {user.display_name}",
                on_click=make_quick_handler(),
                ink=True
            )
            demo_chips.append(chip)

        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.FLASH_ON_ROUNDED, size=15, color=ft.Colors.AMBER_800),
                ft.Text("⚡ Đăng nhập Nhanh 1-Chạm (Dành cho Giám khảo & Trải nghiệm):", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800)
            ], spacing=4),
            ft.Row(demo_chips, wrap=True, spacing=8)
        ], spacing=6)

    def _do_quick_login(self, username: str):
        """Xử lý đăng nhập 1-chạm."""
        success, user, _ = AuthService.quick_login(username)
        if success and user:
            self.on_login_success(user)


class AuthModalDialog:
    """
    Hộp thoại quản lý tài khoản khi đang ở trong phiên học (Xem hồ sơ / Đổi tài khoản / Đăng xuất).
    KHÔNG sử dụng ft.Tabs để đảm bảo 100% tương thích Flet 1.0.1+.
    """
    def __init__(self, page: ft.Page, on_user_changed: Callable[[UserAccount], None], on_logout: Optional[Callable[[], None]] = None):
        self.page = page
        self.on_user_changed = on_user_changed
        self.on_logout = on_logout or (lambda: None)
        self.dialog: Optional[ft.AlertDialog] = None
        self.current_user = AuthService.get_current_user()

    def show(self):
        """Hiển thị hộp thoại tài khoản."""
        self.current_user = AuthService.get_current_user()
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

        # Danh sách đổi nhanh sang tài khoản khác
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

        content_box = ft.Container(
            content=ft.Column([
                profile_card,
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                ft.Text("⚡ Đổi nhanh sang tài khoản học sinh khác:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Column(switch_cards, spacing=6, scroll=ft.ScrollMode.AUTO)
            ], spacing=10),
            width=520,
            height=380,
            padding=ft.Padding(4, 4, 4, 4)
        )

        def close_dialog(_=None):
            if hasattr(self.page, "close"):
                self.page.close(self.dialog)
            else:
                self.dialog.open = False
                self.page.update()

        def do_logout_click(_):
            close_dialog()
            self.on_logout()

        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED, color=ft.Colors.INDIGO_700, size=24),
                ft.Text("Tài Khoản Học Sinh Socrates Nhí", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
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

        if hasattr(self.page, "open"):
            self.page.open(self.dialog)
        else:
            self.page.dialog = self.dialog
            self.dialog.open = True
            self.page.update()

    def _do_switch(self, username: str):
        """Xử lý đổi tài khoản trong hộp thoại."""
        if hasattr(self.page, "close"):
            self.page.close(self.dialog)
        else:
            self.dialog.open = False
            self.page.update()

        success, user, _ = AuthService.quick_login(username)
        if success and user:
            self.on_user_changed(user)


# Định nghĩa alias tương thích ngược
AuthDialogView = AuthModalDialog
