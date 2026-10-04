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
    streak_count: int = 5             # Chuỗi ngày học liên tục (Streak)
    max_streak: int = 7               # Kỷ lục chuỗi ngày học
    study_dates: List[str] = field(default_factory=lambda: ["2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01"])
    completed_topics: List[str] = field(default_factory=list)
    physics_count: int = 2            # Số bài Vật lý đã hoàn thành
    chemistry_count: int = 1          # Số bài Hóa học đã hoàn thành
    biology_count: int = 2            # Số bài Sinh học đã hoàn thành
    total_study_minutes: int = 45     # Tổng số phút học

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserAccount":
        today_str = datetime.now().strftime("%Y-%m-%d")
        default_dates = ["2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30", today_str]
        return cls(
            username=data.get("username", "guest"),
            display_name=data.get("display_name", "Học sinh Ẩn Danh"),
            grade_class=data.get("grade_class", "KHTN 7"),
            avatar=data.get("avatar", "💡"),
            password_hash=data.get("password_hash", ""),
            role=data.get("role", "student"),
            created_at=data.get("created_at", ""),
            last_login=data.get("last_login", ""),
            streak_count=int(data.get("streak_count", 5)),
            max_streak=int(data.get("max_streak", 7)),
            study_dates=list(data.get("study_dates", default_dates)),
            completed_topics=list(data.get("completed_topics", [])),
            physics_count=int(data.get("physics_count", 2)),
            chemistry_count=int(data.get("chemistry_count", 1)),
            biology_count=int(data.get("biology_count", 2)),
            total_study_minutes=int(data.get("total_study_minutes", 45))
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
                    username = sess.get("current_username", "baonhat")
                    users = cls.load_all_users()
                    if username in users:
                        return users[username]
            except Exception:
                pass

        # Mặc định là Phan Nhật (tài khoản học sinh chính thức)
        users = cls.load_all_users()
        default_user = users.get("baonhat") or users.get("minhtriet") or users.get("guest") or UserAccount.from_dict(SEED_USERS[0])
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

    @classmethod
    def get_user_streak(cls, username: str) -> Dict[str, Any]:
        """Lấy thông tin chuỗi ngày học liên tục (Streak) và lịch 7 ngày trong tuần."""
        users = cls.load_all_users()
        user = users.get(username) or cls.get_current_user()

        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")

        # Đảm bảo hôm nay có trong danh sách ngày học
        if today_str not in user.study_dates:
            user.study_dates.append(today_str)
            user.streak_count = max(user.streak_count, 1)
            cls.save_all_users(users)

        # Lịch 7 ngày của tuần hiện tại (Thứ 2 đến Chủ nhật)
        current_weekday = today.weekday() # 0 = T2, 6 = CN
        start_of_week = today - timedelta(days=current_weekday)

        week_days = []
        day_labels = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        day_names_full = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

        for i in range(7):
            day_date = start_of_week + timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            studied = day_str in user.study_dates
            is_today = (day_str == today_str)
            week_days.append({
                "label": day_labels[i],
                "full_name": day_names_full[i],
                "date": day_str,
                "studied": studied,
                "is_today": is_today
            })

        return {
            "streak_count": user.streak_count,
            "max_streak": max(user.max_streak, user.streak_count),
            "study_dates": user.study_dates,
            "week_days": week_days,
            "today_studied": True
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
    def record_study_session(cls, username: str, topic: str = "", domain: str = "", minutes: int = 10):
        """Ghi nhận phiên học tập mới: cập nhật streak và tiến độ."""
        users = cls.load_all_users()
        user = users.get(username)
        if not user:
            return

        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")

        if today_str not in user.study_dates:
            yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            if yesterday_str in user.study_dates:
                user.streak_count += 1
            else:
                user.streak_count = 1
            user.study_dates.append(today_str)
            if user.streak_count > user.max_streak:
                user.max_streak = user.streak_count

        user.total_study_minutes += minutes

        if topic and topic not in user.completed_topics:
            user.completed_topics.append(topic)

        if any(k in domain or k in topic for k in ["Vật", "VL", "Tốc độ", "Âm"]):
            user.physics_count += 1
        elif any(k in domain or k in topic for k in ["Hóa", "HH", "Nguyên tử"]):
            user.chemistry_count += 1
        elif any(k in domain or k in topic for k in ["Sinh", "SH", "Quang hợp"]):
            user.biology_count += 1

        cls.save_all_users(users)

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
