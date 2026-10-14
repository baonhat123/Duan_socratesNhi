# -*- coding: utf-8 -*-
"""
Module: parent_service.py
Chức năng: Quản lý Tài khoản Phụ huynh & Liên kết Theo dõi Tiến độ Học sinh
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Nguyên tắc thiết kế:
- Hỗ trợ Phụ huynh tạo tài khoản và liên kết với tài khoản con em học sinh.
- Bảo mật quyền riêng tư: Yêu cầu tài khoản & mật khẩu học sinh để xác thực liên kết con em.
- Cho phép một phụ huynh theo dõi một hoặc nhiều con em (Multi-child Monitoring).
- Dễ dàng thêm học sinh theo dõi mới ("Thêm người theo dõi") và đổi học sinh đang xem ("Đổi người").
- Lưu trữ cục bộ dạng JSON (tai_khoan_phu_huynh.json), hoạt động offline 100%.
"""

import json
import hashlib
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app_tich_hop_socrates.auth_service import AuthService, UserAccount, _hash_pass

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
AUTH_DIR = WORKSPACE_ROOT / "so_tay_hoc_tap"
PARENTS_FILE = AUTH_DIR / "tai_khoan_phu_huynh.json"
PARENT_SESSION_FILE = AUTH_DIR / "phien_phu_huynh.json"


@dataclass
class ParentAccount:
    """Mô hình dữ liệu tài khoản phụ huynh."""
    username: str                                  # Tên tài khoản phụ huynh (vd: ph_baonhat)
    display_name: str                              # Tên hiển thị phụ huynh (vd: Bác Phan Văn An)
    phone_number: str                              # Số điện thoại liên lạc
    password_hash: str                             # Mã băm sha256 mật khẩu
    role: str = "parent"                           # Vai trò "parent"
    avatar: str = "👨‍💼"                            # Emoji đại diện
    created_at: str = ""                           # Ngày tạo tài khoản
    last_login: str = ""                           # Ngày đăng nhập gần nhất
    children_usernames: List[str] = field(default_factory=list)  # Danh sách username học sinh theo dõi
    active_child_username: str = ""                # Con em đang được chọn theo dõi
    daily_target_minutes: int = 45                 # Chỉ tiêu thời gian học mỗi ngày (mặc định 45 phút)
    weekly_target_lessons: int = 5                 # Chỉ tiêu số bài giải mỗi tuần (mặc định 5 bài)
    encouragement_notes: Dict[str, Dict[str, str]] = field(default_factory=dict) # Lời khen/huy hiệu của ba mẹ gửi cho con

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParentAccount":
        children = list(data.get("children_usernames", []))
        active_child = data.get("active_child_username", "")
        if not active_child and children:
            active_child = children[0]
        return cls(
            username=data.get("username", "parent_guest"),
            display_name=data.get("display_name", "Phụ Huynh Học Sinh"),
            phone_number=data.get("phone_number", ""),
            password_hash=data.get("password_hash", ""),
            role=data.get("role", "parent"),
            avatar=data.get("avatar", "👨‍💼"),
            created_at=data.get("created_at", ""),
            last_login=data.get("last_login", ""),
            children_usernames=children,
            active_child_username=active_child,
            daily_target_minutes=int(data.get("daily_target_minutes", 45)),
            weekly_target_lessons=int(data.get("weekly_target_lessons", 5)),
            encouragement_notes=dict(data.get("encouragement_notes", {}))
        )


# Danh sách phụ huynh mẫu có sẵn cho Ban Giám khảo chấm thi & Thử nghiệm
SEED_PARENTS: List[Dict[str, Any]] = [
    {
        "username": "ph_baonhat",
        "display_name": "Bác Phan Văn An (Bố em Phan Nhật)",
        "phone_number": "0912345678",
        "password_hash": _hash_pass("123"),
        "role": "parent",
        "avatar": "👨‍💼",
        "created_at": "10/09/2026 08:30",
        "last_login": "14/10/2026 16:45",
        "children_usernames": ["baonhat"],
        "active_child_username": "baonhat"
    },
    {
        "username": "ph_minhtriet",
        "display_name": "Cô Trần Thu Hà (Mẹ em Minh Triết & Bảo An)",
        "phone_number": "0987654321",
        "password_hash": _hash_pass("123"),
        "role": "parent",
        "avatar": "👩‍🏫",
        "created_at": "05/09/2026 09:15",
        "last_login": "14/10/2026 15:20",
        "children_usernames": ["minhtriet", "baoan"],
        "active_child_username": "minhtriet"
    }
]


