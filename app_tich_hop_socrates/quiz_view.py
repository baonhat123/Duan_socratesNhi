# -*- coding: utf-8 -*-
"""
Module: quiz_view.py
Chức năng: Giao diện Hộp Thoại Làm Bài Kiểm Tra Củng Cố Kiến Thức (Trắc Nghiệm & Tự Luận)
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Trải nghiệm học tập:
- Trực quan, thân thiện với học sinh THCS.
- Gồm 3 câu trắc nghiệm (chọn 1 trong 4) + 1 câu tự luận mở ứng dụng thực tế đời sống.
- Chấm điểm tức thì, giải thích chi tiết đáp án và phản hồi sư phạm ân cần từ Socrates.
"""

import threading
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List
import flet as ft

from app_tich_hop_socrates.auth_service import AuthService, UserAccount
from app_tich_hop_socrates.quiz_service import QuizService, QuizQuestion, QuizRecord
from app_tich_hop_socrates.dashboard_view import safe_open_dialog, safe_close_dialog


class QuizModalDialog:
    """
    Hộp thoại làm bài kiểm tra củng cố kiến thức hoặc ôn tập ngắt quãng.
    Tích hợp tạo đề bằng AI bám sát câu hỏi của học sinh & dữ liệu Internet chuẩn SGK KHTN 7.
    """
    def __init__(
        self,
        page: ft.Page,
        topic: str,
        strand: str = "Khoa học Tự nhiên 7",
        quiz_type: str = "post_lesson",  # "pre_test", "post_lesson", "post_test", "daily_review"
        pre_record: Optional[QuizRecord] = None,
        on_completed: Optional[Callable[[QuizRecord], None]] = None,
        initial_record: Optional[QuizRecord] = None,
        problem_text: str = "",
        auto_generate_ai: bool = True
    ):
        self.page = page
        self.topic = topic
        self.strand = strand
        self.quiz_type = quiz_type
        self.pre_record = pre_record
        self.on_completed = on_completed
        self.initial_record = initial_record
        self.problem_text = (problem_text or "").strip()
        self.auto_generate_ai = auto_generate_ai
        self.dialog: Optional[ft.AlertDialog] = None
        self.is_ai_generated: bool = False
        self.is_loading_ai: bool = False

        # Tự động liên kết Pre-test từ lịch sử nếu chưa được truyền vào
        if not self.pre_record and self.quiz_type in ["post_lesson", "post_test"]:
            try:
                cur_user = AuthService.get_current_user()
                if cur_user and cur_user.username:
                    hist = QuizService.get_student_records(cur_user.username)
                    for r in hist:
                        if r.quiz_type == "pre_test" and (r.topic == topic or r.strand == strand):
                            self.pre_record = r
                            break
            except Exception:
                pass

        # Nạp câu hỏi ban đầu (offline fallback tức thì để không bị trễ giao diện)
        self.questions: List[QuizQuestion] = QuizService.get_quiz_for_problem(
            problem_text=self.problem_text,
            topic=self.topic,
            strand=self.strand,
            quiz_type=self.quiz_type,
            use_ai=False
        )

        # Kiểm tra nếu online và có bài toán thì kích hoạt cờ tạo đề AI tự động
        if not initial_record and self.auto_generate_ai and (self.problem_text or self.topic):
            try:
                from app_tich_hop_socrates.ai_service import get_ai_config
                from chuc_nang_7_demo_offline_cache.offline_engine import GLOBAL_OFFLINE_ENGINE
                cfg = get_ai_config()
                if not GLOBAL_OFFLINE_ENGINE.is_offline() and cfg.get("has_key"):
                    self.is_loading_ai = True
            except Exception:
                self.is_loading_ai = False

        self.mcq_answers: Dict[str, int] = {}  # question_id -> chosen_index
        self.txt_essay = ft.TextField(
            multiline=True,
            min_lines=3,
            max_lines=5,
            hint_text="Em hãy tự tin gõ lời giải thích khoa học của mình vào đây...",
            border_color=ft.Colors.INDIGO_300,
            text_size=12
        )

        # Trạng thái giao diện: "taking" (đang làm bài) hoặc "result" (đã chấm điểm)
        if initial_record:
            self.current_state = "result"
            self.graded_record = initial_record
            if initial_record.pre_test_score is not None and not self.pre_record:
                # Tạo mock pre-record nhỏ để hiển thị so sánh nếu có điểm
                self.pre_record = QuizRecord(
                    quiz_id="PRE_HIST",
                    username=initial_record.username,
                    student_name=initial_record.student_name,
                    topic=self.topic,
                    strand=self.strand,
                    quiz_type="pre_test",
                    created_at=initial_record.created_at,
                    score=initial_record.pre_test_score,
                    total_mcq=3,
                    correct_mcq=int(initial_record.pre_test_score / 2),
                    essay_score=0.0,
                    essay_feedback="",
                    student_essay_answer="",
                    badge_earned="Khảo sát",
                    details=[]
                )
        else:
            self.current_state = "taking"
            self.graded_record = None

        self.streak_result: Dict[str, Any] = {}
        self.content_area = ft.Container()

    def show(self):
        """Hiển thị hộp thoại làm bài kiểm tra."""
        self._render_content()

        if self.quiz_type == "pre_test":
            title_icon = ft.Icons.CENTER_FOCUS_STRONG_ROUNDED
            title_text = "Khảo Sát Trình Độ Đầu Vào (Pre-test) 🎯"
        elif self.quiz_type in ["post_lesson", "post_test"]:
            title_icon = ft.Icons.ASSESSMENT_ROUNDED
            title_text = "Kiểm Tra Lại Trình Độ Sau Bài Học (Post-test) 📝"
        else:
            title_icon = ft.Icons.REPLAY_CIRCLE_FILLED_ROUNDED
            title_text = "Thử Thách Ôn Tập Ngày Mới 🔁"

        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(title_icon, color=ft.Colors.INDIGO_700, size=24),
                ft.Column([
                    ft.Text(title_text, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Text(f"Chủ đề: {self.topic} • {self.strand}", size=11, color=ft.Colors.GREY_600)
                ], spacing=1)
            ], spacing=10),
            content=ft.Container(
                content=self.content_area,
                width=720,
                height=560,
                padding=ft.Padding(4, 0, 4, 0)
            ),
            actions=[self._build_actions()],
            actions_alignment=ft.MainAxisAlignment.END
        )

        safe_open_dialog(self.page, self.dialog)

        # Nếu đang ở chế độ chờ AI soạn đề, kích hoạt luồng ngầm qua Flet thread pool
        if self.is_loading_ai:
            self._start_ai_fetch()

    def _start_ai_fetch(self):
        """Kích hoạt tác vụ tạo đề AI an toàn trên Flet thread pool để giao diện cập nhật tức thì."""
        if hasattr(self.page, "run_thread") and callable(getattr(self.page, "run_thread")):
            self.page.run_thread(self._async_fetch_ai_quiz)
        else:
            threading.Thread(target=self._async_fetch_ai_quiz, daemon=True).start()

    def _update_dialog_ui(self):
        """Ép cập nhật giao diện hộp thoại lập tức trên cả cây widget của Flutter."""
        self._render_content()
        if self.dialog:
            self.dialog.actions = [self._build_actions()]
            try:
                if self.page:
                    self.page.update(self.dialog)
            except Exception:
                pass
            try:
                self.dialog.update()
            except Exception:
                pass
        try:
            self.content_area.update()
        except Exception:
            pass
        if hasattr(self.page, "_dialogs") and self.page._dialogs:
            try:
                self.page._dialogs.update()
            except Exception:
                pass
        try:
            if self.page:
                self.page.update()
        except Exception:
            pass

    def _async_fetch_ai_quiz(self):
        """Luồng ngầm gọi AI tạo đề bám sát câu hỏi & học liệu KHTN trên Internet."""
        try:
            ai_qs = QuizService.generate_quiz_via_ai(
                problem_text=self.problem_text,
                topic=self.topic,
                strand=self.strand,
                quiz_type=self.quiz_type
            )
            if ai_qs and len(ai_qs) >= 3:
                self.questions = ai_qs
                self.is_ai_generated = True
                self.mcq_answers.clear()
        except Exception as e:
            print(f"[QuizModalDialog] Lỗi gọi AI tạo đề: {e}")
        finally:
            self.is_loading_ai = False
            self._update_dialog_ui()

    def _trigger_manual_ai_generation(self):
        """Học sinh chủ động bấm đổi đề câu hỏi mới bằng AI."""
        self.is_loading_ai = True
        self.mcq_answers.clear()
        self._update_dialog_ui()
        self._start_ai_fetch()

    def _cancel_loading_and_use_offline(self):
        """Học sinh không muốn chờ AI và muốn làm ngay với đề SGK chuẩn."""
        self.is_loading_ai = False
        self._update_dialog_ui()

    def _render_content(self):
        """Vẽ lại nội dung theo trạng thái đang làm bài hoặc màn hình kết quả."""
        if self.current_state == "taking":
            self.content_area.content = self._build_taking_view()
        else:
            self.content_area.content = self._build_result_view()

    def _build_taking_view(self) -> ft.Control:
        """Xây dựng giao diện danh sách câu hỏi làm bài."""
        if self.is_loading_ai:
            prob_preview = (self.problem_text[:75] + "...") if len(self.problem_text) > 75 else (self.problem_text or self.topic)
            return ft.Container(
                content=ft.Column([
                    ft.Container(height=45),
                    ft.ProgressRing(width=48, height=48, stroke_width=3.5, color=ft.Colors.INDIGO_700),
                    ft.Container(height=12),
                    ft.Text("✨ Socrates AI Đang Soạn Đề Theo Đúng Câu Hỏi Của Em", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Text(
                        "Hệ thống đang phân tích bản chất khoa học và tham khảo ngân hàng câu hỏi KHTN 7 chuẩn từ Internet...",
                        size=12,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=ft.Colors.GREEN_700, size=16),
                            ft.Text(f"Bài toán: \"{prob_preview}\"", size=11, color=ft.Colors.GREEN_900, italic=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                        bgcolor=ft.Colors.GREEN_50,
                        padding=ft.Padding(12, 6, 12, 6),
                        border_radius=8,
                        border=ft.Border.all(1, ft.Colors.GREEN_200)
                    ),
                    ft.Container(height=18),
                    ft.OutlinedButton(
                        "Làm ngay với đề chuẩn SGK Offline (Không cần đợi) ⚡",
                        icon=ft.Icons.FLASH_ON_ROUNDED,
                        style=ft.ButtonStyle(color=ft.Colors.INDIGO_800),
                        on_click=lambda _: self._cancel_loading_and_use_offline()
                    ),
                    ft.Container(height=45)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                alignment=ft.Alignment.CENTER,
                padding=20
            )

        items: List[ft.Control] = []
        is_pre = (self.quiz_type == "pre_test")

        # Banner chỉ dẫn
        banner_bg = ft.Colors.BLUE_50 if is_pre else ft.Colors.AMBER_50
        banner_border = ft.Colors.BLUE_300 if is_pre else ft.Colors.AMBER_300
        banner_icon = ft.Icons.CENTER_FOCUS_STRONG_ROUNDED if is_pre else ft.Icons.LIGHTBULB_ROUNDED
        banner_icon_c = ft.Colors.BLUE_700 if is_pre else ft.Colors.AMBER_800
        banner_title = "KHẢO SÁT TRÌNH ĐỘ BAN ĐẦU (PRE-TEST 2 PHÚT) 🎯" if is_pre else "MỤC TIÊU BÀI KIỂM TRA NĂNG LỰC:"
        banner_desc = (
            "Gồm 3 câu trắc nghiệm nhanh để Socrates hiểu mức độ hiểu biết của em trước bài học. Đừng lo lắng nếu chưa biết làm, hãy chọn theo suy nghĩ tự nhiên của em nhé!"
            if is_pre
            else "Gồm 3 câu trắc nghiệm (6.0đ) + 1 câu tự luận vận dụng thực tế (4.0đ). Hãy vận dụng kiến thức vừa học cùng Socrates để giải bài nhé!"
        )

        banner = ft.Container(
            content=ft.Row([
                ft.Icon(banner_icon, color=banner_icon_c, size=22),
                ft.Column([
                    ft.Text(banner_title, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Text(banner_desc, size=10, color=ft.Colors.GREY_800)
                ], spacing=2, expand=True)
            ], spacing=8),
            bgcolor=banner_bg,
            padding=10,
            border_radius=10,
            border=ft.Border.all(1, banner_border)
        )
        items.append(banner)

        # AI Generation Badge & Re-roll Button
        ai_badge = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.AUTO_AWESOME_ROUNDED if self.is_ai_generated else ft.Icons.MENU_BOOK_ROUNDED,
                    color=ft.Colors.PURPLE_700 if self.is_ai_generated else ft.Colors.BLUE_700,
                    size=16
                ),
                ft.Text(
                    "✨ Đề thi do AI Socrates tạo tự động bám sát bài toán & học liệu Internet"
                    if self.is_ai_generated
                    else "📚 Bộ câu hỏi khảo sát chuẩn SGK KHTN 7 theo đúng chủ đề",
                    size=11,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.PURPLE_900 if self.is_ai_generated else ft.Colors.BLUE_900,
                    expand=True
                ),
                ft.TextButton(
                    "🔄 Đổi đề bằng AI" if self.is_ai_generated else "✨ Soạn lại bằng AI",
                    icon=ft.Icons.REFRESH_ROUNDED if self.is_ai_generated else ft.Icons.AUTO_AWESOME_ROUNDED,
                    style=ft.ButtonStyle(color=ft.Colors.PURPLE_800 if self.is_ai_generated else ft.Colors.INDIGO_800),
                    on_click=lambda _: self._trigger_manual_ai_generation()
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.PURPLE_50 if self.is_ai_generated else ft.Colors.BLUE_50,
            padding=ft.Padding(10, 4, 10, 4),
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.PURPLE_200 if self.is_ai_generated else ft.Colors.BLUE_200)
        )
        items.append(ai_badge)
        items.append(ft.Container(height=4))

        # Hiển thị từng câu hỏi
        mcq_idx = 1
        for q in self.questions:
            if q.q_type == "mcq":
                card = self._build_mcq_card(q, mcq_idx, is_pre=is_pre)
                items.append(card)
                items.append(ft.Container(height=8))
                mcq_idx += 1
            elif not is_pre:
                card = self._build_essay_card(q)
                items.append(card)
                items.append(ft.Container(height=8))

        return ft.Column(items, spacing=4, scroll=ft.ScrollMode.AUTO)

    def _build_mcq_card(self, q: QuizQuestion, index: int, is_pre: bool = False) -> ft.Container:
        """Thẻ câu hỏi trắc nghiệm kèm 4 phương án A, B, C, D."""
        option_containers: List[ft.Container] = []
        point_str = "Nhận biết ban đầu (3.3đ)" if is_pre else "Trắc nghiệm (2.0 điểm)"

        for opt_idx, opt_text in enumerate(q.options):
            is_selected = (self.mcq_answers.get(q.question_id) == opt_idx)

            def make_click_handler(question_id=q.question_id, o_idx=opt_idx):
                def handler(_):
                    self.mcq_answers[question_id] = o_idx
                    self._render_content()
                    self.page.update()
                return handler

            opt_chip = ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(chr(65 + opt_idx), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_selected else ft.Colors.INDIGO_900),
                        width=22,
                        height=22,
                        border_radius=11,
                        bgcolor=ft.Colors.INDIGO_700 if is_selected else ft.Colors.INDIGO_100,
                        alignment=ft.Alignment.CENTER
                    ),
                    ft.Text(opt_text[3:] if len(opt_text) > 3 and opt_text[1] == "." else opt_text, size=11, color=ft.Colors.INDIGO_900 if is_selected else ft.Colors.GREY_800, expand=True)
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.INDIGO_50 if is_selected else ft.Colors.WHITE,
                border=ft.Border.all(1.5 if is_selected else 1, ft.Colors.INDIGO_600 if is_selected else ft.Colors.GREY_300),
                border_radius=10,
                padding=ft.Padding(10, 8, 10, 8),
                on_click=make_click_handler(),
                ink=True
            )
            option_containers.append(opt_chip)

        card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"Câu {index}", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800),
                        bgcolor=ft.Colors.INDIGO_100,
                        padding=ft.Padding(6, 2, 6, 2),
                        border_radius=6
                    ),
                    ft.Text(point_str, size=10, italic=True, color=ft.Colors.GREY_600)
                ], spacing=6),
                ft.Text(q.prompt, size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_900),
                ft.Column(option_containers, spacing=6)
            ], spacing=6),
            bgcolor=ft.Colors.WHITE,
            padding=12,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.02, ft.Colors.BLACK), offset=ft.Offset(0, 1))
        )
        return card

    def _build_essay_card(self, q: QuizQuestion) -> ft.Container:
        """Thẻ câu hỏi tự luận mở ứng dụng thực tế."""
        hint_box = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, color=ft.Colors.TEAL_700, size=15),
                ft.Text(f"Gợi ý tư duy từ Socrates: {q.hint}", size=10, italic=True, color=ft.Colors.TEAL_900, expand=True)
            ], spacing=6),
            bgcolor=ft.Colors.TEAL_50,
            padding=8,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.TEAL_200)
        )

        card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text("Câu 4", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800),
                        bgcolor=ft.Colors.PURPLE_100,
                        padding=ft.Padding(6, 2, 6, 2),
                        border_radius=6
                    ),
                    ft.Text("Tự luận vận dụng thực tế (4.0 điểm)", size=10, italic=True, color=ft.Colors.PURPLE_700)
                ], spacing=6),
                ft.Text(q.prompt, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                hint_box,
                self.txt_essay
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=12,
            border_radius=12,
            border=ft.Border.all(1.5, ft.Colors.PURPLE_200),
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.02, ft.Colors.BLACK), offset=ft.Offset(0, 1))
        )
        return card

    def _build_result_view(self) -> ft.Control:
        """Xây dựng màn hình kết quả điểm số, đối chứng Pre vs Post và phân tích sư phạm."""
        rec = self.graded_record
        if not rec:
            return ft.Text("Không có dữ liệu kết quả.")

        is_pre = (self.quiz_type == "pre_test")
        score_color = ft.Colors.GREEN_700 if rec.score >= 8.0 else (ft.Colors.AMBER_800 if rec.score >= 5.0 else ft.Colors.BLUE_700)
        score_bg = ft.Colors.GREEN_50 if rec.score >= 8.0 else (ft.Colors.AMBER_50 if rec.score >= 5.0 else ft.Colors.BLUE_50)

        header_score_card = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"{rec.score:.1f}", size=36, weight=ft.FontWeight.BOLD, color=score_color),
                        ft.Text("TRÊN 10 ĐIỂM", size=9, weight=ft.FontWeight.BOLD, color=score_color)
                    ], spacing=0, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=90,
                    height=90,
                    border_radius=45,
                    bgcolor=score_bg,
                    border=ft.Border.all(2, score_color),
                    alignment=ft.Alignment.CENTER
                ),
                ft.Column([
                    ft.Row([
                        ft.Text(rec.badge_earned, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ft.Container(
                            content=ft.Text(
                                "Khảo Sát Đầu Vào 🎯" if is_pre else f"Đúng {rec.correct_mcq}/{rec.total_mcq} trắc nghiệm",
                                size=10,
                                color=ft.Colors.INDIGO_800
                            ),
                            bgcolor=ft.Colors.INDIGO_100,
                            padding=ft.Padding(6, 2, 6, 2),
                            border_radius=6
                        )
                    ], spacing=8),
                    ft.Text(f"Học sinh: {rec.student_name} (@{rec.username})", size=11, color=ft.Colors.GREY_700),
                    ft.Text(
                        "• Socrates đã ghi nhận trình độ ban đầu để định hướng câu hỏi gợi mở phù hợp 💡"
                        if is_pre
                        else "• Kết quả bài kiểm tra này đã được lưu vào Sổ tay Tự học và đồng bộ sang Cổng Phụ Huynh 👨‍👩‍👧‍👦",
                        size=10,
                        color=ft.Colors.BLUE_800 if is_pre else ft.Colors.GREEN_800,
                        italic=True
                    )
                ], spacing=3, expand=True)
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=16,
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.GREY_300)
        )

        detail_items: List[ft.Control] = [header_score_card]

        # BẢNG ĐỐI CHỨNG TIẾN BỘ NĂNG LỰC (PRE-TEST vs POST-TEST LEARNING GAIN)
        if not is_pre:
            has_pre = (rec.pre_test_score is not None or self.pre_record is not None)
            if has_pre:
                pre_val = rec.pre_test_score if rec.pre_test_score is not None else self.pre_record.score
                diff_val = rec.learning_gain if rec.learning_gain is not None else round(rec.score - pre_val, 1)
                diff_str = f"+{diff_val} điểm" if diff_val > 0 else f"{diff_val} điểm"
                gain_color = ft.Colors.GREEN_700 if diff_val > 0 else ft.Colors.AMBER_800
                hake_pct = rec.gain_percent if rec.gain_percent is not None else (round((diff_val / max(0.1, 10.0 - pre_val)) * 100, 1) if diff_val > 0 else 0.0)

                comparison_card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.TRENDING_UP_ROUNDED, color=ft.Colors.INDIGO_700, size=20),
                            ft.Text("BẢNG ĐỐI CHỨNG TIẾN BỘ NĂNG LỰC (PRE vs POST) 📊", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                            ft.Container(
                                content=ft.Text(f"ĐỘ TĂNG TIẾN BỘ: {diff_str} 🚀", size=9.5, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=gain_color,
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=6
                            )
                        ], spacing=6),
                        ft.Row([
                            # Cột 1: Đầu vào Pre-test
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("1. ĐẦU VÀO (PRE-TEST) 🎯", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                                    ft.Text(f"{pre_val:.1f} / 10đ", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                                    ft.Text("Trình độ trước bài học", size=9.5, color=ft.Colors.GREY_600)
                                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.BLUE_50,
                                padding=10,
                                border_radius=10,
                                border=ft.Border.all(1, ft.Colors.BLUE_200),
                                expand=True
                            ),
                            # Mũi tên tiến bộ
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, color=gain_color, size=22),
                                    ft.Text(diff_str, size=11, weight=ft.FontWeight.BOLD, color=gain_color),
                                    ft.Text(f"Hake: {hake_pct}%", size=9, weight=ft.FontWeight.BOLD, color=gain_color)
                                ], spacing=1, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=4
                            ),
                            # Cột 2: Đầu ra Post-test
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("2. ĐẦU RA (POST-TEST) 📝", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                                    ft.Text(f"{rec.score:.1f} / 10đ", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
                                    ft.Text("Làm chủ sau bài học", size=9.5, color=ft.Colors.GREY_600)
                                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.GREEN_50,
                                padding=10,
                                border_radius=10,
                                border=ft.Border.all(1, ft.Colors.GREEN_200),
                                expand=True
                            )
                        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Text(
                            f"💡 Phân tích sư phạm: Sau khi trải qua chu trình gợi mở Socratic 5 pha, tư duy của em đã bứt phá {diff_str}! Em đã chuyển biến từ mức nhận biết ban đầu sang làm chủ sâu sắc bản chất khoa học.",
                            size=10.5,
                            color=ft.Colors.INDIGO_900,
                            italic=True
                        )
                    ], spacing=8),
                    bgcolor=ft.Colors.WHITE,
                    padding=12,
                    border_radius=12,
                    border=ft.Border.all(1.5, ft.Colors.INDIGO_300),
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2))
                )
            else:
                # Học sinh không làm Pre-test trước bài học -> Vẫn hiển thị bảng đánh giá tiến độ trực quan
                baseline_est = 4.0
                diff_val = max(0.0, round(rec.score - baseline_est, 1))
                diff_str = f"+{diff_val} điểm" if diff_val > 0 else f"{diff_val} điểm"
                comparison_card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.TRENDING_UP_ROUNDED, color=ft.Colors.INDIGO_700, size=20),
                            ft.Text("ĐÁNH GIÁ NĂNG LỰC ĐẦU RA & TIẾN ĐỘ HỌC TẬP 📊", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                            ft.Container(
                                content=ft.Text(f"TIẾN ĐỘ ĐẦU RA: {rec.score:.1f}/10đ ✓", size=9.5, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.GREEN_700,
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=6
                            )
                        ], spacing=6),
                        ft.Row([
                            # Cột 1: Mức nhận biết ban đầu
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("1. TRƯỚC BÀI HỌC 🎯", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                                    ft.Text("~4.0 / 10đ", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                                    ft.Text("Mức nhận biết khởi điểm", size=9.5, color=ft.Colors.GREY_600)
                                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.BLUE_50,
                                padding=10,
                                border_radius=10,
                                border=ft.Border.all(1, ft.Colors.BLUE_200),
                                expand=True
                            ),
                            # Mũi tên tiến bộ
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, color=ft.Colors.GREEN_700, size=22),
                                    ft.Text(f"+{diff_val}đ 🚀", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                    ft.Text("Bứt phá", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
                                ], spacing=1, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=4
                            ),
                            # Cột 2: Đầu ra Post-test
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("2. ĐẦU RA (POST-TEST) 📝", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                                    ft.Text(f"{rec.score:.1f} / 10đ", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
                                    ft.Text("Làm chủ sau bài học", size=9.5, color=ft.Colors.GREY_600)
                                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.GREEN_50,
                                padding=10,
                                border_radius=10,
                                border=ft.Border.all(1, ft.Colors.GREEN_200),
                                expand=True
                            )
                        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Text(
                            f"💡 Phân tích sư phạm: Em đã đạt {rec.score:.1f}/10đ trong bài kiểm tra sau học! Năng lực khoa học đã TĂNG TRƯỞNG RÕ RỆT và được ghi nhận vào hồ sơ cá nhân. (Mẹo: Lần sau hãy làm bài Khảo sát đầu vào 2 phút trước khi chat để hệ thống đo độ tăng trưởng Hake Gain chuẩn xác 100% nhé!)",
                            size=10.5,
                            color=ft.Colors.INDIGO_900,
                            italic=True
                        )
                    ], spacing=8),
                    bgcolor=ft.Colors.WHITE,
                    padding=12,
                    border_radius=12,
                    border=ft.Border.all(1.5, ft.Colors.INDIGO_300),
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2))
                )
            detail_items.append(ft.Container(height=4))
            detail_items.append(comparison_card)

        # Thẻ thông báo Chuỗi ngày học (Streak) nếu là Post-test
        if not is_pre and self.streak_result:
            streak_cnt = self.streak_result.get("streak_count", 1)
            streak_msg = self.streak_result.get("message", f"Chúc mừng em đã giải xong bài tập! Chuỗi ngày học tăng lên {streak_cnt} ngày liên tiếp!")
            streak_card = ft.Container(
                content=ft.Row([
                    ft.Text("🔥", size=26),
                    ft.Column([
                        ft.Row([
                            ft.Text(f"Chuỗi Học Tập: {streak_cnt} Ngày Liên Tiếp!", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900),
                            ft.Container(
                                content=ft.Text("ĐÃ GHI NHẬN HÔM NAY ✓", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.GREEN_700,
                                padding=ft.Padding(5, 2, 5, 2),
                                border_radius=4
                            )
                        ], spacing=6),
                        ft.Text(streak_msg, size=11, color=ft.Colors.AMBER_900)
                    ], spacing=2, expand=True)
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.AMBER_50,
                padding=10,
                border_radius=10,
                border=ft.Border.all(1.2, ft.Colors.AMBER_300)
            )
            detail_items.append(ft.Container(height=4))
            detail_items.append(streak_card)

        # Nhận xét câu tự luận (nếu có câu tự luận)
        if not is_pre and hasattr(rec, "essay_score") and rec.essay_score > 0:
            essay_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.PURPLE_700, size=16),
                        ft.Text(f"Đánh giá Câu Tự Luận: {rec.essay_score:.1f} / 4.0 điểm", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900)
                    ], spacing=6),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Lời nhận xét từ Socrates:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                            ft.Text(rec.essay_feedback, size=11, color=ft.Colors.INDIGO_900)
                        ], spacing=2),
                        bgcolor=ft.Colors.PURPLE_50,
                        padding=10,
                        border_radius=10,
                        border=ft.Border.all(1, ft.Colors.PURPLE_200)
                    )
                ], spacing=8),
                bgcolor=ft.Colors.WHITE,
                padding=12,
                border_radius=12,
                border=ft.Border.all(1, ft.Colors.GREY_300)
            )
            detail_items.append(ft.Container(height=4))
            detail_items.append(essay_card)

        # Chi tiết từng câu trắc nghiệm
        mcq_details_col = []
        for idx, d in enumerate(rec.details):
            if d.get("q_type") == "mcq":
                is_c = d.get("is_correct", False)
                icon = ft.Icons.CHECK_CIRCLE_ROUNDED if is_c else ft.Icons.CANCEL_ROUNDED
                icon_color = ft.Colors.GREEN_600 if is_c else ft.Colors.RED_600
                bg = ft.Colors.GREEN_50 if is_c else ft.Colors.RED_50
                border_c = ft.Colors.GREEN_300 if is_c else ft.Colors.RED_200
                score_str = "+3.3đ" if (is_c and is_pre) else ("+2.0đ" if is_c else "0.0đ")

                options = d.get("options", [])
                chosen_idx = d.get("chosen_index", -1)
                correct_idx = d.get("correct_index", 0)

                chosen_text = options[chosen_idx] if (0 <= chosen_idx < len(options)) else "(Chưa chọn đáp án)"
                correct_text = options[correct_idx] if (0 <= correct_idx < len(options)) else ""

                answer_lines = []
                if is_c:
                    answer_lines.append(
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_ROUNDED, color=ft.Colors.GREEN_700, size=15),
                            ft.Text(f"Đáp án em chọn: {chosen_text} (CHÍNH XÁC ✓)", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800, expand=True)
                        ], spacing=4)
                    )
                else:
                    answer_lines.append(
                        ft.Row([
                            ft.Icon(ft.Icons.CLOSE_ROUNDED, color=ft.Colors.RED_700, size=15),
                            ft.Text(f"Lựa chọn của em: {chosen_text} (Chưa đúng)", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_800, expand=True)
                        ], spacing=4)
                    )
                    if correct_text:
                        answer_lines.append(
                            ft.Row([
                                ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.GREEN_700, size=15),
                                ft.Text(f"Đáp án đúng chuẩn SGK: {correct_text}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900, expand=True)
                            ], spacing=4)
                        )

                mcq_details_col.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(icon, color=icon_color, size=16),
                                ft.Text(f"Câu {idx + 1}: {d.get('prompt')}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900, expand=True),
                                ft.Text(score_str, size=11, weight=ft.FontWeight.BOLD, color=icon_color)
                            ], spacing=6),
                            *answer_lines,
                            ft.Text(f"💡 Bản chất khoa học: {d.get('explanation')}", size=10.5, italic=True, color=ft.Colors.GREY_800)
                        ], spacing=4),
                        bgcolor=bg,
                        padding=10,
                        border_radius=10,
                        border=ft.Border.all(1, border_c)
                    )
                )

        detail_items.append(ft.Container(height=6))
        detail_items.append(ft.Column(mcq_details_col, spacing=6))

        return ft.Column(detail_items, spacing=4, scroll=ft.ScrollMode.AUTO)

    def _build_actions(self) -> ft.Control:
        """Thanh nút hành động ở cuối dialog."""
        if self.is_loading_ai:
            return ft.Row([
                ft.OutlinedButton(
                    "Để Lần Sau",
                    icon=ft.Icons.CLOSE_ROUNDED,
                    on_click=lambda _: safe_close_dialog(self.page, self.dialog),
                    style=ft.ButtonStyle(color=ft.Colors.GREY_700)
                ),
                ft.FilledButton(
                    "Dùng Đề SGK Ngay ⚡",
                    icon=ft.Icons.FLASH_ON_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE),
                    on_click=lambda _: self._cancel_loading_and_use_offline()
                )
            ], spacing=10)

        if self.current_state == "taking":
            btn_submit_text = "Nộp Bài Khảo Sát & Vào Học 🚀" if self.quiz_type == "pre_test" else "Nộp Bài & So Sánh Tiến Bộ 🎯"

            def on_cancel_click(_):
                safe_close_dialog(self.page, self.dialog)
                if self.quiz_type == "pre_test" and self.on_completed:
                    self.on_completed(None)

            return ft.Row([
                ft.OutlinedButton(
                    "Để Lần Sau",
                    icon=ft.Icons.CLOSE_ROUNDED,
                    on_click=on_cancel_click,
                    style=ft.ButtonStyle(color=ft.Colors.GREY_700)
                ),
                ft.FilledButton(
                    btn_submit_text,
                    icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE),
                    on_click=lambda _: self._on_submit_quiz()
                )
            ], spacing=10)
        else:
            if self.quiz_type == "pre_test":
                btn_done_text = "Bắt Đầu Học Cùng Socrates Ngay 💡"
                btn_done_bg = ft.Colors.INDIGO_700
                btn_done_icon = ft.Icons.ROCKET_LAUNCH_ROUNDED
            else:
                btn_done_text = "Đã Hiểu Đáp Án ➔ Vào Sơ Đồ Tư Duy & Đúc Kết 🌿"
                btn_done_bg = ft.Colors.GREEN_700
                btn_done_icon = ft.Icons.WORKSPACE_PREMIUM_ROUNDED

            def on_finish_click(_):
                safe_close_dialog(self.page, self.dialog)
                if self.on_completed and self.graded_record:
                    self.on_completed(self.graded_record)

            return ft.FilledButton(
                btn_done_text,
                icon=btn_done_icon,
                style=ft.ButtonStyle(bgcolor=btn_done_bg, color=ft.Colors.WHITE),
                on_click=on_finish_click
            )

    def _on_submit_quiz(self):
        """Xử lý nộp bài và chấm điểm toàn diện (Pre-test hoặc Post-test)."""
        try:
            cur_user: UserAccount = AuthService.get_current_user()
            student_essay_text = (self.txt_essay.value or "").strip()

            if self.quiz_type == "pre_test":
                total_score, correct_mcq, details = QuizService.grade_pre_test(self.questions, self.mcq_answers)
                if total_score >= 7.0:
                    badge = "Nền Tảng Tốt 🌟"
                elif total_score >= 4.0:
                    badge = "Cần Khám Phá 💡"
                else:
                    badge = "Mới Bắt Đầu 🌱"

                import uuid
                record = QuizRecord(
                    quiz_id=f"PRE_{uuid.uuid4().hex[:8].upper()}",
                    username=cur_user.username,
                    student_name=cur_user.display_name,
                    topic=self.topic,
                    strand=self.strand,
                    quiz_type="pre_test",
                    created_at=datetime.now().isoformat(),
                    score=total_score,
                    total_mcq=len(self.questions),
                    correct_mcq=correct_mcq,
                    essay_score=0.0,
                    essay_feedback="Khảo sát đầu vào hoàn tất! Socrates đã hiểu trình độ hiện tại của em.",
                    student_essay_answer="",
                    badge_earned=badge,
                    details=details
                )
                QuizService.save_quiz_record(record)
                self.graded_record = record
                self.streak_result = {}
            else:
                total_score, correct_mcq, essay_score, essay_feedback, details = QuizService.grade_full_quiz(
                    questions=self.questions,
                    mcq_answers=self.mcq_answers,
                    student_essay=student_essay_text
                )

                # Xác định huy hiệu
                if total_score >= 8.5:
                    badge = "Xuất Sắc ⭐"
                elif total_score >= 7.0:
                    badge = "Khá Giỏi 🌟"
                elif total_score >= 5.0:
                    badge = "Đạt Chuẩn 💡"
                else:
                    badge = "Cần Ôn Luyện Thêm 💪"

                pre_score = self.pre_record.score if self.pre_record else None
                learning_gain = None
                gain_percent = None
                if pre_score is not None:
                    comp = QuizService.compare_pre_post(pre_score, total_score)
                    learning_gain = comp["diff"]
                    gain_percent = comp["hake_gain"]
                    badge = comp["badge"]

                import uuid
                record = QuizRecord(
                    quiz_id=f"QUIZ_{uuid.uuid4().hex[:8].upper()}",
                    username=cur_user.username,
                    student_name=cur_user.display_name,
                    topic=self.topic,
                    strand=self.strand,
                    quiz_type="post_test" if self.quiz_type in ["post_lesson", "post_test"] else self.quiz_type,
                    created_at=datetime.now().isoformat(),
                    score=total_score,
                    total_mcq=3,
                    correct_mcq=correct_mcq,
                    essay_score=essay_score,
                    essay_feedback=essay_feedback,
                    student_essay_answer=student_essay_text,
                    badge_earned=badge,
                    details=details,
                    pre_test_score=pre_score,
                    learning_gain=learning_gain,
                    gain_percent=gain_percent
                )
                QuizService.save_quiz_record(record)
                self.graded_record = record

                # Ghi nhận bài tập đã giải và cập nhật Chuỗi Streak học tập chuẩn xác
                try:
                    self.streak_result = AuthService.record_exercise_solved(
                        username=cur_user.username,
                        topic=self.topic,
                        domain=self.strand,
                        exercise_type="quiz",
                        score=total_score,
                        minutes=10,
                        is_new_exercise=False
                    )
                except Exception as e:
                    print(f"[QuizView] Lỗi ghi nhận giải bài tập: {e}")
                    self.streak_result = {}

            # Chuyển trạng thái sang xem kết quả
            self.current_state = "result"
            self._render_content()
            self.dialog.actions = [self._build_actions()]
            self.page.update()
        except Exception as e:
            import traceback
            traceback.print_exc()
