"""
Module: auth_service.py
Chức năng: Quản lý Tài khoản Học sinh & Đăng nhập đơn giản cho Socrates Nhí
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Nguyên tắc thiết kế:
- Thân thiện tối đa với học sinh THCS (giao diện tươi sáng, avatar vui nhộn, mật khẩu đơn giản).
- Đăng nhập 1-chạm (Quick Login) cho học sinh mẫu & Ban Giám khảo chấm thi.
- Hỗ trợ Đăng ký mới, Đăng nhập mật khẩu, và chế độ Khách Ẩn danh (Bảo vệ PII trẻ em).
- Lưu trữ cục bộ dạng JSON (hoạt động offline 100%, không cần kết nối internet hay cơ sở dữ liệu nặng).
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
AUTH_DIR = WORKSPACE_ROOT / "so_tay_hoc_tap"
USERS_FILE = AUTH_DIR / "tai_khoan_hoc_sinh.json"
SESSION_FILE = AUTH_DIR / "phien_dang_nhap.json"


@dataclass
class UserAccount:
    """Mô hình dữ liệu tài khoản học sinh."""
    username: str                     # Tên đăng nhập (viết liền không dấu, vd: minhtriet)
    display_name: str                 # Tên hiển thị thân mật (vd: Minh Triết)
    grade_class: str                  # Lớp / Trường (vd: Lớp 7A • Say mê Vật lý)
    avatar: str                       # Emoji đại diện (vd: 💡, 🌿, 🔬, 🚀)
    password_hash: str                # Mã băm mật khẩu sha256
    role: str = "student"             # "student" hoặc "guest"
    created_at: str = ""              # Thời gian tạo tài khoản
    last_login: str = ""              # Thời gian đăng nhập gần nhất

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserAccount":
        return cls(
            username=data.get("username", "guest"),
            display_name=data.get("display_name", "Học sinh Ẩn Danh"),
            grade_class=data.get("grade_class", "KHTN 7"),
            avatar=data.get("avatar", "💡"),
            password_hash=data.get("password_hash", ""),
            role=data.get("role", "student"),
            created_at=data.get("created_at", ""),
            last_login=data.get("last_login", "")
        )


def _hash_pass(raw_password: str) -> str:
    """Mã hóa mật khẩu sha256 với salt an toàn."""
    salt = "socrates_nhi_khtn_2026"
    return hashlib.sha256(f"{salt}_{raw_password}".encode("utf-8")).hexdigest()


# Danh sách các tài khoản học sinh mẫu có sẵn
SEED_USERS: List[Dict[str, Any]] = [
    {
        "username": "minhtriet",
        "display_name": "Minh Triết",
        "grade_class": "Lớp 7A • Say mê Vật lý 💡",
        "avatar": "💡",
        "password_hash": _hash_pass("123"),
        "role": "student",
        "created_at": "01/09/2026 08:00",
        "last_login": "30/09/2026 19:00"
    },
    {
        "username": "baoan",
        "display_name": "Bảo An",
        "grade_class": "Lớp 7B • Yêu Sinh học 🌿",
        "avatar": "🌿",
        "password_hash": _hash_pass("123"),
        "role": "student",
        "created_at": "05/09/2026 09:30",
        "last_login": "30/09/2026 18:30"
    },
    {
        "username": "huyhoang",
        "display_name": "Huy Hoàng",
        "grade_class": "Lớp 7C • Thích Hóa học 🔬",
        "avatar": "🔬",
        "password_hash": _hash_pass("123"),
        "role": "student",
        "created_at": "10/09/2026 14:15",
        "last_login": "30/09/2026 17:45"
    },
    {
        "username": "guest",
        "display_name": "Học sinh Ẩn Danh",
        "grade_class": "Khách Trải Nghiệm Tự Do",
        "avatar": "👤",
        "password_hash": "",
        "role": "guest",
        "created_at": "01/01/2026 00:00",
        "last_login": ""
    }
]


class AuthService:
    """Dịch vụ quản trị tài khoản học sinh."""

    @classmethod
    def _ensure_dir(cls):
        AUTH_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_all_users(cls) -> Dict[str, UserAccount]:
        """Tải toàn bộ tài khoản từ tệp JSON."""
        cls._ensure_dir()
        if not USERS_FILE.exists():
            # Khởi tạo dữ liệu mẫu lần đầu
            users = {u["username"]: UserAccount.from_dict(u) for u in SEED_USERS}
            cls.save_all_users(users)
            return users

        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                users = {}
                for k, v in data.items():
                    users[k] = UserAccount.from_dict(v)

                # Đảm bảo có tài khoản guest và các tài khoản mẫu
                for s in SEED_USERS:
                    if s["username"] not in users:
                        users[s["username"]] = UserAccount.from_dict(s)
                return users
        except Exception as e:
            print(f"[AuthService] Lỗi đọc danh sách tài khoản: {e}")
            return {u["username"]: UserAccount.from_dict(u) for u in SEED_USERS}

    @classmethod
    def save_all_users(cls, users: Dict[str, UserAccount]) -> bool:
        """Lưu toàn bộ tài khoản ra tệp JSON."""
        try:
            cls._ensure_dir()
            data = {k: v.to_dict() for k, v in users.items()}
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[AuthService] Lỗi lưu danh sách tài khoản: {e}")
            return False

    @classmethod
    def get_current_user(cls) -> UserAccount:
        """Lấy thông tin tài khoản đang đăng nhập trong phiên làm việc."""
        cls._ensure_dir()
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    sess = json.load(f)
                    username = sess.get("current_username", "minhtriet")
                    users = cls.load_all_users()
                    if username in users:
                        return users[username]
            except Exception:
                pass

        # Mặc định là Minh Triết (đã sẵn sàng để học)
        users = cls.load_all_users()
        default_user = users.get("minhtriet") or users.get("guest") or UserAccount.from_dict(SEED_USERS[0])
        cls.set_current_user(default_user)
        return default_user

    @classmethod
    def set_current_user(cls, user: UserAccount) -> bool:
        """Lưu phiên đăng nhập hiện tại."""
        try:
            cls._ensure_dir()
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "current_username": user.username,
                    "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[AuthService] Lỗi lưu phiên: {e}")
            return False

    @classmethod
    def authenticate(cls, username: str, raw_password: str) -> Tuple[bool, Optional[UserAccount], str]:
        """Xác thực đăng nhập với tên tài khoản và mật khẩu."""
        clean_user = username.strip().lower()
        if not clean_user:
            return False, None, "Vui lòng nhập tên tài khoản!"

        users = cls.load_all_users()
        if clean_user not in users:
            return False, None, f"Không tìm thấy tài khoản '{username}'!"

        user = users[clean_user]
        if user.role == "guest":
            # Tài khoản khách không cần mật khẩu
            user.last_login = datetime.now().strftime("%d/%m/%Y %H:%M")
            cls.save_all_users(users)
            cls.set_current_user(user)
            return True, user, f"Đăng nhập thành công với vai trò {user.display_name}!"

        expected_hash = _hash_pass(raw_password)
        if user.password_hash != expected_hash:
            return False, None, "Mật khẩu không chính xác! (Gợi ý cho tài khoản mẫu: 123)"

        # Cập nhật thời gian đăng nhập
        user.last_login = datetime.now().strftime("%d/%m/%Y %H:%M")
        cls.save_all_users(users)
        cls.set_current_user(user)
        return True, user, f"Chào mừng {user.display_name} trở lại!"

    @classmethod
    def quick_login(cls, username: str) -> Tuple[bool, Optional[UserAccount], str]:
        """Đăng nhập 1-chạm không cần gõ mật khẩu (Dành cho tài khoản mẫu & Giám khảo)."""
        users = cls.load_all_users()
        clean_user = username.strip().lower()
        if clean_user in users:
            user = users[clean_user]
            user.last_login = datetime.now().strftime("%d/%m/%Y %H:%M")
            cls.save_all_users(users)
            cls.set_current_user(user)
            return True, user, f"Đã chuyển sang tài khoản {user.display_name}!"
        return False, None, f"Không tìm thấy tài khoản '{username}'!"

    @classmethod
    def register_account(
        cls,
        username: str,
        raw_password: str,
        display_name: str,
        grade_class: str = "",
        avatar: str = "💡"
    ) -> Tuple[bool, Optional[UserAccount], str]:
        """Tạo tài khoản học sinh mới."""
        clean_user = username.strip().lower()
        clean_name = display_name.strip()

        if not clean_user:
            return False, None, "Tên tài khoản không được để trống!"
        if len(clean_user) < 3:
            return False, None, "Tên tài khoản phải có ít nhất 3 ký tự (viết liền, không dấu)!"
        if not clean_name:
            return False, None, "Vui lòng nhập tên hoặc biệt danh của em!"
        if len(raw_password) < 2:
            return False, None, "Mật khẩu phải có ít nhất 2 ký tự!"

        users = cls.load_all_users()
        if clean_user in users:
            return False, None, f"Tài khoản '{clean_user}' đã tồn tại! Vui lòng chọn tên khác."

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        new_user = UserAccount(
            username=clean_user,
            display_name=clean_name,
            grade_class=grade_class.strip() or "Học sinh THCS",
            avatar=avatar or "💡",
            password_hash=_hash_pass(raw_password),
            role="student",
            created_at=now_str,
            last_login=now_str
        )

        users[clean_user] = new_user
        cls.save_all_users(users)
        cls.set_current_user(new_user)
        return True, new_user, f"Chúc mừng {clean_name}! Tài khoản của em đã được tạo thành công!"

    @classmethod
    def logout(cls):
        """Đăng xuất phiên làm việc hiện tại."""
        try:
            cls._ensure_dir()
            if SESSION_FILE.exists():
                with open(SESSION_FILE, "w", encoding="utf-8") as f:
                    json.dump({
                        "current_username": "",
                        "is_logged_in": False,
                        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def logout_to_guest(cls) -> UserAccount:
        """Đăng xuất và chuyển về tài khoản Khách Ẩn Danh."""
        users = cls.load_all_users()
        guest_user = users.get("guest") or UserAccount.from_dict(SEED_USERS[3])
        cls.set_current_user(guest_user)
        return guest_user

    @classmethod
    def get_user_notebook_stats(cls, username: str) -> Dict[str, Any]:
        """Thống kê số lượng bài học và đánh giá của tài khoản trong Sổ tay."""
        from chuc_nang_5_so_do_tong_ket.notebook_manager import load_notebook_entries
        entries = load_notebook_entries()

        user_entries = [
            e for e in entries
            if e.get("author_username") == username or (username == "minhtriet" and not e.get("author_username"))
        ]

        total_lessons = len(user_entries)
        avg_stars = (sum(e.get("rating_stars", 5) for e in user_entries) / total_lessons) if total_lessons > 0 else 5.0

        return {
            "total_lessons": total_lessons,
            "avg_stars": round(avg_stars, 1),
            "user_entries": user_entries
        }