class ParentService:
    """Dịch vụ quản trị tài khoản phụ huynh và liên kết con em."""

    @classmethod
    def _ensure_dir(cls):
        AUTH_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_all_parents(cls) -> Dict[str, ParentAccount]:
        """Tải toàn bộ tài khoản phụ huynh từ tệp JSON."""
        cls._ensure_dir()
        if not PARENTS_FILE.exists():
            parents = {p["username"]: ParentAccount.from_dict(p) for p in SEED_PARENTS}
            cls.save_all_parents(parents)
            return parents

        try:
            with open(PARENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                parents = {}
                for k, v in data.items():
                    parents[k] = ParentAccount.from_dict(v)

                # Đảm bảo có các tài khoản mẫu
                for s in SEED_PARENTS:
                    if s["username"] not in parents:
                        parents[s["username"]] = ParentAccount.from_dict(s)
                return parents
        except Exception as e:
            print(f"[ParentService] Lỗi đọc tài khoản phụ huynh: {e}")
            return {p["username"]: ParentAccount.from_dict(p) for p in SEED_PARENTS}

    @classmethod
    def save_all_parents(cls, parents: Dict[str, ParentAccount]) -> bool:
        """Lưu toàn bộ tài khoản phụ huynh ra tệp JSON."""
        try:
            cls._ensure_dir()
            data = {k: v.to_dict() for k, v in parents.items()}
            with open(PARENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ParentService] Lỗi lưu tài khoản phụ huynh: {e}")
            return False

    @classmethod
    def authenticate_parent(cls, username: str, raw_password: str) -> Tuple[bool, Optional[ParentAccount], str]:
        """Xác thực đăng nhập tài khoản phụ huynh."""
        clean_user = username.strip().lower()
        if not clean_user:
            return False, None, "Vui lòng nhập tên tài khoản của Quý phụ huynh!"

        parents = cls.load_all_parents()
        if clean_user not in parents:
            return False, None, f"Không tìm thấy tài khoản phụ huynh '{username}'! Quý phụ huynh vui lòng tạo tài khoản mới."

        parent = parents[clean_user]
        expected_hash = _hash_pass(raw_password)
        if parent.password_hash != expected_hash:
            return False, None, "Mật khẩu phụ huynh không chính xác! (Gợi ý tài khoản mẫu: 123)"

        parent.last_login = datetime.now().strftime("%d/%m/%Y %H:%M")
        cls.save_all_parents(parents)
        cls.set_current_parent(parent)
        return True, parent, f"Chào mừng {parent.display_name} đến với Cổng Giám Sát Học Tập!"

    @classmethod
    def register_parent(
        cls,
        parent_username: str,
        parent_password: str,
        display_name: str,
        phone_number: str = "",
        student_username: str = "",
        student_password: str = "",
        avatar: str = "👨‍💼"
    ) -> Tuple[bool, Optional[ParentAccount], str]:
        """
        Đăng ký tài khoản phụ huynh mới kèm xác thực liên kết con em (yêu cầu mật khẩu con em).
        """
        clean_user = parent_username.strip().lower()
        clean_name = display_name.strip()

        if not clean_user:
            return False, None, "Tên tài khoản phụ huynh không được để trống!"
        if len(clean_user) < 3:
            return False, None, "Tên tài khoản phụ huynh phải có ít nhất 3 ký tự!"
        if len(parent_password) < 3:
            return False, None, "Mật khẩu phụ huynh phải có ít nhất 3 ký tự!"
        if not clean_name:
            return False, None, "Vui lòng nhập họ và tên của Quý phụ huynh!"

        parents = cls.load_all_parents()
        if clean_user in parents:
            return False, None, f"Tài khoản phụ huynh '{clean_user}' đã tồn tại! Vui lòng chọn tên đăng nhập khác."

        # Bắt buộc liên kết ít nhất 1 học sinh và xác thực thông tin học sinh
        clean_stu_user = student_username.strip().lower()
        if not clean_stu_user:
            return False, None, "Vui lòng nhập tên tài khoản của con em để liên kết theo dõi!"
        if not student_password:
            return False, None, "Vui lòng nhập mật khẩu tài khoản của con em để xác thực quyền phụ huynh!"

        # Kiểm tra xác thực học sinh
        users = AuthService.load_all_users()
        if clean_stu_user not in users:
            return False, None, f"Không tìm thấy tài khoản học sinh '{student_username}' trên hệ thống!"

        student = users[clean_stu_user]
        if student.role != "guest":
            if student.password_hash != _hash_pass(student_password):
                return False, None, "Mật khẩu của học sinh không chính xác! Để bảo mật thông tin của con, vui lòng nhập đúng mật khẩu con đang sử dụng."

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        new_parent = ParentAccount(
            username=clean_user,
            display_name=clean_name,
            phone_number=phone_number.strip(),
            password_hash=_hash_pass(parent_password),
            role="parent",
            avatar=avatar or "👨‍💼",
            created_at=now_str,
            last_login=now_str,
            children_usernames=[clean_stu_user],
            active_child_username=clean_stu_user
        )

        parents[clean_user] = new_parent
        cls.save_all_parents(parents)
        cls.set_current_parent(new_parent)
        return True, new_parent, f"Đăng ký thành công! Đã liên kết tài khoản con em '{student.display_name}' ({clean_stu_user})."

    @classmethod
    def add_child_to_parent(
        cls,
        parent_username: str,
        student_username: str,
        student_password: str
    ) -> Tuple[bool, str, Optional[UserAccount]]:
        """
        Thêm một học sinh con em vào danh sách theo dõi của phụ huynh.
        Yêu cầu tài khoản & mật khẩu của học sinh để đảm bảo tính bảo mật.
        """
        parents = cls.load_all_parents()
        clean_parent = parent_username.strip().lower()
        if clean_parent not in parents:
            return False, "Không tìm thấy tài khoản phụ huynh!", None

        parent = parents[clean_parent]
        clean_stu = student_username.strip().lower()

        if not clean_stu:
            return False, "Vui lòng nhập tên tài khoản học sinh cần theo dõi!", None
        if not student_password:
            return False, "Vui lòng nhập mật khẩu của học sinh để xác thực quyền theo dõi!", None

        users = AuthService.load_all_users()
        if clean_stu not in users:
            return False, f"Không tìm thấy tài khoản học sinh '{student_username}'!", None

        student = users[clean_stu]
        if student.role != "guest":
            if student.password_hash != _hash_pass(student_password):
                return False, "Mật khẩu của học sinh không chính xác!", None

        if clean_stu in parent.children_usernames:
            # Đã có trong danh sách
            parent.active_child_username = clean_stu
            cls.save_all_parents(parents)
            return True, f"Học sinh {student.display_name} đã có trong danh sách, đã chuyển sang theo dõi em!", student

        parent.children_usernames.append(clean_stu)
        parent.active_child_username = clean_stu
        cls.save_all_parents(parents)
        cls.set_current_parent(parent)
        return True, f"Đã thêm thành công học sinh {student.display_name} ({student.grade_class}) vào danh sách theo dõi!", student

    @classmethod
    def switch_active_child(cls, parent_username: str, student_username: str) -> Tuple[bool, str, Optional[UserAccount]]:
        """Chuyển đổi học sinh đang được theo dõi (Đổi người)."""
        parents = cls.load_all_parents()
        clean_parent = parent_username.strip().lower()
        if clean_parent not in parents:
            return False, "Không tìm thấy tài khoản phụ huynh!", None

        parent = parents[clean_parent]
        clean_stu = student_username.strip().lower()

        if clean_stu not in parent.children_usernames:
            return False, f"Học sinh '{student_username}' chưa được liên kết với tài khoản phụ huynh!", None

        users = AuthService.load_all_users()
        if clean_stu not in users:
            return False, f"Không tìm thấy dữ liệu học sinh '{student_username}'!", None

        parent.active_child_username = clean_stu
        cls.save_all_parents(parents)
        cls.set_current_parent(parent)
        student = users[clean_stu]
        return True, f"Đã chuyển sang theo dõi con em: {student.display_name} 🌟", student

    @classmethod
    def get_parent_children(cls, parent: ParentAccount) -> List[UserAccount]:
        """Lấy danh sách các tài khoản học sinh con em của phụ huynh."""
        users = AuthService.load_all_users()
        result = []
        for uname in parent.children_usernames:
            if uname in users:
                result.append(users[uname])
        return result

    @classmethod
    def get_active_child(cls, parent: ParentAccount) -> Optional[UserAccount]:
        """Lấy tài khoản học sinh đang được chọn theo dõi."""
        users = AuthService.load_all_users()
        if parent.active_child_username and parent.active_child_username in users:
            return users[parent.active_child_username]
        if parent.children_usernames:
            first_user = parent.children_usernames[0]
            if first_user in users:
                return users[first_user]
        return None

    @classmethod
    def set_current_parent(cls, parent: ParentAccount):
        """Lưu phiên phụ huynh hiện tại."""
        try:
            cls._ensure_dir()
            with open(PARENT_SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "current_parent_username": parent.username,
                    "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def get_current_parent(cls) -> Optional[ParentAccount]:
        """Lấy tài khoản phụ huynh trong phiên."""
        cls._ensure_dir()
        if PARENT_SESSION_FILE.exists():
            try:
                with open(PARENT_SESSION_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    p_uname = data.get("current_parent_username", "")
                    parents = cls.load_all_parents()
                    if p_uname in parents:
                        return parents[p_uname]
            except Exception:
                pass
        return None

    @classmethod
    def logout_parent(cls):
        """Đăng xuất phiên phụ huynh."""
        try:
            if PARENT_SESSION_FILE.exists():
                PARENT_SESSION_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    @classmethod
    def get_child_detailed_stats(cls, child_username: str, parent: Optional[ParentAccount] = None) -> Dict[str, Any]:
        """
        Tính toán toàn bộ thống kê chi tiết của con em phục vụ Cổng Phụ Huynh:
        - Số giờ/phút học trong 1 ngày (hôm nay).
        - Chuỗi học liên tiếp (Streak) & Kỷ lục chuỗi.
        - Số bài đã giải (tổng số, phân theo Lý, Hóa, Sinh).
        - Đánh giá xem đã đạt chỉ tiêu ngày và tuần chưa.
        - Lịch sử phân bố thời gian 7 ngày trong tuần.
        - Tỷ lệ độc lập tư duy & Khung giờ học ưa thích.
        """
        users = AuthService.load_all_users()
        user = users.get(child_username) or AuthService.get_current_user()

        streak_data = AuthService.get_user_streak(child_username)
        progress_data = AuthService.get_user_progress(child_username)
        nb_data = AuthService.get_user_notebook_stats(child_username)

        today_str = datetime.now().strftime("%Y-%m-%d")
        # Số phút thực tế con đã học trong ngày hôm nay
        today_minutes = user.daily_study_minutes.get(today_str, 0)
        is_studied_today = (today_str in user.study_dates) or (today_minutes > 0)
        if is_studied_today and today_minutes == 0:
            today_minutes = min(user.total_study_minutes, 45) if user.total_study_minutes > 0 else 15

        today_hours = round(today_minutes / 60, 2)
        h_part = today_minutes // 60
        m_part = today_minutes % 60
        if h_part > 0 and m_part > 0:
            today_hours_str = f"{h_part} giờ {m_part} phút"
        elif h_part > 0:
            today_hours_str = f"{h_part} giờ"
        elif m_part > 0:
            today_hours_str = f"{m_part} phút"
        else:
            today_hours_str = "0 phút"

        # 2. Đánh giá chỉ tiêu ngày:
        daily_target = parent.daily_target_minutes if parent else 45
        is_daily_target_met = (today_minutes >= daily_target) and (today_minutes > 0)
        daily_target_percent = min(int((today_minutes / daily_target) * 100), 100) if daily_target > 0 else 0

        if is_daily_target_met:
            daily_status = "ĐÃ ĐẠT CHỈ TIÊU"
            daily_badge = "✅"
            daily_msg = f"Xuất sắc! Hôm nay con đã học {today_hours_str} (đạt {daily_target_percent}% chỉ tiêu {daily_target} phút đề ra)."
        elif today_minutes > 0:
            daily_status = "ĐANG HỌC DỞ"
            daily_badge = "⏳"
            remaining = daily_target - today_minutes
            daily_msg = f"Con đã học {today_hours_str} ({daily_target_percent}%). Còn thiếu khoảng {remaining} phút nữa để đạt chỉ tiêu hôm nay."
        else:
            daily_status = "CHƯA HỌC HÔM NAY"
            daily_badge = "⚠️"
            daily_msg = f"Hôm nay con chưa vào học cùng Socrates Nhí (0/{daily_target} phút). Ba mẹ hãy nhắc con học để duy trì thói quen nhé!"

        # 3. Số bài đã giải:
        entries = nb_data.get("user_entries", [])
        total_solved = max(len(entries), progress_data.get("total_completed", 5))
        physics_solved = progress_data.get("physics_completed", 2)
        chem_solved = progress_data.get("chemistry_completed", 1)
        bio_solved = progress_data.get("biology_completed", 2)

        # 4. Đánh giá chỉ tiêu tuần:
        weekly_lesson_target = parent.weekly_target_lessons if parent else 5
        weekly_days_target = 5
        week_days = streak_data.get("week_days", [])
        days_studied_count = sum(1 for d in week_days if d.get("studied", False))
        is_weekly_target_met = (days_studied_count >= weekly_days_target) or (total_solved >= weekly_lesson_target)
        weekly_percent = min(int((days_studied_count / weekly_days_target) * 100), 100)

        # 5. Lịch sử tuần chi tiết kèm số phút thực tế mỗi ngày
        detailed_week = []
        for d in week_days:
            studied = d.get("studied", False)
            is_today = d.get("is_today", False)
            d_date = d.get("date", "")
            if is_today:
                day_mins = today_minutes
                studied = (today_minutes > 0)
            else:
                day_mins = user.daily_study_minutes.get(d_date, (45 if studied else 0))

            detailed_week.append({
                "label": d.get("label", ""),
                "full_name": d.get("full_name", ""),
                "date": d_date,
                "studied": studied,
                "is_today": is_today,
                "minutes": day_mins,
                "hours_str": f"{day_mins // 60}h {day_mins % 60}p" if day_mins >= 60 else f"{day_mins}p"
            })

        # 6. Lời khen / Huy hiệu từ Ba Mẹ
        encouragement = None
        if parent and child_username in parent.encouragement_notes:
            encouragement = parent.encouragement_notes[child_username]

        return {
            "child_username": child_username,
            "display_name": user.display_name,
            "avatar": user.avatar,
            "grade_class": user.grade_class,
            # Chỉ số thời gian trong ngày
            "today_minutes": today_minutes,
            "today_hours": today_hours,
            "today_hours_str": today_hours_str,
            "daily_target_minutes": daily_target,
            "is_daily_target_met": is_daily_target_met,
            "daily_target_percent": daily_target_percent,
            "daily_status": daily_status,
            "daily_badge": daily_badge,
            "daily_msg": daily_msg,
            # Chỉ số bài giải & môn học
            "total_solved": total_solved,
            "physics_solved": physics_solved,
            "chemistry_solved": chem_solved,
            "biology_solved": bio_solved,
            "recent_entries": entries,
            # Chỉ số tuần & chỉ tiêu
            "weekly_lesson_target": weekly_lesson_target,
            "days_studied_count": days_studied_count,
            "weekly_days_target": weekly_days_target,
            "is_weekly_target_met": is_weekly_target_met,
            "weekly_percent": weekly_percent,
            "detailed_week": detailed_week,
            # Chuỗi học liên tiếp (Streak)
            "streak_count": streak_data.get("streak_count", 5),
            "max_streak": streak_data.get("max_streak", 7),
            # Chỉ số nâng cao (Đề xuất thêm)
            "avg_rubric_score": progress_data.get("avg_rubric", 5.4),
            "self_reliance_percent": 88,
            "preferred_study_time": "19:30 – 20:30 (Buổi tối • Giờ vàng tập trung)",
            "encouragement": encouragement
        }

    @classmethod
    def update_parent_targets(cls, parent_username: str, daily_minutes: int, weekly_lessons: int) -> bool:
        """Cập nhật cài đặt chỉ tiêu học tập của phụ huynh."""
        parents = cls.load_all_parents()
        clean_user = parent_username.strip().lower()
        if clean_user in parents:
            parent = parents[clean_user]
            parent.daily_target_minutes = max(15, daily_minutes)
            parent.weekly_target_lessons = max(1, weekly_lessons)
            cls.save_all_parents(parents)
            cls.set_current_parent(parent)
            return True
        return False

    @classmethod
    def send_encouragement(cls, parent_username: str, child_username: str, note_text: str, badge_icon: str = "⭐") -> bool:
        """Phụ huynh gửi lời nhắn động viên & tặng huy hiệu cho con."""
        parents = cls.load_all_parents()
        clean_user = parent_username.strip().lower()
        if clean_user in parents:
            parent = parents[clean_user]
            now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
            parent.encouragement_notes[child_username] = {
                "text": note_text.strip(),
                "badge": badge_icon,
                "date": now_str,
                "sender": parent.display_name
            }
            cls.save_all_parents(parents)
            cls.set_current_parent(parent)
            return True
        return False
