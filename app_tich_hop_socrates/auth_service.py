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
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
AUTH_DIR = WORKSPACE_ROOT / "so_tay_hoc_tap"
USERS_FILE = AUTH_DIR / "tai_khoan_hoc_sinh.json"
SESSION_FILE = AUTH_DIR / "phien_dang_nhap.json"


def get_sample_study_dates(streak_days: int = 5) -> List[str]:
    """Tạo danh sách các ngày học liên tiếp kết thúc vào ngày hôm qua để làm dữ liệu mẫu ban đầu."""
    today = datetime.now().date()
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(streak_days, 0, -1)]


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
    streak_count: int = 0             # Chuỗi ngày học liên tục (Streak) - mặc định 0!
    max_streak: int = 0               # Kỷ lục chuỗi ngày học - mặc định 0!
    study_dates: List[str] = field(default_factory=list) # Mặc định danh sách ngày học RỖNG []
    completed_topics: List[str] = field(default_factory=list)
    physics_count: int = 0            # Số bài Vật lý đã hoàn thành - mặc định 0
    chemistry_count: int = 0          # Số bài Hóa học đã hoàn thành - mặc định 0
    biology_count: int = 0            # Số bài Sinh học đã hoàn thành - mặc định 0
    total_study_minutes: int = 0      # Tổng số phút học - mặc định 0
    daily_study_minutes: Dict[str, int] = field(default_factory=dict) # Phân bổ số phút học từng ngày YYYY-MM-DD
    solved_exercises_count: int = 0   # Tổng số bài tập đã giải thành công - mặc định 0!
    streak_freeze_count: int = 0      # Bùa khiên bảo vệ chuỗi ngày học - mặc định 0
    last_solved_date: str = ""        # Ngày giải bài tập gần nhất (YYYY-MM-DD)
    security_question: str = "Môn học KHTN em yêu thích nhất?"  # Câu hỏi bảo mật phục hồi mật khẩu
    security_answer_hash: str = ""    # Mã băm câu trả lời bảo mật

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserAccount":
        raw_dates = data.get("study_dates")
        study_dates = list(raw_dates) if isinstance(raw_dates, list) else []
        return cls(
            username=data.get("username", "guest"),
            display_name=data.get("display_name", "Học sinh Ẩn Danh"),
            grade_class=data.get("grade_class", "KHTN 7"),
            avatar=data.get("avatar", "💡"),
            password_hash=data.get("password_hash", ""),
            role=data.get("role", "student"),
            created_at=data.get("created_at", ""),
            last_login=data.get("last_login", ""),
            streak_count=int(data.get("streak_count", 0)),
            max_streak=int(data.get("max_streak", 0)),
            study_dates=study_dates,
            completed_topics=list(data.get("completed_topics", [])),
            physics_count=int(data.get("physics_count", 0)),
            chemistry_count=int(data.get("chemistry_count", 0)),
            biology_count=int(data.get("biology_count", 0)),
            total_study_minutes=int(data.get("total_study_minutes", 0)),
            daily_study_minutes=dict(data.get("daily_study_minutes", {})),
            solved_exercises_count=int(data.get("solved_exercises_count", 0)),
            streak_freeze_count=int(data.get("streak_freeze_count", 0)),
            last_solved_date=data.get("last_solved_date", (study_dates[-1] if study_dates else "")),
            security_question=data.get("security_question", "Môn học KHTN em yêu thích nhất?"),
            security_answer_hash=data.get("security_answer_hash", "")
        )


def _hash_pass(raw_password: str) -> str:
    """Mã hóa mật khẩu sha256 với salt an toàn."""
    salt = "socrates_nhi_khtn_2026"
    return hashlib.sha256(f"{salt}_{raw_password}".encode("utf-8")).hexdigest()


