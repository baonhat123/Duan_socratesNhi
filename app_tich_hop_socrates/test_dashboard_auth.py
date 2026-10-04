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


if __name__ == "__main__":
    unittest.main()
