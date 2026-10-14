"""
Unit Test: Kiểm thử chức năng Dashboard, Streak, Tiến độ học tập & Quản lý Tài khoản (Đăng nhập/Đăng xuất/Lưu trữ)
"""

import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock

from app_tich_hop_socrates.auth_service import AuthService, UserAccount
from app_tich_hop_socrates.dashboard_view import StudentDashboardModal, safe_open_dialog, safe_close_dialog


class TestDashboardAndAuthService(unittest.TestCase):
    def setUp(self):
        # Sao lưu danh sách user gốc
        self.orig_users = AuthService.load_all_users()

        # Thiết lập user mẫu để kiểm tra
        self.user = UserAccount(
            username="test_user_unit",
            display_name="Nguyễn Văn A",
            grade_class="7A1 • THCS Lê Quý Đôn",
            avatar="🚀",
            password_hash="test_hash",
            streak_count=4,
            max_streak=7,
            study_dates=[
                (date.today() - timedelta(days=3)).strftime("%Y-%m-%d"),
                (date.today() - timedelta(days=2)).strftime("%Y-%m-%d"),
                (date.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
                date.today().strftime("%Y-%m-%d"),
            ],
            physics_count=3,
            chemistry_count=2,
            biology_count=1,
            total_study_minutes=150
        )
        users = dict(self.orig_users)
        users["test_user_unit"] = self.user
        AuthService.save_all_users(users)

    def tearDown(self):
        # Khôi phục danh sách user gốc
        AuthService.save_all_users(self.orig_users)

    def test_streak_calculation(self):
        """Kiểm tra logic tính chuỗi ngày học streak và lịch 7 ngày trong tuần."""
        streak_data = AuthService.get_user_streak("test_user_unit")
        self.assertGreaterEqual(streak_data["streak_count"], 4)
        self.assertEqual(streak_data["max_streak"], 7)
        self.assertEqual(len(streak_data["week_days"]), 7)

        # Kiểm tra ngày hôm nay có được đánh dấu đã học (studied == True)
        today_entry = next((d for d in streak_data["week_days"] if d["is_today"]), None)
        self.assertIsNotNone(today_entry)
        self.assertTrue(today_entry["studied"])

    def test_progress_calculation(self):
        """Kiểm tra logic tiến độ 3 mạch KHTN 7 và huy hiệu danh hiệu."""
        progress = AuthService.get_user_progress("test_user_unit")
        self.assertGreaterEqual(progress["physics_completed"], 3)
        self.assertGreaterEqual(progress["chemistry_completed"], 2)
        self.assertGreaterEqual(progress["biology_completed"], 1)
        self.assertGreaterEqual(progress["total_completed"], 6)
        self.assertEqual(progress["total_target"], 12)
        self.assertGreaterEqual(progress["progress_percent"], 50)

        # Kiểm tra badges
        badges = progress["badges"]
        self.assertGreater(len(badges), 0)
        unlocked_ids = [b["id"] for b in badges if b["unlocked"]]
        self.assertIn("first_step", unlocked_ids)
        self.assertIn("streak_3", unlocked_ids)

    def test_record_study_session(self):
        """Kiểm tra hàm ghi nhận buổi học tự động tăng streak và mạch KHTN."""
        AuthService.record_study_session(
            username="test_user_unit",
            topic="Định luật phản xạ ánh sáng",
            domain="Vật lý",
            minutes=25
        )

        users = AuthService.load_all_users()
        u = users["test_user_unit"]
        self.assertEqual(u.physics_count, 4)
        self.assertEqual(u.total_study_minutes, 175)
        self.assertIn(date.today().strftime("%Y-%m-%d"), u.study_dates)

    def test_safe_open_close_dialog(self):
        """Kiểm tra safe_open_dialog và safe_close_dialog tương thích Flet overlay."""
        class MockPage:
            def __init__(self):
                self.overlay = []
                self.updated = False
            def update(self):
                self.updated = True

        mock_page = MockPage()
        mock_dialog = MagicMock()
        mock_dialog.open = False

        # Mở dialog
        safe_open_dialog(mock_page, mock_dialog)
        self.assertIn(mock_dialog, mock_page.overlay)
        self.assertTrue(mock_dialog.open)
        self.assertTrue(mock_page.updated)

        # Đóng dialog
        safe_close_dialog(mock_page, mock_dialog)
        self.assertFalse(mock_dialog.open)

    def test_dashboard_modal_structure(self):
        """Kiểm tra khởi tạo và hiển thị StudentDashboardModal."""
        class MockPage:
            def __init__(self):
                self.overlay = []
                self.updated = False
            def update(self):
                self.updated = True

        mock_page = MockPage()

        opened_notebook = []
        switched_account = []
        logged_out = []

        modal = StudentDashboardModal(
            page=mock_page,
            current_user=self.user,
            on_open_notebook=lambda: opened_notebook.append(True),
            on_switch_account=lambda: switched_account.append(True),
            on_logout=lambda: logged_out.append(True)
        )

        # Kiểm tra hiển thị dialog
        modal.show()
        self.assertIsNotNone(modal.dialog)
        self.assertIn(modal.dialog, mock_page.overlay)
        self.assertTrue(modal.dialog.open)

    def test_open_notebook_viewer_and_ai_settings_dialogs(self):
        """Kiểm tra gọi mở Sổ tay Tự học (1 tài khoản duy nhất) và Cài đặt AI không bị UnboundLocalError."""
        from app_tich_hop_socrates.main_app import SocratesIntegratedApp

        class MockPage:
            def __init__(self):
                self.overlay = []
                self.controls = []
                self.window = MagicMock()
            def update(self):
                pass
            def add(self, *controls):
                self.controls.extend(controls)

        mock_page = MockPage()
        app = SocratesIntegratedApp(mock_page)

        # 1. Kiểm tra mở Sổ tay Tự học
        app._open_notebook_viewer()
        self.assertGreater(len(mock_page.overlay), 0)
        nb_dialog = mock_page.overlay[-1]
        self.assertTrue(nb_dialog.open)

        # 2. Kiểm tra mở Cài đặt AI không bị lỗi UnboundLocalError
        app._open_ai_settings_dialog()
        ai_dialog = mock_page.overlay[-1]
        self.assertTrue(ai_dialog.open)

    def test_password_strength_and_reset_flow(self):
        """Kiểm tra chức năng tính độ mạnh mật khẩu, đổi mật khẩu và khôi phục mật khẩu chuẩn web."""
        from app_tich_hop_socrates.auth_service import evaluate_password_strength, _hash_pass

        # 1. Đo độ mạnh mật khẩu
        weak = evaluate_password_strength("12")
        self.assertLess(weak["score"], 40)

        medium = evaluate_password_strength("12345")
        self.assertGreaterEqual(medium["score"], 40)

        strong = evaluate_password_strength("Socrates2026!")
        self.assertGreaterEqual(strong["score"], 80)

        # 2. Đổi mật khẩu
        users = AuthService.load_all_users()
        users["test_user_unit"].password_hash = _hash_pass("oldpass123")
        AuthService.save_all_users(users)

        # Thử đổi với mật khẩu cũ sai
        ok, msg = AuthService.change_password("test_user_unit", "wrongpass", "newpass123")
        self.assertFalse(ok)

        # Đổi với mật khẩu cũ đúng
        ok, msg = AuthService.change_password("test_user_unit", "oldpass123", "newpass123")
        self.assertTrue(ok)

        # Xác thực lại với mật khẩu mới
        auth_ok, u, _ = AuthService.authenticate("test_user_unit", "newpass123")
        self.assertTrue(auth_ok)
        self.assertIsNotNone(u)

        # 3. Khôi phục mật khẩu qua câu hỏi bảo mật
        q_ok, question, _ = AuthService.get_security_question("test_user_unit")
        self.assertTrue(q_ok)
        self.assertTrue(len(question) > 0)

        # Đặt câu hỏi và câu trả lời
        users = AuthService.load_all_users()
        users["test_user_unit"].security_question = "Môn học KHTN em yêu thích nhất?"
        users["test_user_unit"].security_answer_hash = _hash_pass("vat ly")
        AuthService.save_all_users(users)

        # Trả lời sai
        reset_ok, _ = AuthService.reset_password_with_question("test_user_unit", "sai_roi", "pass999")
        self.assertFalse(reset_ok)

        # Trả lời đúng
        reset_ok, _ = AuthService.reset_password_with_question("test_user_unit", "vat ly", "pass999")
        self.assertTrue(reset_ok)

        # Kiểm tra đăng nhập với pass mới
        auth_ok2, _, _ = AuthService.authenticate("test_user_unit", "pass999")
        self.assertTrue(auth_ok2)

    def test_login_screen_web_views(self):
        """Kiểm tra LoginScreenView khởi tạo và chuyển đổi mượt mà giữa các chế độ web."""
        from app_tich_hop_socrates.auth_view import LoginScreenView

        class MockPage:
            def __init__(self):
                self.overlay = []
            def update(self):
                pass

        mock_page = MockPage()
        login_success_called = []

        login_view = LoginScreenView(mock_page, on_login_success=lambda u: login_success_called.append(u))
        root_ctrl = login_view.build()
        self.assertIsNotNone(root_ctrl)

        # Kiểm tra chuyển sang register
        login_view._switch_to_mode("register")
        self.assertEqual(login_view.mode, "register")
        self.assertIsNotNone(login_view.form_host.content)

        # Kiểm tra chuyển sang forgot
        login_view._switch_to_mode("forgot")
        self.assertEqual(login_view.mode, "forgot")
        self.assertIsNotNone(login_view.form_host.content)

        # Kiểm tra chuyển sang guest
        login_view._switch_to_mode("guest")
        self.assertEqual(login_view.mode, "guest")
        self.assertIsNotNone(login_view.form_host.content)

        # Kiểm tra chuyển lại login
        login_view._switch_to_mode("login")
        self.assertEqual(login_view.mode, "login")

        # Kiểm tra khởi tạo với vai trò Phụ huynh (initial_role="parent")
        parent_login_view = LoginScreenView(mock_page, on_login_success=lambda u: None, initial_role="parent")
        # Kiểm tra gọi _render_role_selector an toàn ngay cả trước khi gọi build()
        parent_login_view._render_role_selector()
        self.assertIsNotNone(parent_login_view.role_selector_bar)
        
        parent_root = parent_login_view.build()
        self.assertIsNotNone(parent_root)
        self.assertEqual(parent_login_view.active_role, "parent")

        # Kiểm tra chuyển đổi qua lại giữa Học sinh và Phụ huynh
        parent_login_view._switch_role("student")
        self.assertEqual(parent_login_view.active_role, "student")
        parent_login_view._switch_role("parent")
        self.assertEqual(parent_login_view.active_role, "parent")

    def test_auth_modal_change_password(self):
        """Kiểm tra AuthModalDialog khởi tạo và chuyển đổi giữa tab Profile và Đổi Mật Khẩu."""
        from app_tich_hop_socrates.auth_view import AuthModalDialog

        class MockPage:
            def __init__(self):
                self.overlay = []
            def update(self):
                pass

        mock_page = MockPage()
        modal = AuthModalDialog(
            page=mock_page,
            on_user_changed=lambda u: None,
            on_logout=lambda: None
        )
        modal.show()
        self.assertIsNotNone(modal.dialog)
        self.assertEqual(modal.view_tab, "profile")

        # Chuyển tab sang change_password
        modal._switch_tab("change_password")
        self.assertEqual(modal.view_tab, "change_password")

    def test_logout_confirmation_and_flow(self):
        """Kiểm tra quy trình xác nhận đăng xuất cho học sinh và phụ huynh."""
        from app_tich_hop_socrates.parent_view import ParentPortalView
        from app_tich_hop_socrates.parent_service import ParentAccount

        class MockPage:
            def __init__(self):
                self.dialog = None
                self.overlay = []
            def update(self):
                pass
            def open(self, dlg):
                self.dialog = dlg
            def close(self, dlg):
                if self.dialog == dlg:
                    self.dialog = None

        mock_page = MockPage()
        logout_called = []

        parent = ParentAccount(
            username="test_parent",
            display_name="Ba Nam",
            phone_number="0912345678",
            password_hash="dummy",
            children_usernames=["baonhat"]
        )

        parent_view = ParentPortalView(
            page=mock_page,
            parent=parent,
            on_switch_to_student=lambda u: None,
            on_logout=lambda: logout_called.append(True)
        )
        ctrl = parent_view.build()
        self.assertIsNotNone(ctrl)

        # Mở hộp thoại xác nhận đăng xuất
        parent_view._confirm_parent_logout()
        opened_dlg = mock_page.dialog or (mock_page.overlay[0] if mock_page.overlay else None)
        self.assertIsNotNone(opened_dlg)
        self.assertEqual(opened_dlg.title.controls[1].value, "Xác nhận đăng xuất 🚪")

        # Giả lập bấm nút Đăng xuất ngay (nút thứ 2 trong actions)
        do_logout_btn = opened_dlg.actions[1]
        do_logout_btn.on_click(None)
        self.assertTrue(len(logout_called) > 0)


if __name__ == "__main__":
    unittest.main()