def evaluate_password_strength(password: str) -> Dict[str, Any]:
    """
    Đánh giá độ mạnh mật khẩu chuẩn trang web hiện đại:
    - Trả về điểm (0-100), nhãn, màu sắc và lời khuyên sư phạm.
    """
    pwd = password or ""
    length = len(pwd)

    if length == 0:
        return {
            "score": 0,
            "label": "Chưa nhập",
            "color": "#94A3B8",
            "percent": 0.0,
            "tips": "Em hãy đặt mật khẩu từ 4-6 ký tự dễ nhớ."
        }
    if length < 3:
        return {
            "score": 20,
            "label": "Quá ngắn",
            "color": "#EF4444",
            "percent": 0.2,
            "tips": "Mật khẩu cần ít nhất 3 ký tự!"
        }

    has_alpha = any(c.isalpha() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    has_special = any(not c.isalnum() for c in pwd)

    if length < 6:
        return {
            "score": 45,
            "label": "Trung bình",
            "color": "#F59E0B",
            "percent": 0.45,
            "tips": "Nên có ít nhất 6 ký tự để bảo vệ Sổ tay tự học an toàn hơn."
        }
    elif (has_alpha and has_digit) or has_special:
        if length >= 8:
            return {
                "score": 100,
                "label": "Rất an toàn ✨",
                "color": "#10B981",
                "percent": 1.0,
                "tips": "Mật khẩu tuyệt vời! Rất mạnh và an toàn."
            }
        return {
            "score": 80,
            "label": "Mạnh ✓",
            "color": "#059669",
            "percent": 0.8,
            "tips": "Mật khẩu an toàn, gồm cả chữ và số."
        }
    else:
        return {
            "score": 60,
            "label": "Khá ổn",
            "color": "#3B82F6",
            "percent": 0.6,
            "tips": "Em có thể kết hợp thêm chữ số để mật khẩu mạnh hơn."
        }


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
        "last_login": "30/09/2026 19:00",
        "security_question": "Môn học KHTN em yêu thích nhất?",
        "security_answer_hash": _hash_pass("vat ly")
    },
    {
        "username": "baoan",
        "display_name": "Bảo An",
        "grade_class": "Lớp 7B • Yêu Sinh học 🌿",
        "avatar": "🌿",
        "password_hash": _hash_pass("123"),
        "role": "student",
        "created_at": "05/09/2026 09:30",
        "last_login": "30/09/2026 18:30",
        "security_question": "Môn học KHTN em yêu thích nhất?",
        "security_answer_hash": _hash_pass("sinh hoc")
    },
    {
        "username": "huyhoang",
        "display_name": "Huy Hoàng",
        "grade_class": "Lớp 7C • Thích Hóa học 🔬",
        "avatar": "🔬",
        "password_hash": _hash_pass("123"),
        "role": "student",
        "created_at": "10/09/2026 14:15",
        "last_login": "30/09/2026 17:45",
        "security_question": "Môn học KHTN em yêu thích nhất?",
        "security_answer_hash": _hash_pass("hoa hoc")
    },
    {
        "username": "baonhat",
        "display_name": "Phan Nhật",
        "grade_class": "Lớp 7/8 • THCS Nguyễn Bỉnh Khiêm 🏆",
        "avatar": "🏆",
        "password_hash": _hash_pass("123"),
        "role": "student",
        "created_at": "30/09/2026 19:45",
        "last_login": "01/10/2026 18:25",
        "security_question": "Môn học KHTN em yêu thích nhất?",
        "security_answer_hash": _hash_pass("khtn")
    },
    {
        "username": "guest",
        "display_name": "Học sinh Ẩn Danh",
        "grade_class": "Khách Trải Nghiệm Tự Do",
        "avatar": "👤",
        "password_hash": "",
        "role": "guest",
        "created_at": "01/01/2026 00:00",
        "last_login": "",
        "security_question": "Môn học KHTN em yêu thích nhất?",
        "security_answer_hash": ""
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
    def get_session_info(cls) -> Dict[str, Any]:
        """Lấy thông tin chi tiết phiên đăng nhập từ file."""
        cls._ensure_dir()
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"current_username": "", "remember_me": False, "is_logged_in": False}

    @classmethod
    def get_current_user(cls) -> UserAccount:
        """Lấy thông tin tài khoản đang đăng nhập trong phiên làm việc."""
        cls._ensure_dir()
        sess = cls.get_session_info()
        username = sess.get("current_username", "")
        users = cls.load_all_users()

        if username and username in users:
            return users[username]

        # Mặc định là Phan Nhật (tài khoản học sinh chính thức)
        default_user = users.get("baonhat") or users.get("minhtriet") or users.get("guest") or UserAccount.from_dict(SEED_USERS[0])
        cls.set_current_user(default_user, remember_me=True)
        return default_user

    @classmethod
    def set_current_user(cls, user: UserAccount, remember_me: bool = True) -> bool:
        """Lưu phiên đăng nhập hiện tại kèm tùy chọn Ghi nhớ tài khoản."""
        try:
            cls._ensure_dir()
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "current_username": user.username,
                    "remember_me": bool(remember_me),
                    "is_logged_in": True,
                    "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[AuthService] Lỗi lưu phiên: {e}")
            return False

    @classmethod
    def authenticate(cls, username: str, raw_password: str, remember_me: bool = True) -> Tuple[bool, Optional[UserAccount], str]:
        """Xác thực đăng nhập với tên tài khoản và mật khẩu."""
        clean_user = username.strip().lower()
        if not clean_user:
            return False, None, "Vui lòng nhập tên tài khoản của em!"

        users = cls.load_all_users()
        if clean_user not in users:
            return False, None, f"Không tìm thấy tài khoản '{username}'! Em có muốn tạo tài khoản mới không?"

        user = users[clean_user]
        if user.role == "guest":
            # Tài khoản khách không cần mật khẩu
            user.last_login = datetime.now().strftime("%d/%m/%Y %H:%M")
            cls.save_all_users(users)
            cls.set_current_user(user, remember_me=remember_me)
            return True, user, f"Đăng nhập thành công với vai trò {user.display_name}!"

        expected_hash = _hash_pass(raw_password)
        if user.password_hash != expected_hash:
            return False, None, "Mật khẩu không chính xác! (Gợi ý cho tài khoản mẫu: 123 hoặc bấm 'Quên mật khẩu?')"

        # Cập nhật thời gian đăng nhập
        user.last_login = datetime.now().strftime("%d/%m/%Y %H:%M")
        cls.save_all_users(users)
        cls.set_current_user(user, remember_me=remember_me)
        return True, user, f"Chào mừng {user.display_name} trở lại! Chúc em có buổi học bổ ích 💡"

    @classmethod
    def quick_login(cls, username: str, remember_me: bool = True) -> Tuple[bool, Optional[UserAccount], str]:
        """Đăng nhập 1-chạm không cần gõ mật khẩu (Dành cho tài khoản mẫu & Giám khảo)."""
        users = cls.load_all_users()
        clean_user = username.strip().lower()
        if clean_user in users:
            user = users[clean_user]
            user.last_login = datetime.now().strftime("%d/%m/%Y %H:%M")
            cls.save_all_users(users)
            cls.set_current_user(user, remember_me=remember_me)
            return True, user, f"Đã chuyển sang tài khoản {user.display_name}!"
        return False, None, f"Không tìm thấy tài khoản '{username}'!"

    @classmethod
    def register_account(
        cls,
        username: str,
        raw_password: str,
        display_name: str,
        grade_class: str = "",
        avatar: str = "💡",
        security_question: str = "Môn học KHTN em yêu thích nhất?",
        security_answer: str = "",
        remember_me: bool = True
    ) -> Tuple[bool, Optional[UserAccount], str]:
        """Tạo tài khoản học sinh mới kèm câu hỏi bảo mật chuẩn web."""
        clean_user = username.strip().lower()
        clean_name = display_name.strip()

        if not clean_user:
            return False, None, "Tên tài khoản không được để trống!"
        if len(clean_user) < 3:
            return False, None, "Tên tài khoản phải có ít nhất 3 ký tự (viết liền, không dấu)!"
        if not clean_user.isalnum() and "_" not in clean_user:
            return False, None, "Tên tài khoản chỉ gồm chữ cái, chữ số và dấu gạch dưới!"
        if not clean_name:
            return False, None, "Vui lòng nhập tên hoặc biệt danh của em!"
        if len(raw_password) < 3:
            return False, None, "Mật khẩu phải có ít nhất 3 ký tự để bảo mật!"

        users = cls.load_all_users()
        if clean_user in users:
            return False, None, f"Tài khoản '{clean_user}' đã tồn tại! Vui lòng chọn một tên khác."

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        ans_hash = _hash_pass(security_answer.strip().lower()) if security_answer.strip() else ""

        new_user = UserAccount(
            username=clean_user,
            display_name=clean_name,
            grade_class=grade_class.strip() or "Học sinh THCS",
            avatar=avatar or "💡",
            password_hash=_hash_pass(raw_password),
            role="student",
            created_at=now_str,
            last_login=now_str,
            security_question=security_question or "Môn học KHTN em yêu thích nhất?",
            security_answer_hash=ans_hash
        )

        users[clean_user] = new_user
        cls.save_all_users(users)
        cls.set_current_user(new_user, remember_me=remember_me)
        return True, new_user, f"Chúc mừng {clean_name}! Tài khoản của em đã được tạo thành công!"

    @classmethod
    def change_password(cls, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Đổi mật khẩu cho tài khoản học sinh đang đăng nhập."""
        users = cls.load_all_users()
        clean_user = username.strip().lower()
        if clean_user not in users:
            return False, "Không tìm thấy tài khoản!"

        user = users[clean_user]
        if user.role == "guest":
            return False, "Tài khoản Khách Trải Nghiệm không có mật khẩu để đổi."

        # Kiểm tra mật khẩu cũ
        if user.password_hash != _hash_pass(old_password):
            return False, "Mật khẩu hiện tại không chính xác!"

        if len(new_password) < 3:
            return False, "Mật khẩu mới phải có ít nhất 3 ký tự!"

        user.password_hash = _hash_pass(new_password)
        cls.save_all_users(users)
        return True, "Đổi mật khẩu thành công! Hãy ghi nhớ mật khẩu mới của em nhé."

    @classmethod
    def get_security_question(cls, username: str) -> Tuple[bool, str, str]:
        """Lấy câu hỏi bảo mật của tài khoản để học sinh khôi phục mật khẩu."""
        users = cls.load_all_users()
        clean_user = username.strip().lower()
        if clean_user not in users:
            return False, "", f"Không tìm thấy tài khoản '{username}'!"

        user = users[clean_user]
        question = user.security_question or "Môn học KHTN em yêu thích nhất?"
        return True, question, ""

    @classmethod
    def reset_password_with_question(cls, username: str, answer: str, new_password: str) -> Tuple[bool, str]:
        """Khôi phục mật khẩu thông qua câu hỏi bảo mật."""
        users = cls.load_all_users()
        clean_user = username.strip().lower()
        if clean_user not in users:
            return False, f"Không tìm thấy tài khoản '{username}'!"

        user = users[clean_user]
        if user.role == "guest":
            return False, "Tài khoản Khách không cần đặt lại mật khẩu."

        clean_ans = answer.strip().lower()
        if not clean_ans:
            return False, "Vui lòng nhập câu trả lời bảo mật!"

        # Kiểm tra câu trả lời
        ans_hash = _hash_pass(clean_ans)
        # Hỗ trợ cả trường hợp tài khoản cũ chưa có hash hoặc tài khoản mẫu
        is_valid = False
        if user.security_answer_hash and user.security_answer_hash == ans_hash:
            is_valid = True
        elif not user.security_answer_hash and clean_ans in ["123", "vat ly", "khtn", "sinh hoc", "hoa hoc", "socrates"]:
            is_valid = True

        if not is_valid:
            return False, "Câu trả lời bảo mật chưa chính xác! (Gợi ý cho tài khoản mẫu: 'vat ly', 'sinh hoc', 'khtn')"

        if len(new_password) < 3:
            return False, "Mật khẩu mới phải có ít nhất 3 ký tự!"

        user.password_hash = _hash_pass(new_password)
        user.security_answer_hash = ans_hash
        cls.save_all_users(users)
        return True, "Khôi phục mật khẩu thành công! Bây giờ em có thể đăng nhập bằng mật khẩu mới."

    @classmethod
    def logout(cls, clear_remember: bool = False):
        """Đăng xuất phiên làm việc hiện tại."""
        try:
            cls._ensure_dir()
            if SESSION_FILE.exists():
                sess = cls.get_session_info()
                username_to_keep = "" if clear_remember else sess.get("current_username", "")
                with open(SESSION_FILE, "w", encoding="utf-8") as f:
                    json.dump({
                        "current_username": username_to_keep,
                        "remember_me": not clear_remember,
                        "is_logged_in": False,
                        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def clear_remembered_account(cls):
        """Xóa hoàn toàn thông tin tài khoản đã ghi nhớ khỏi thiết bị."""
        cls.logout(clear_remember=True)

    @classmethod
    def logout_to_guest(cls) -> UserAccount:
        """Đăng xuất và chuyển về tài khoản Khách Ẩn Danh."""
        users = cls.load_all_users()
        guest_user = users.get("guest") or UserAccount.from_dict(SEED_USERS[-1])
        cls.set_current_user(guest_user, remember_me=False)
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

    @classmethod
    def calculate_streak(cls, study_dates: List[str]) -> Tuple[int, bool, bool]:
        """
        Tính chuỗi ngày học thực tế (Streak) dựa trên ngày giải bài:
        - QUY TẮC SƯ PHẠM: Học sinh PHẢI GIẢI BÀI TẬP trong ngày mới được tính chuỗi ngày học.
        - Trả về: (streak_count, studied_today, studied_yesterday)
        
        Logic xác thực:
        1. Hôm nay đã giải bài (today_str in study_dates):
           Đếm chuỗi ngày liên tiếp lùi từ hôm nay: hôm nay, hôm qua, hôm kia...
           -> streak >= 1, studied_today = True.
        2. Hôm nay chưa giải bài (today_str not in study_dates):
           - Nếu hôm qua có giải bài: Bảo lưu chuỗi của ngày hôm qua (đang chờ giải hôm nay để tăng +1).
             studied_today = False, studied_yesterday = True.
           - Nếu hôm qua KHÔNG giải bài: Đã bị đứt chuỗi do bỏ lỡ >= 1 ngày -> streak = 0.
             studied_today = False, studied_yesterday = False.
        """
        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")
        yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")

        unique_dates = set(study_dates or [])
        studied_today = today_str in unique_dates
        studied_yesterday = yesterday_str in unique_dates

        if studied_today:
            streak = 0
            cur = today
            while cur.strftime("%Y-%m-%d") in unique_dates:
                streak += 1
                cur -= timedelta(days=1)
            return streak, True, studied_yesterday
        elif studied_yesterday:
            streak = 0
            cur = today - timedelta(days=1)
            while cur.strftime("%Y-%m-%d") in unique_dates:
                streak += 1
                cur -= timedelta(days=1)
            return streak, False, True
        else:
            return 0, False, False

    @classmethod
    def get_user_streak(cls, username: str) -> Dict[str, Any]:
        """Lấy thông tin chuỗi ngày học liên tục (Streak) và lịch 7 ngày trong tuần."""
        users = cls.load_all_users()
        user = users.get(username) or cls.get_current_user()

        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")

        # Tính toán streak thực tế chuẩn xác
        streak_count, today_studied, studied_yesterday = cls.calculate_streak(user.study_dates)

        # Cập nhật tự động streak_count và kỷ lục max_streak nếu có biến động
        if user.streak_count != streak_count or streak_count > user.max_streak:
            user.streak_count = streak_count
            user.max_streak = max(user.max_streak, streak_count)
            users[user.username] = user
            cls.save_all_users(users)

        today_mins = user.daily_study_minutes.get(today_str, 0)
        if today_studied and today_mins == 0:
            today_mins = min(user.total_study_minutes, 45) if user.total_study_minutes > 0 else 15

        # Lịch 7 ngày của tuần hiện tại (Thứ 2 đến Chủ nhật)
        current_weekday = today.weekday() # 0 = T2, 6 = CN
        start_of_week = today - timedelta(days=current_weekday)

        week_days = []
        day_labels = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        day_names_full = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

        for i in range(7):
            day_date = start_of_week + timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            is_today = (day_str == today_str)
            if is_today:
                studied = today_studied
                mins = today_mins
            else:
                studied = day_str in user.study_dates
                mins = user.daily_study_minutes.get(day_str, (45 if studied else 0))

            week_days.append({
                "label": day_labels[i],
                "full_name": day_names_full[i],
                "date": day_str,
                "studied": studied,
                "is_today": is_today,
                "minutes": mins
            })

        status_msg = (
            f"🔥 Tuyệt vời! Em đã giải bài hôm nay và đạt chuỗi {streak_count} ngày liên tiếp!"
            if today_studied
            else (
                f"⏳ Chuỗi {streak_count} ngày đang chờ em! Hãy giải 1 bài KHTN hôm nay để đạt chuỗi {streak_count + 1} ngày nhé!"
                if studied_yesterday
                else "🎯 Chuỗi ngày học đã ngắt. Hãy giải 1 bài hôm nay để thắp lại ngọn lửa chuỗi 1 ngày nhé!"
            )
        )

        return {
            "streak_count": streak_count,
            "max_streak": max(user.max_streak, streak_count),
            "study_dates": user.study_dates,
            "week_days": week_days,
            "today_studied": today_studied,
            "today_minutes": today_mins,
            "studied_yesterday": studied_yesterday,
            "solved_exercises_count": getattr(user, "solved_exercises_count", len(user.study_dates)),
            "status_message": status_msg
        }

    @classmethod
    def get_user_progress(cls, username: str) -> Dict[str, Any]:
        """Thống kê chi tiết tiến độ học tập 3 mạch KHTN 7 và huy hiệu."""
        from chuc_nang_5_so_do_tong_ket.notebook_manager import load_notebook_entries
        entries = load_notebook_entries()

        user_entries = [
            e for e in entries
            if e.get("author_username") == username or (username in ["baonhat", "minhtriet"] and not e.get("author_username"))
        ]

        users = cls.load_all_users()
        user = users.get(username) or cls.get_current_user()

        notebook_count = len(user_entries)

        # Đếm theo 3 mạch kiến thức
        phys = max(user.physics_count, sum(1 for e in user_entries if any(k in e.get("topic", "") for k in ["Vật", "Tốc độ", "Âm", "Ánh sáng", "VL"])))
        chem = max(user.chemistry_count, sum(1 for e in user_entries if any(k in e.get("topic", "") for k in ["Hóa", "Nguyên tử", "Phân tử", "Hóa trị", "HH"])))
        bio = max(user.biology_count, sum(1 for e in user_entries if any(k in e.get("topic", "") for k in ["Sinh", "Quang hợp", "Hô hấp", "Cảm ứng", "SH"])))

        total_completed = min(phys + chem + bio, 12)
        total_target = 12
        progress_percent = int((total_completed / total_target) * 100)

        # Tính điểm Rubric trung bình
        avg_rubric = 5.2
        if user_entries:
            rubrics = [e.get("rubric_score", 5) for e in user_entries if e.get("rubric_score")]
            if rubrics:
                avg_rubric = round(sum(rubrics) / len(rubrics), 1)

        # Huy hiệu đạt được
        badges = [
            {"id": "first_step", "name": "Nhà Khám Phá Nhí", "desc": "Hoàn thành bài học đầu tiên", "icon": "🌟", "unlocked": True},
            {"id": "streak_3", "name": "Ngọn Lửa Kiên Trì", "desc": "Chuỗi học liên tục từ 3 ngày", "icon": "🔥", "unlocked": user.streak_count >= 3},
            {"id": "physics_pro", "name": "Cao Thủ Vật Lý", "desc": "Làm chủ công thức Tốc độ KHTN", "icon": "⚡", "unlocked": phys >= 1},
            {"id": "chem_expert", "name": "Nhà Hóa Học Tương Lai", "desc": "Hiểu rõ Cấu tạo nguyên tử & Phân tử", "icon": "🔬", "unlocked": chem >= 1},
            {"id": "bio_master", "name": "Bậc Thầy Sinh Học", "desc": "Đúc kết bài học Trao đổi chất & Năng lượng", "icon": "🌿", "unlocked": bio >= 1},
            {"id": "guardrail_hero", "name": "Hiệp Sĩ Tự Tư Duy", "desc": "Tuyệt đối không ỷ lại lời giải có sẵn", "icon": "🛡️", "unlocked": True},
            {"id": "notebook_scholar", "name": "Nhà Đúc Kết Tri Thức", "desc": "Lưu trữ bài học vào Sổ tay Tự học", "icon": "📓", "unlocked": notebook_count >= 1}
        ]

        return {
            "total_completed": total_completed,
            "total_target": total_target,
            "progress_percent": progress_percent,
            "physics_completed": min(phys, 4),
            "chemistry_completed": min(chem, 4),
            "biology_completed": min(bio, 4),
            "notebook_count": notebook_count,
            "avg_rubric": avg_rubric,
            "total_study_minutes": user.total_study_minutes,
            "badges": badges
        }

    @classmethod
    def record_exercise_solved(
        cls,
        username: str,
        topic: str = "",
        domain: str = "",
        exercise_type: str = "exercise",
        score: float = 10.0,
        minutes: int = 15,
        is_new_exercise: bool = True
    ) -> Dict[str, Any]:
        """
        Ghi nhận một bài tập đã được học sinh hoàn thành:
        - QUY TẮC SƯ PHẠM: Học sinh PHẢI GIẢI BÀI (Quiz, Socratic, hoặc đúc kết Sổ tay) mới được cộng chuỗi.
        - Cập nhật số bài giải, thời gian học, phân môn Lý-Hóa-Sinh.
        - Tự động cộng chuỗi Streak ngày học và kiểm tra kỷ lục.
        """
        users = cls.load_all_users()
        user = users.get(username)
        if not user:
            return {"success": False, "streak_count": 0, "is_new_streak_day": False}

        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")

        is_new_streak_day = today_str not in user.study_dates

        # Thêm ngày hôm nay vào danh sách ngày học nếu chưa có
        if is_new_streak_day:
            user.study_dates.append(today_str)

        # Cập nhật số phút học
        user.daily_study_minutes[today_str] = user.daily_study_minutes.get(today_str, 0) + minutes
        user.total_study_minutes += minutes

        # Tăng tổng số bài tập đã giải (chỉ tăng khi là phiên bài tập mới)
        if is_new_exercise:
            user.solved_exercises_count = getattr(user, "solved_exercises_count", 0) + 1
        user.last_solved_date = today_str

        # Tính toán lại chuỗi Streak chuẩn xác
        streak, studied_today, studied_yesterday = cls.calculate_streak(user.study_dates)
        user.streak_count = streak
        if streak > user.max_streak:
            user.max_streak = streak

        # Cập nhật chủ đề và phân môn KHTN
        if topic and topic not in user.completed_topics:
            user.completed_topics.append(topic)

        if is_new_exercise:
            dom_lower = (domain or "").lower() + " " + (topic or "").lower()
            if any(k in dom_lower for k in ["vật", "vl", "tốc độ", "âm", "ánh sáng", "lực", "năng lượng"]):
                user.physics_count += 1
            elif any(k in dom_lower for k in ["hóa", "hh", "nguyên tử", "phân tử", "nguyên tố", "hóa trị"]):
                user.chemistry_count += 1
            elif any(k in dom_lower for k in ["sinh", "sh", "quang hợp", "hô hấp", "tế bào", "cảm ứng"]):
                user.biology_count += 1

        cls.save_all_users(users)
        if cls.get_current_user().username == username:
            cls.set_current_user(user)

        return {
            "success": True,
            "username": username,
            "streak_count": user.streak_count,
            "max_streak": user.max_streak,
            "is_new_streak_day": is_new_streak_day,
            "today_studied": True,
            "solved_exercises_count": user.solved_exercises_count,
            "message": (
                f"🎉 Chúc mừng em đã giải xong bài tập! Chuỗi học tập đã tăng lên {user.streak_count} ngày liên tiếp! 🔥"
                if is_new_streak_day
                else f"🌟 Em đã hoàn thành thêm 1 bài tập hôm nay! Chuỗi {user.streak_count} ngày đang bừng sáng! 🔥"
            )
        }

    @classmethod
    def record_study_session(cls, username: str, topic: str = "", domain: str = "", minutes: int = 10, is_new_exercise: bool = True):
        """Ghi nhận phiên học tập mới (Ủy quyền sang record_exercise_solved để đồng nhất)."""
        return cls.record_exercise_solved(
            username=username,
            topic=topic,
            domain=domain,
            exercise_type="study_session",
            score=10.0,
            minutes=minutes,
            is_new_exercise=is_new_exercise
        )

    @classmethod
    def update_profile(cls, username: str, display_name: str, grade_class: str, avatar: str) -> bool:
        """Cập nhật thông tin hồ sơ tài khoản học sinh."""
        users = cls.load_all_users()
        user = users.get(username)
        if not user:
            return False

        if display_name.strip():
            user.display_name = display_name.strip()
        if grade_class.strip():
            user.grade_class = grade_class.strip()
        if avatar.strip():
            user.avatar = avatar.strip()

        cls.save_all_users(users)
        if cls.get_current_user().username == username:
            cls.set_current_user(user)
        return True
