# -*- coding: utf-8 -*-
"""
Unit Test: Kiểm thử chức năng Quản lý Tài khoản Phụ huynh, Liên kết Con em,
Thêm người theo dõi và Đổi người theo dõi (Parent Monitoring & Multi-Child Switcher).
"""

import unittest
from pathlib import Path
from app_tich_hop_socrates.auth_service import AuthService, _hash_pass
from app_tich_hop_socrates.parent_service import ParentService, ParentAccount, PARENTS_FILE, PARENT_SESSION_FILE


class TestParentService(unittest.TestCase):
    def setUp(self):
        # Lưu lại danh sách phụ huynh gốc
        self.orig_parents = ParentService.load_all_parents()

    def tearDown(self):
        # Khôi phục danh sách phụ huynh gốc
        ParentService.save_all_parents(self.orig_parents)
        ParentService.logout_parent()

    def test_seed_parents_exist(self):
        """Kiểm tra danh sách phụ huynh mẫu khởi tạo sẵn."""
        parents = ParentService.load_all_parents()
        self.assertIn("ph_baonhat", parents)
        self.assertIn("ph_minhtriet", parents)

        p_nhat = parents["ph_baonhat"]
        self.assertEqual(p_nhat.active_child_username, "baonhat")
        self.assertIn("baonhat", p_nhat.children_usernames)

        p_triet = parents["ph_minhtriet"]
        self.assertIn("minhtriet", p_triet.children_usernames)
        self.assertIn("baoan", p_triet.children_usernames)

    def test_authenticate_parent(self):
        """Kiểm tra xác thực đăng nhập phụ huynh."""
        # Đăng nhập đúng mật khẩu
        ok, parent, msg = ParentService.authenticate_parent("ph_baonhat", "123")
        self.assertTrue(ok)
        self.assertIsNotNone(parent)
        self.assertEqual(parent.username, "ph_baonhat")

        # Sai mật khẩu
        ok, parent, msg = ParentService.authenticate_parent("ph_baonhat", "wrong_pass")
        self.assertFalse(ok)
        self.assertIsNone(parent)

        # Tài khoản không tồn tại
        ok, parent, msg = ParentService.authenticate_parent("ph_khong_ton_tai", "123")
        self.assertFalse(ok)
        self.assertIsNone(parent)

    def test_register_parent_with_student_verification(self):
        """Kiểm tra tạo tài khoản phụ huynh kèm xác thực mật khẩu học sinh."""
        # 1. Tạo thành công khi mật khẩu học sinh đúng
        ok, parent, msg = ParentService.register_parent(
            parent_username="ph_test_new",
            parent_password="456",
            display_name="Bác Lê Văn Test",
            phone_number="0911223344",
            student_username="minhtriet",
            student_password="123"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(parent)
        self.assertEqual(parent.username, "ph_test_new")
        self.assertIn("minhtriet", parent.children_usernames)
        self.assertEqual(parent.active_child_username, "minhtriet")

        # 2. Thất bại khi mật khẩu con em không chính xác (bảo mật quyền riêng tư)
        ok, parent, msg = ParentService.register_parent(
            parent_username="ph_test_fail",
            parent_password="456",
            display_name="Bác Test Fail",
            phone_number="0911223344",
            student_username="minhtriet",
            student_password="wrong_student_password"
        )
        self.assertFalse(ok)
        self.assertIsNone(parent)
        self.assertIn("không chính xác", msg)

        # 3. Thất bại khi học sinh không tồn tại
        ok, parent, msg = ParentService.register_parent(
            parent_username="ph_test_fail2",
            parent_password="456",
            display_name="Bác Test Fail 2",
            phone_number="0911223344",
            student_username="hoc_sinh_ao_999",
            student_password="123"
        )
        self.assertFalse(ok)
        self.assertIsNone(parent)

    def test_add_child_and_switch_child(self):
        """Kiểm tra tính năng 'Thêm người theo dõi' và 'Đổi người'."""
        # Bác ph_baonhat ban đầu chỉ theo dõi em baonhat
        parent = ParentService.load_all_parents()["ph_baonhat"]
        self.assertEqual(len(parent.children_usernames), 1)

        # Thêm con thứ 2 (em baoan) với mật khẩu đúng (123)
        ok, msg, new_child = ParentService.add_child_to_parent(
            parent_username="ph_baonhat",
            student_username="baoan",
            student_password="123"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(new_child)
        self.assertEqual(new_child.username, "baoan")

        # Kiểm tra danh sách đã có 2 con em
        updated_parent = ParentService.load_all_parents()["ph_baonhat"]
        self.assertIn("baonhat", updated_parent.children_usernames)
        self.assertIn("baoan", updated_parent.children_usernames)
        self.assertEqual(updated_parent.active_child_username, "baoan")

        # Kiểm tra tính năng Đổi người theo dõi quay lại em baonhat
        ok_switch, msg_switch, active_child = ParentService.switch_active_child(
            parent_username="ph_baonhat",
            student_username="baonhat"
        )
        self.assertTrue(ok_switch)
        self.assertIsNotNone(active_child)
        self.assertEqual(active_child.username, "baonhat")

        # Kiểm tra hàm get_parent_children trả về đúng các đối tượng UserAccount
        children = ParentService.get_parent_children(updated_parent)
        self.assertEqual(len(children), 2)
        child_unames = [c.username for c in children]
        self.assertIn("baonhat", child_unames)
        self.assertIn("baoan", child_unames)

    def test_add_child_with_wrong_password_rejected(self):
        """Thêm học sinh theo dõi với mật khẩu sai phải bị từ chối."""
        ok, msg, child = ParentService.add_child_to_parent(
            parent_username="ph_baonhat",
            student_username="minhtriet",
            student_password="sai_mat_khau"
        )
        self.assertFalse(ok)
        self.assertIsNone(child)
        self.assertIn("không chính xác", msg)


if __name__ == "__main__":
    unittest.main()
