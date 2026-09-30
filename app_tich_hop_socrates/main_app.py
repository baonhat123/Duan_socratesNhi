"""
Module: main_app.py
Ứng dụng Tích hợp Hoàn chỉnh Socrates Nhí (Kết hợp Đầy đủ Chức năng 1, 2, 3, 4 & 5)
Phiên bản Giao diện Ed-Tech 2.0 Thân thiện Học sinh THCS
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Hành trình tương tác hoàn chỉnh xuyên suốt 5 Trạm Khám Phá:
1. Trạm 1: Tiếp nhận đề bài (Văn bản, Tải ảnh JPG/PNG <= 5MB, hoặc Đề mẫu KHTN 7).
2. Trạm 2: Trích xuất OCR & Soát lỗi công thức KHTN (Đo độ nét, Đối chiếu 2 cột, Thanh ký hiệu nhanh).
3. Trạm 3: Phân loại kiến thức bài toán & Bản đồ khái niệm cốt lõi (Cơ học, Hóa học, Sinh học, Lỗi thường gặp).
4. Trạm 4: Hội thoại Socratic gợi mở tư duy 5 pha (clarify -> recall -> reason -> check -> generalize) không phát đáp án sẵn!
5. Trạm 5: Sơ đồ Tư duy 3–6 nút & Khung tự đúc kết 3 dòng, Khảo sát 1–5 sao, Nhật ký ẩn danh (FR-06, FR-08, FR-09).
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import os
import flet as ft

from app_tich_hop_socrates.ai_service import (
    get_ai_config,
    save_ai_config,
    test_ai_connection,
    load_project_env
)

# Nhập các thành phần từ các thư mục chức năng độc lập
from chuc_nang_1_nhap_de.input_model import ProblemInput, InputType
from chuc_nang_1_nhap_de.ui_component import ProblemInputView

from chuc_nang_2_ocr_xac_nhan.ocr_model import ConfirmedProblem
from chuc_nang_2_ocr_xac_nhan.ocr_view import OcrConfirmationView
from chuc_nang_2_ocr_xac_nhan.formula_normalizer import normalize_khtn_text

from chuc_nang_3_phan_loai_kien_thuc.classifier_model import ClassificationResult
from chuc_nang_3_phan_loai_kien_thuc.classifier_view import KnowledgeClassifierView

from chuc_nang_4_hoi_thoai_socratic.socratic_view import SocraticChatView
from chuc_nang_4_hoi_thoai_socratic.socratic_model import SocraticPhase

from chuc_nang_5_so_do_tong_ket.mindmap_view import MindmapSummaryView
from chuc_nang_6_guardrail_chong_ro_dap_an.guardrail_view import GuardrailPlaygroundView
from chuc_nang_7_demo_offline_cache.offline_view import OfflineCacheControlView
from chuc_nang_7_demo_offline_cache.offline_engine import GLOBAL_OFFLINE_ENGINE

from app_tich_hop_socrates.app_state import SessionState, AppStep
from app_tich_hop_socrates.auth_service import AuthService, UserAccount
from app_tich_hop_socrates.auth_view import LoginScreenView, AuthModalDialog, AuthDialogView


class SocratesIntegratedApp:
    """
    Ứng dụng tích hợp điều phối toàn bộ hành trình tương tác của học sinh.
    """
    def __init__(self, page: ft.Page):
        self.page = page
        self.state = SessionState()
        self.state.current_user = AuthService.get_current_user()

        # Nạp biến môi trường toàn cục
        load_project_env()

        # Tự động kích hoạt chế độ AI trực tuyến nếu có cấu hình OPENAI_API_KEY
        if os.getenv("OPENAI_API_KEY"):
            GLOBAL_OFFLINE_ENGINE.set_force_offline(False)
        else:
            GLOBAL_OFFLINE_ENGINE.set_force_offline(True)

        # Cấu hình cửa sổ ứng dụng
        self.page.title = "Socrates Nhí 💡 - Trợ lý AI gợi mở tư duy KHTN (Bảng A - AI 2026)"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#F8FAFC"
        self.page.padding = 0

        if hasattr(self.page, "window") and self.page.window is not None:
            try:
                self.page.window.width = 1140
                self.page.window.height = 920
            except Exception:
                pass

        # Vùng chứa giao diện nội dung động của các Trạm (Step 1-5)
        self.content_area = ft.Container(expand=True)

        # Xây dựng thanh định vị toàn cục (Global Stepper & Header)
        self._build_global_navigation()

        # Khung chứa chính của ứng dụng (Main Gateway Container)
        self.main_container = ft.Container(expand=True)

        # Mới vào ứng dụng: Bắt buộc hiển thị Màn hình Đăng nhập & Tạo tài khoản theo yêu cầu
        self.is_logged_in = False
        self._show_login_screen()

    def _create_station_pill(self, step_num: int, title: str, subtitle: str, on_click=None) -> ft.Container:
        """Tạo thẻ giao diện cho một Trạm trong lộ trình 3 bước thân thiện."""
        circle_badge = ft.Container(
            content=ft.Text(str(step_num), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
            width=26,
            height=26,
            border_radius=13,
            bgcolor=ft.Colors.GREY_200,
            alignment=ft.Alignment.CENTER
        )

        title_text = ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800)
        subtitle_text = ft.Text(subtitle, size=10, color=ft.Colors.GREY_500)

        pill = ft.Container(
            content=ft.Row([
                circle_badge,
                ft.Column([title_text, subtitle_text], spacing=1)
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(12, 8, 12, 8),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            bgcolor=ft.Colors.WHITE,
            expand=True,
            on_click=on_click,
            ink=True if on_click else False
        )
        return pill

    def _build_global_navigation(self):
        """Xây dựng thanh tiêu đề và thanh tiến trình lộ trình 3 bước sinh động."""
        self.app_brand = ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.WHITE, size=24),
                    bgcolor=ft.Colors.AMBER_500,
                    width=42,
                    height=42,
                    border_radius=21,
                    alignment=ft.Alignment.CENTER,
                    shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.35, ft.Colors.AMBER_500), offset=ft.Offset(0, 2))
                ),
                ft.Column(
                    [
                        ft.Text("SOCRATES NHÍ 💡", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ft.Text("Trợ lý AI gợi mở tư duy KHTN THCS • Cuộc thi Sáng tạo trẻ Quốc gia AI 2026", size=11, color=ft.Colors.GREY_700)
                    ],
                    spacing=1
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )

        self.pedagogy_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.INDIGO_700, size=14),
                ft.Text("Gia sư Socratic 5 Pha", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=4),
            bgcolor=ft.Colors.INDIGO_50,
            padding=ft.Padding(10, 6, 10, 6),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.INDIGO_200)
        )

        self.offline_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BOLT_ROUNDED, color=ft.Colors.AMBER_800, size=15),
                ft.Text("⚡ Demo Offline (12 Bài) 📚", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
            ], spacing=4),
            bgcolor=ft.Colors.AMBER_50,
            padding=ft.Padding(10, 6, 10, 6),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.AMBER_300),
            tooltip="Bấm để mở Bảng điều khiển Demo Offline & Khám phá 12 bài mẫu KHTN 7 (FR-10)",
            on_click=lambda _: self._open_offline_dashboard()
        )

        self.guardrail_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SHIELD_ROUNDED, color=ft.Colors.GREEN_700, size=14),
                ft.Text("Khiên An Toàn 🛡️", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900)
            ], spacing=4),
            bgcolor=ft.Colors.GREEN_50,
            padding=ft.Padding(10, 6, 10, 6),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREEN_300),
            tooltip="Bấm để mở Bảng kiểm định & thử nghiệm bẻ khóa AI 3 tầng (FR-07)",
            on_click=lambda _: self._open_guardrail_dashboard()
        )

        self.rubric_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ASSESSMENT_ROUNDED, color=ft.Colors.PURPLE_700, size=14),
                ft.Text("Đánh Giá Rubric 📊", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900)
            ], spacing=4),
            bgcolor=ft.Colors.PURPLE_50,
            padding=ft.Padding(10, 6, 10, 6),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.PURPLE_300),
            tooltip="Bấm để mở Bảng đánh giá Rubric tiến bộ lập luận 0-6đ & 5 Chỉ số khoa học MVP (Mục 16.3 & 3)",
            on_click=lambda _: self._open_rubric_dashboard()
        )

        self.ai_status_btn = self._create_ai_status_badge()

        # 3 Bước Khám phá Thân thiện với Học sinh
        def on_click_pill_1(_):
            self.navigate_to_step_1()

        def on_click_pill_2(_):
            if self.state.confirmed_problem or self.state.problem_input:
                self.navigate_to_step_4()
            else:
                self.navigate_to_step_1()

        def on_click_pill_3(_):
            if not self.state.is_socratic_completed:
                self._show_not_summarized_dialog()
            else:
                self.navigate_to_step_5()

        self.pill_step_1 = self._create_station_pill(1, "Bước 1: Đặt câu hỏi", "Gõ câu hỏi / Mẫu / Chụp ảnh", on_click=on_click_pill_1)
        self.pill_step_2 = self._create_station_pill(2, "Bước 2: Gia sư Socratic", "Gợi mở & Trao đổi trực tiếp 💬", on_click=on_click_pill_2)
        self.pill_step_3 = self._create_station_pill(3, "Bước 3: Sơ đồ & Đúc kết", "Bản đồ tư duy & Tự đúc kết 🌟", on_click=on_click_pill_3)

        self.station_pills = [
            self.pill_step_1,
            self.pill_step_2,
            self.pill_step_3
        ]

        arrow_icon = lambda: ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color=ft.Colors.INDIGO_300, size=18)

        self.notebook_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=ft.Colors.CYAN_800, size=14),
                ft.Text("Sổ Tay Của Em 📓", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_900)
            ], spacing=4),
            bgcolor=ft.Colors.CYAN_50,
            padding=ft.Padding(10, 6, 10, 6),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.CYAN_300),
            tooltip="Bấm để mở Sổ tay Tự học (Xem lại các bài đã đúc kết và kiến thức cần nhớ)",
            on_click=lambda _: self._open_notebook_viewer()
        )

        self.stepper_bar = ft.Container(
            content=ft.Row(
                [
                    self.pill_step_1,
                    arrow_icon(),
                    self.pill_step_2,
                    arrow_icon(),
                    self.pill_step_3,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8
            ),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(10, 8, 10, 8),
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        self.user_chip = self._create_user_profile_chip()

        self.header_panel = ft.Container(
            content=ft.Row([
                self.app_brand,
                ft.Row([
                    self.pedagogy_badge,
                    self.ai_status_btn,
                    self.notebook_btn,
                    self.offline_btn,
                    self.guardrail_btn,
                    self.rubric_btn,
                    self.user_chip
                ], spacing=8, wrap=True, alignment=ft.MainAxisAlignment.END)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(18, 12, 18, 12),
            border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.INDIGO_50)),
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 3))
        )

    def _update_stepper_visuals(self, active_step: str):
        """Cập nhật giao diện Stepper 3 bước thân thiện học sinh."""
        if active_step in [AppStep.STEP_1_INPUT, AppStep.STEP_2_OCR]:
            active_idx = 0
        elif active_step in [AppStep.STEP_4_SOCRATIC, AppStep.STEP_3_CLASSIFIER]:
            active_idx = 1
        else:
            active_idx = 2

        orig_subs = [
            "Gõ câu hỏi / Mẫu / Chụp ảnh",
            "Gợi mở & Trao đổi trực tiếp 💬",
            "Bản đồ tư duy & Tự đúc kết 🌟"
        ]

        for idx, pill in enumerate(self.station_pills):
            row = pill.content
            badge = row.controls[0]
            texts = row.controls[1]
            title_text = texts.controls[0]
            sub_text = texts.controls[1]

            if idx < active_idx:
                # Đã hoàn thành (Completed) -> Xanh ngọc tươi sáng
                pill.bgcolor = ft.Colors.GREEN_50
                pill.border = ft.Border.all(1.5, ft.Colors.GREEN_300)
                pill.shadow = None
                badge.bgcolor = ft.Colors.GREEN_600
                badge.content = ft.Icon(ft.Icons.CHECK_ROUNDED, color=ft.Colors.WHITE, size=15)
                title_text.color = ft.Colors.GREEN_900
                title_text.weight = ft.FontWeight.BOLD
                sub_text.color = ft.Colors.GREEN_700
                sub_text.value = "✓ Đã hoàn thành"

            elif idx == active_idx:
                # Đang hoạt động (Active) -> Màu Indigo nổi bật có bóng mờ
                pill.bgcolor = ft.Colors.INDIGO_600
                pill.border = ft.Border.all(1.5, ft.Colors.INDIGO_700)
                pill.shadow = ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.25, ft.Colors.INDIGO_700), offset=ft.Offset(0, 2))
                badge.bgcolor = ft.Colors.WHITE
                badge.content = ft.Text(str(idx + 1), size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800)
                title_text.color = ft.Colors.WHITE
                title_text.weight = ft.FontWeight.BOLD
                sub_text.color = ft.Colors.INDIGO_100
                sub_text.value = "🎯 Đang ở đây"

            else:
                # Chưa tới (Upcoming) -> Trắng xám thanh lịch
                pill.bgcolor = ft.Colors.WHITE
                pill.border = ft.Border.all(1, ft.Colors.GREY_300)
                pill.shadow = None
                badge.bgcolor = ft.Colors.GREY_100
                badge.content = ft.Text(str(idx + 1), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600)
                title_text.color = ft.Colors.GREY_700
                title_text.weight = ft.FontWeight.W_500
                sub_text.color = ft.Colors.GREY_500
                sub_text.value = orig_subs[idx]

        self.page.update()

    def _create_ai_status_badge(self) -> ft.Container:
        """Tạo nút hiển thị trạng thái AI và mở hộp thoại Cấu hình AI."""
        is_online = not GLOBAL_OFFLINE_ENGINE.is_offline()
        cfg = get_ai_config()
        has_key = cfg["has_key"]
        model = cfg["model"]

        if is_online and has_key:
            short_model = model.split("-202")[0] if "-202" in model else model
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREEN_600, size=9),
                    ft.Text(f"AI Trực Tuyến: {short_model}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900)
                ], spacing=6),
                bgcolor=ft.Colors.GREEN_50,
                padding=ft.Padding(10, 6, 10, 6),
                border_radius=12,
                border=ft.Border.all(1, ft.Colors.GREEN_300),
                tooltip=f"AI đang hoạt động ({model}). Bấm để kiểm tra kết nối / cấu hình AI.",
                on_click=lambda _: self._open_ai_settings_dialog()
            )
        else:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CLOUD_OFF_ROUNDED, color=ft.Colors.AMBER_800, size=14),
                    ft.Text("⚡ Demo Ngoại Tuyến", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
                ], spacing=5),
                bgcolor=ft.Colors.AMBER_50,
                padding=ft.Padding(10, 6, 10, 6),
                border_radius=12,
                border=ft.Border.all(1, ft.Colors.AMBER_300),
                tooltip="Đang ở chế độ Ngoại tuyến. Bấm để kích hoạt AI trực tuyến hoặc cấu hình API Key.",
                on_click=lambda _: self._open_ai_settings_dialog()
            )

    def _refresh_ai_badge(self):
        """Cập nhật lại giao diện nút trạng thái AI trên thanh tiêu đề."""
        new_badge = self._create_ai_status_badge()
        self.ai_status_btn.content = new_badge.content
        self.ai_status_btn.bgcolor = new_badge.bgcolor
        self.ai_status_btn.border = new_badge.border
        self.ai_status_btn.tooltip = new_badge.tooltip
        self.page.update()

    def _open_ai_settings_dialog(self):
        """Mở Bảng Điều Khiển & Cấu Hình Kết Nối AI (OpenAI-compatible Hub)."""
        cfg = get_ai_config()
        is_online = not GLOBAL_OFFLINE_ENGINE.is_offline()

        status_text = ft.Text(
            "🟢 AI Đang Hoạt Động (Trực Tuyến)" if is_online and cfg["has_key"] else "⚡ Chế Độ Demo Ngoại Tuyến (Offline)",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_800 if is_online and cfg["has_key"] else ft.Colors.AMBER_900
        )

        ping_result_text = ft.Text("", size=12, italic=True)

        txt_base_url = ft.TextField(
            label="Điểm cuối API (OPENAI_BASE_URL)",
            value=cfg["base_url"],
            hint_text="https://api.openai.com/v1",
            text_size=12,
            dense=True
        )

        txt_model = ft.TextField(
            label="Mã mô hình AI (SOCRATES_MODEL)",
            value=cfg["model"],
            hint_text="gpt-5-mini-2025-08-07, gpt-4o-mini...",
            text_size=12,
            dense=True
        )

        txt_api_key = ft.TextField(
            label="Khóa bí mật API (OPENAI_API_KEY)",
            value=cfg["api_key"],
            password=True,
            can_reveal_password=True,
            hint_text="sk-...",
            text_size=12,
            dense=True
        )

        def on_test_ping(_):
            ping_result_text.value = "⏳ Đang gửi thử nghiệm ping đến máy chủ AI..."
            ping_result_text.color = ft.Colors.BLUE_700
            self.page.update()

            def ping_worker():
                res = test_ai_connection()
                def apply_ping_ui():
                    if res["success"]:
                        ping_result_text.value = f"✅ {res['message']}"
                        ping_result_text.color = ft.Colors.GREEN_700
                    else:
                        ping_result_text.value = f"❌ {res['message']}"
                        ping_result_text.color = ft.Colors.RED_700
                    try:
                        self.page.update()
                    except Exception:
                        pass

                try:
                    if hasattr(self.page, "loop") and self.page.loop and self.page.loop.is_running():
                        self.page.loop.call_soon_threadsafe(apply_ping_ui)
                    else:
                        apply_ping_ui()
                except Exception:
                    apply_ping_ui()

            if hasattr(self.page, "run_thread") and callable(self.page.run_thread):
                self.page.run_thread(ping_worker)
            else:
                import threading
                threading.Thread(target=ping_worker, daemon=True).start()

        def on_toggle_mode(_):
            now_offline = GLOBAL_OFFLINE_ENGINE.is_offline()
            if now_offline:
                GLOBAL_OFFLINE_ENGINE.set_force_offline(False)
            else:
                GLOBAL_OFFLINE_ENGINE.set_force_offline(True)

            self._refresh_ai_badge()
            curr_online = not GLOBAL_OFFLINE_ENGINE.is_offline()
            status_text.value = "🟢 AI Đang Hoạt Động (Trực Tuyến)" if curr_online and cfg["has_key"] else "⚡ Chế Độ Demo Ngoại Tuyến (Offline)"
            status_text.color = ft.Colors.GREEN_800 if curr_online and cfg["has_key"] else ft.Colors.AMBER_900
            toggle_btn.text = "Chuyển sang Ngoại tuyến ⚡" if curr_online else "Kích hoạt AI Trực tuyến 🟢"
            self.page.update()

        toggle_btn = ft.OutlinedButton(
            "Chuyển sang Ngoại tuyến ⚡" if is_online else "Kích hoạt AI Trực tuyến 🟢",
            on_click=on_toggle_mode
        )

        save_status_text = ft.Text("", size=12, color=ft.Colors.GREEN_700)

        def on_save_config(_):
            new_key = txt_api_key.value or ""
            new_model = txt_model.value or ""
            new_url = txt_base_url.value or ""
            ok = save_ai_config(new_key, new_model, new_url)
            if ok:
                if new_key.strip():
                    GLOBAL_OFFLINE_ENGINE.set_force_offline(False)
                save_status_text.value = "💾 Đã lưu cấu hình AI vào file .env thành công!"
                save_status_text.color = ft.Colors.GREEN_700
                self._refresh_ai_badge()
            else:
                save_status_text.value = "❌ Không thể ghi file .env!"
                save_status_text.color = ft.Colors.RED_700
            self.page.update()

        def close_dialog(_):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        content_box = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text("Trạng thái kết nối hiện thời:", size=11, color=ft.Colors.GREY_600),
                            status_text,
                        ], spacing=2),
                        toggle_btn
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.GREY_50,
                    padding=10,
                    border_radius=10,
                    border=ft.Border.all(1, ft.Colors.GREY_200)
                ),
                ft.Container(height=4),
                ft.Text("Cấu hình nhà cung cấp AI chuẩn OpenAI-compatible (Mục 8.1 & Mục 19.1):", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                txt_base_url,
                txt_model,
                txt_api_key,
                ft.Row([
                    ft.FilledButton(
                        "Kiểm tra kết nối AI ⚡",
                        icon=ft.Icons.NETWORK_CHECK_ROUNDED,
                        on_click=on_test_ping,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
                    ),
                    ft.FilledButton(
                        "Lưu cấu hình (.env) 💾",
                        icon=ft.Icons.SAVE_ROUNDED,
                        on_click=on_save_config,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
                    )
                ], spacing=10),
                ping_result_text,
                save_status_text,
                ft.Divider(height=1),
                ft.Text("💡 Lưu ý sư phạm & Bảng A: Khóa bí mật chỉ lưu trên máy trạm tại tệp .env, hỗ trợ chuyển đổi linh hoạt mô hình GPT-4o, GPT-5-mini, Gemini OpenAI proxy hoặc DeepSeek mà không cần sửa mã nguồn.", size=10, italic=True, color=ft.Colors.GREY_600)
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            width=650,
            height=530,
            padding=10
        )

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.SMART_TOY_ROUNDED, color=ft.Colors.INDIGO_700, size=24),
                ft.Text("Bảng Điều Khiển & Cấu Hình Kết Nối AI 🤖", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=content_box,
            actions=[
                ft.FilledButton(
                    "Đóng",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _open_guardrail_dashboard(self):
        """Mở Bảng Điều Khiển An Toàn & Thử Nghiệm Bẻ Khóa AI (FR-07)."""
        playground = GuardrailPlaygroundView(page=self.page, is_standalone=False)

        def close_dialog(_):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.SHIELD_ROUNDED, color=ft.Colors.GREEN_700, size=24),
                ft.Text("Bảng Điều Khiển An Toàn & Thử Nghiệm Bẻ Khóa AI (FR-07)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=playground.build(),
                width=850,
                height=580,
            ),
            actions=[
                ft.FilledButton(
                    "Đóng bảng điều khiển",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _open_offline_dashboard(self):
        """Mở Bảng Điều Khiển Demo Offline & Ngân hàng 12 Bài Mẫu KHTN 7 (FR-10)."""
        def on_study_prob(prob):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

            # Nạp bài toán vào ứng dụng và vào thẳng trao đổi với Gia sư Socratic
            normalized_text = normalize_khtn_text(prob.problem_text)
            self.state.problem_input = ProblemInput(
                input_type=InputType.SAMPLE,
                text_content=prob.problem_text,
                is_confirmed=True
            )
            self.state.confirmed_problem = ConfirmedProblem(
                original_text=prob.problem_text,
                confirmed_text=normalized_text,
                source_type="sample"
            )
            from chuc_nang_3_phan_loai_kien_thuc.classifier_engine import KnowledgeClassifier
            self.state.classification_result = KnowledgeClassifier().classify_problem(normalized_text)
            self.navigate_to_step_4()

        view_7 = OfflineCacheControlView(
            page=self.page,
            on_select_problem_for_study=on_study_prob,
            is_standalone=False
        )

        def close_dialog(_):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CLOUD_OFF_ROUNDED, color=ft.Colors.AMBER_800, size=24),
                ft.Text("Bảng Điều Khiển Chế Độ Demo Offline (FR-10)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=view_7.build(),
                width=900,
                height=620,
            ),
            actions=[
                ft.FilledButton(
                    "Đóng bảng điều khiển",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _create_user_profile_chip(self) -> ft.Container:
        """Tạo thẻ hiển thị thông tin tài khoản học sinh ở góc phải trên cùng."""
        user = self.state.current_user or AuthService.get_current_user()

        self.user_avatar_text = ft.Text(user.avatar, size=15)
        self.user_name_text = ft.Text(user.display_name, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900)
        class_short = user.grade_class.split("•")[0].strip() if user.grade_class else "Học sinh"
        self.user_class_text = ft.Text(class_short, size=10, color=ft.Colors.PURPLE_700)

        chip = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=self.user_avatar_text,
                    width=26,
                    height=26,
                    border_radius=13,
                    bgcolor=ft.Colors.PURPLE_100,
                    alignment=ft.Alignment.CENTER
                ),
                ft.Column([
                    self.user_name_text,
                    self.user_class_text
                ], spacing=0),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN_ROUNDED, color=ft.Colors.PURPLE_800, size=18)
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.PURPLE_50,
            padding=ft.Padding(8, 4, 10, 4),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.PURPLE_300),
            tooltip="Tài khoản học sinh • Bấm để xem thông tin, đổi tài khoản hoặc đăng nhập",
            on_click=lambda _: self._open_auth_dialog(),
            ink=True
        )
        return chip

    def _show_login_screen(self):
        """Hiển thị Màn hình Đăng Nhập & Tạo Tài Khoản khi mới vào ứng dụng."""
        self.is_logged_in = False
        login_view = LoginScreenView(self.page, on_login_success=self._on_login_success)
        self.main_container.content = login_view.build()
        if hasattr(self.page, "update"):
            self.page.update()

    def _on_login_success(self, user: UserAccount):
        """Xử lý khi học sinh đăng nhập hoặc tạo tài khoản thành công."""
        self.is_logged_in = True
        self.state.current_user = user
        self._update_user_chip_display(user)

        # Chuyển sang không gian làm việc học tập 5 Trạm
        self._show_main_workspace()

        # Thông báo chào mừng học sinh
        snack = ft.SnackBar(
            content=ft.Row([
                ft.Text(user.avatar, size=20),
                ft.Text(f"Chào mừng {user.display_name}! Sẵn sàng cùng Socrates Nhí khám phá KHTN 💡", color=ft.Colors.WHITE, size=12)
            ], spacing=8),
            bgcolor=ft.Colors.INDIGO_900
        )
        if hasattr(self.page, "open"):
            self.page.open(snack)
        else:
            self.page.snack_bar = snack
            snack.open = True
        self.page.update()

    def _show_main_workspace(self):
        """Hiển thị Không gian làm việc học tập (Header + Stepper + Trạm học tập)."""
        self.main_container.content = ft.Column(
            [
                self.header_panel,
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                self.content_area
            ],
            spacing=0,
            expand=True
        )
        self.navigate_to_step_1()

    def _on_logout(self):
        """Xử lý khi học sinh bấm Đăng xuất."""
        AuthService.logout()
        self._show_login_screen()

    def _update_user_chip_display(self, user: UserAccount):
        """Cập nhật nhãn và avatar của chip tài khoản trên Header."""
        if hasattr(self, "user_avatar_text") and self.user_avatar_text:
            self.user_avatar_text.value = user.avatar
            self.user_name_text.value = user.display_name
            class_short = user.grade_class.split("•")[0].strip() if user.grade_class else "Học sinh"
            self.user_class_text.value = class_short

    def _open_auth_dialog(self):
        """Mở cửa sổ Đăng nhập / Tài khoản học sinh."""
        auth_modal = AuthModalDialog(
            self.page,
            on_user_changed=self._on_user_changed,
            on_logout=self._on_logout
        )
        auth_modal.show()

    def _on_user_changed(self, new_user: UserAccount):
        """Xử lý sự kiện đăng nhập / chuyển đổi tài khoản thành công."""
        self.state.current_user = new_user
        self._update_user_chip_display(new_user)

        # Hiển thị thông báo chào mừng
        snack = ft.SnackBar(
            content=ft.Row([
                ft.Text(new_user.avatar, size=18),
                ft.Text(f"Đã chuyển sang tài khoản {new_user.display_name}! 💡", color=ft.Colors.WHITE, size=12)
            ], spacing=6),
            bgcolor=ft.Colors.INDIGO_900
        )
        if hasattr(self.page, "open"):
            self.page.open(snack)
        else:
            self.page.snack_bar = snack
            snack.open = True
        self.page.update()

    def _open_notebook_viewer(self):
        """Mở Sổ tay Tự học từ thanh điều hướng trên cùng kèm thông tin tài khoản học sinh."""
        from chuc_nang_5_so_do_tong_ket.notebook_manager import load_notebook_entries
        entries = load_notebook_entries()

        cur_user = self.state.current_user or AuthService.get_current_user()
        active_filter = ["all"]  # "all" hoặc "mine"

        detail_container = ft.Container(expand=True)
        list_container = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

        def display_entry_detail(item: dict):
            takeaways_list = []
            for t in item.get("key_takeaways", []):
                takeaways_list.append(
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_600, size=14),
                        ft.Text(t, size=11, color=ft.Colors.GREY_800, expand=True)
                    ], spacing=4)
                )

            author_row = ft.Row([
                ft.Text(item.get("author_avatar", "💡"), size=14),
                ft.Text(f"Học sinh: {item.get('author_name', 'Học sinh')} • {item.get('author_class', '')}", size=11, color=ft.Colors.PURPLE_900, weight=ft.FontWeight.W_500)
            ], spacing=4) if item.get("author_name") else ft.Container()

            detail_container.content = ft.Column([
                ft.Row([
                    ft.Text(item.get("topic", "Khoa học Tự nhiên 7"), size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ft.Text(item.get("created_at", ""), size=11, color=ft.Colors.GREY_600)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                author_row,

                # Đề bài
                ft.Container(
                    content=ft.Column([
                        ft.Text("❓ Vấn đề / Câu hỏi nghiên cứu:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Text(item.get("problem_text", "Không có nội dung"), size=11, color=ft.Colors.GREY_900)
                    ], spacing=2),
                    bgcolor=ft.Colors.GREY_50,
                    padding=8,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.GREY_200)
                ),

                # Khái niệm hoàn chỉnh
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.INDIGO_700, size=16),
                            ft.Text(f"💡 {item.get('concept_name', 'Khái niệm chuẩn SGK')}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                        ], spacing=4),
                        ft.Text(item.get("full_concept", ""), size=11, color=ft.Colors.GREY_800),
                        *takeaways_list
                    ], spacing=4),
                    bgcolor=ft.Colors.INDIGO_50,
                    padding=10,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.INDIGO_200)
                ),

                # Đúc kết của học sinh
                ft.Container(
                    content=ft.Column([
                        ft.Text("✍️ 3 Điều em đã tự đúc kết:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900),
                        ft.Text(f"1. Quy tắc vận dụng: {item.get('rule_learned', '(Chưa ghi)')}", size=11, color=ft.Colors.GREY_800),
                        ft.Text(f"2. Bẫy sai sót: {item.get('pitfall_avoided', '(Chưa ghi)')}", size=11, color=ft.Colors.GREY_800),
                        ft.Text(f"3. Bước tiếp theo: {item.get('next_step', '(Chưa ghi)')}", size=11, color=ft.Colors.GREY_800),
                    ], spacing=3),
                    bgcolor=ft.Colors.PURPLE_50,
                    padding=10,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.PURPLE_200)
                ),

                # Đánh giá
                ft.Row([
                    ft.Text(f"Đánh giá: {'⭐' * item.get('rating_stars', 5)}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900),
                    ft.Text(f"Phản hồi: {item.get('feedback_comment', 'Không có')}", size=11, italic=True, color=ft.Colors.GREY_600)
                ], spacing=10)
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

            self.page.update()

        def render_list():
            list_container.controls.clear()
            filtered_entries = entries
            if active_filter[0] == "mine":
                filtered_entries = [
                    e for e in entries
                    if e.get("author_username") == cur_user.username or (cur_user.username == "minhtriet" and not e.get("author_username"))
                ]

            if filtered_entries:
                for entry in filtered_entries:
                    def make_click_handler(item_ref=entry):
                        return lambda _: display_entry_detail(item_ref)

                    author_label = f"{entry.get('author_avatar', '💡')} {entry.get('author_name', 'Minh Triết')}"

                    card = ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(entry.get("concept_name", entry.get("topic", "Bài học")), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900, expand=True),
                                ft.Text(f"{'⭐' * entry.get('rating_stars', 5)}", size=9, color=ft.Colors.AMBER_600)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([
                                ft.Text(author_label, size=10, color=ft.Colors.PURPLE_800, weight=ft.FontWeight.W_500),
                                ft.Text(entry.get("created_at", ""), size=9, color=ft.Colors.GREY_500)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        ], spacing=2),
                        bgcolor=ft.Colors.WHITE,
                        padding=8,
                        border_radius=8,
                        border=ft.Border.all(1, ft.Colors.INDIGO_100),
                        on_click=make_click_handler(),
                        ink=True
                    )
                    list_container.controls.append(card)

                display_entry_detail(filtered_entries[0])
            else:
                list_container.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=ft.Colors.GREY_400, size=28),
                            ft.Text("Chưa có bài nào!", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                            ft.Text("Hãy học và đúc kết để bài học xuất hiện ở đây nhé!", size=9, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                        padding=12
                    )
                )
                detail_container.content = ft.Container(
                    content=ft.Text("Chưa có bài học nào theo bộ lọc này.", color=ft.Colors.GREY_500),
                    alignment=ft.Alignment.CENTER
                )
            self.page.update()

        # Nút chuyển bộ lọc
        btn_filter_all = ft.Container(
            content=ft.Text("Tất cả", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
            bgcolor=ft.Colors.INDIGO_100,
            padding=ft.Padding(8, 4, 8, 4),
            border_radius=6,
            ink=True
        )
        btn_filter_mine = ft.Container(
            content=ft.Text(f"Của em ({cur_user.display_name})", size=10, color=ft.Colors.GREY_700),
            bgcolor=ft.Colors.GREY_100,
            padding=ft.Padding(8, 4, 8, 4),
            border_radius=6,
            ink=True
        )

        def set_filter_all(_):
            active_filter[0] = "all"
            btn_filter_all.bgcolor = ft.Colors.INDIGO_100
            btn_filter_all.content.color = ft.Colors.INDIGO_900
            btn_filter_all.content.weight = ft.FontWeight.BOLD
            btn_filter_mine.bgcolor = ft.Colors.GREY_100
            btn_filter_mine.content.color = ft.Colors.GREY_700
            btn_filter_mine.content.weight = ft.FontWeight.NORMAL
            render_list()

        def set_filter_mine(_):
            active_filter[0] = "mine"
            btn_filter_mine.bgcolor = ft.Colors.PURPLE_100
            btn_filter_mine.content.color = ft.Colors.PURPLE_900
            btn_filter_mine.content.weight = ft.FontWeight.BOLD
            btn_filter_all.bgcolor = ft.Colors.GREY_100
            btn_filter_all.content.color = ft.Colors.GREY_700
            btn_filter_all.content.weight = ft.FontWeight.NORMAL
            render_list()

        btn_filter_all.on_click = set_filter_all
        btn_filter_mine.on_click = set_filter_mine

        filter_row = ft.Row([btn_filter_all, btn_filter_mine], spacing=4)

        left_column = ft.Container(
            content=ft.Column([
                filter_row,
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                list_container
            ], spacing=6, expand=True),
            width=250,
            border=ft.Border(right=ft.BorderSide(1, ft.Colors.GREY_200)),
            padding=ft.Padding(0, 0, 8, 0)
        )

        content_box = ft.Container(
            content=ft.Row([left_column, detail_container], spacing=12),
            width=780,
            height=480,
            padding=10
        )

        def close_dialog(_):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=ft.Colors.INDIGO_700, size=24),
                ft.Text("Sổ Tay Tự Học Của Em 📓", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                ft.Container(
                    content=ft.Row([
                        ft.Text(cur_user.avatar, size=13),
                        ft.Text(cur_user.display_name, size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900)
                    ], spacing=3),
                    bgcolor=ft.Colors.PURPLE_50,
                    padding=ft.Padding(6, 2, 8, 2),
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.PURPLE_200)
                )
            ], spacing=8),
            content=content_box,
            actions=[
                ft.FilledButton(
                    "Đóng Sổ Tay",
                    icon=ft.Icons.CLOSE_ROUNDED,
                    on_click=close_dialog,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        render_list()

        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _open_rubric_dashboard(self):
        """Mở Bảng Điều Khiển Đánh Giá Sư Phạm & 5 Chỉ Số Khoa Học (Mục 16.3 & Mục 3)."""
        from chuc_nang_8_rubric_danh_gia_tien_bo.rubric_view import RubricDashboardView
        from chuc_nang_8_rubric_danh_gia_tien_bo.rubric_engine import GLOBAL_RUBRIC_ENGINE

        problem_title = "Bài toán KHTN 7"
        problem_text = ""
        if self.state.confirmed_problem:
            problem_text = self.state.confirmed_problem.confirmed_text
            problem_title = self.state.classification_result.topic if self.state.classification_result else "Khoa học Tự nhiên 7"

        # Đánh giá dựa trên tiến trình hội thoại thực tế
        student_answers = []
        if hasattr(self, "socratic_view") and hasattr(self.socratic_view, "engine"):
            for m in self.socratic_view.engine.conversation_history:
                if m.sender == "student":
                    student_answers.append(m.content)

        if not student_answers:
            student_answers = [
                "Tia sáng bị hắt ngược trở lại chứ không đi qua",
                "Góc phản xạ luôn bằng góc tới i' = i",
                "Nó sẽ bị bật thẳng ngược trở lại theo phương tới"
            ]

        assessment = GLOBAL_RUBRIC_ENGINE.evaluate_session(
            problem_title=problem_title,
            problem_text=problem_text,
            student_answers=student_answers,
            turn_count=len(student_answers) + 1,
            unknown_count=0
        )

        dashboard = RubricDashboardView(page=self.page, assessment=assessment, is_standalone=False)

        def close_dialog(_):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.ASSESSMENT_ROUNDED, color=ft.Colors.PURPLE_800, size=24),
                ft.Text("Bảng Đánh Giá Tiến Bộ Sư Phạm (Rubric 0-6đ) & 5 Chỉ Số MVP (Mục 16.3 & 3)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=dashboard.build(),
                width=920,
                height=600,
            ),
            actions=[
                ft.FilledButton(
                    "Đóng bảng đánh giá",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def navigate_to_step_1(self):
        """Hiển thị Bước 1: Tiếp nhận đề bài."""
        self.state.current_step = AppStep.STEP_1_INPUT
        self._update_stepper_visuals(AppStep.STEP_1_INPUT)

        view_1 = ProblemInputView(
            page=self.page,
            on_confirm=self._on_step_1_confirmed,
            is_standalone=False
        )
        self.content_area.content = view_1.build()
        self.page.update()

    def _on_step_1_confirmed(self, problem: ProblemInput):
        """Khi học sinh gửi câu hỏi hoặc đề bài."""
        self.state.problem_input = problem

        # Nếu là ảnh chụp: Cho phép xem lại nhanh nội dung nhận diện từ ảnh
        if problem.input_type == InputType.IMAGE:
            self.navigate_to_step_2()
        else:
            # Gõ văn bản trực tiếp hoặc chọn bài mẫu: BỎ QUA HOÀN TOÀN OCR!
            # Tự động chuẩn hóa và phân tích kiến thức KHTN 7 trong nền
            normalized_text = normalize_khtn_text(problem.text_content)
            self.state.confirmed_problem = ConfirmedProblem(
                original_text=problem.text_content,
                confirmed_text=normalized_text,
                source_type="sample" if problem.input_type == InputType.SAMPLE else "text"
            )
            from chuc_nang_3_phan_loai_kien_thuc.classifier_engine import KnowledgeClassifier
            self.state.classification_result = KnowledgeClassifier().classify_problem(normalized_text)

            # VÀO THẲNG PHÒNG TRAO ĐỔI VỚI GIA SƯ SOCRATIC!
            self.navigate_to_step_4()


    def navigate_to_step_2(self):
        """Hiển thị Xác nhận chữ nhận dạng từ ảnh chụp (Chỉ dành cho tải ảnh)."""
        self.state.current_step = AppStep.STEP_2_OCR
        self._update_stepper_visuals(AppStep.STEP_2_OCR)

        problem = self.state.problem_input
        img_path = problem.file_path if (problem and problem.file_path) else None

        view_2 = OcrConfirmationView(
            page=self.page,
            image_path=img_path,
            on_confirm=self._on_step_2_confirmed,
            is_standalone=False
        )

        btn_back_to_1 = ft.OutlinedButton(
            "Quay lại đặt câu hỏi / Chọn lại đề",
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            on_click=lambda _: self.navigate_to_step_1()
        )

        step_2_container = ft.Column(
            [
                ft.Row([btn_back_to_1], alignment=ft.MainAxisAlignment.START),
                view_2.build()
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO
        )

        self.content_area.content = step_2_container
        self.page.update()

    def _on_step_2_confirmed(self, confirmed_problem: ConfirmedProblem):
        """Khi học sinh xác nhận văn bản từ ảnh -> Vào thẳng trò chuyện với Gia sư!"""
        self.state.confirmed_problem = confirmed_problem
        from chuc_nang_3_phan_loai_kien_thuc.classifier_engine import KnowledgeClassifier
        self.state.classification_result = KnowledgeClassifier().classify_problem(confirmed_problem.confirmed_text)
        self.navigate_to_step_4()

    def _show_concept_map_dialog(self):
        """Mở modal Bản đồ Khái niệm & Cảnh báo lỗi thường gặp (Chức năng 3)."""
        problem_text = self.state.confirmed_problem.confirmed_text if self.state.confirmed_problem else ""

        def close_dialog(_=None):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        view_3 = KnowledgeClassifierView(
            page=self.page,
            problem_text=problem_text,
            on_proceed_to_socratic=lambda _: close_dialog(),
            on_back=lambda: close_dialog(),
            is_standalone=False
        )

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.MAP_ROUNDED, color=ft.Colors.INDIGO_700, size=24),
                ft.Text("Bản Đồ Khái Niệm & Cảnh Báo Lỗi Thường Gặp (FR-03)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
            ], spacing=8),
            content=ft.Container(
                content=view_3.build(),
                width=880,
                height=580,
            ),
            actions=[
                ft.FilledButton(
                    "Đã hiểu, quay lại trò chuyện cùng Gia sư",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def navigate_to_step_3(self, confirmed_problem: ConfirmedProblem):
        """Dự phòng xem Bản đồ Khái niệm toàn trang nếu cần."""
        self._show_concept_map_dialog()

    def _on_step_3_proceed(self, classification_result: ClassificationResult):
        self.state.classification_result = classification_result
        self.navigate_to_step_4()

    def _show_not_summarized_dialog(self):
        """Hộp thoại thông báo khi học sinh bấm vào Sơ đồ tư duy dạng nhánh mà chưa đúc kết xong."""
        def close_dialog(_=None):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        def open_notebook_and_close(_=None):
            close_dialog()
            self._open_notebook_viewer()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.LOCK_ROUNDED, color=ft.Colors.AMBER_800, size=24),
                ft.Text("Bạn chưa đúc kết bài học!", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Em chưa hoàn thành đúc kết bài học cùng Thầy Socrates Nhí!",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_900
                    ),
                    ft.Text(
                        "Để mở khóa Sơ đồ Tư duy Dạng Nhánh (khái niệm cốt lõi SGK KHTN 7), em cần tiếp tục trao đổi cùng Thầy và tự đúc kết kiến thức cốt lõi ở cuối bài học nhé.",
                        size=12,
                        color=ft.Colors.GREY_800
                    ),
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE_ROUNDED, color=ft.Colors.CYAN_800, size=18),
                            ft.Text(
                                "💡 Lúc này, em chỉ có thể mở 'Sổ Tay Của Em 📓' để xem lại các kiến thức, công thức và bài học đã lưu từ trước thôi nhé!",
                                size=11.5,
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.CYAN_900,
                                expand=True
                            )
                        ], spacing=6),
                        bgcolor=ft.Colors.CYAN_50,
                        padding=10,
                        border_radius=8,
                        border=ft.Border.all(1, ft.Colors.CYAN_200)
                    )
                ], spacing=8, tight=True),
                width=480
            ),
            actions=[
                ft.FilledButton(
                    "Mở Sổ Tay Của Em 📓",
                    icon=ft.Icons.MENU_BOOK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_800, color=ft.Colors.WHITE),
                    on_click=open_notebook_and_close
                ),
                ft.OutlinedButton(
                    "Tiếp tục đúc kết cùng AI 💬",
                    on_click=close_dialog
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _show_congrats_unlock_dialog(self, turn_count: int = 4):
        """Hộp thoại thông báo chúc mừng đúc kết thành công và mở khóa Sơ đồ tư duy dạng nhánh."""
        def close_dialog(_=None):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        def go_to_mindmap(_=None):
            close_dialog()
            self.navigate_to_step_5(turn_count=turn_count)

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CELEBRATION_ROUNDED, color=ft.Colors.GREEN_700, size=26),
                ft.Text("Chúc Mừng Em Đã Đúc Kết Thành Công! 🎉", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Em đã hoàn thành trọn vẹn chu trình tự học và tự mình đúc kết kiến thức cốt lõi!",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_900
                    ),
                    ft.Text(
                        "🌿 Thầy Socrates Nhí đã chính thức mở khóa Sơ đồ Tư duy Dạng Nhánh (khái niệm cốt lõi SGK KHTN 7) cho em rồi đó!\n\n"
                        "Em hãy bấm nút bên dưới để khám phá sơ đồ rẽ nhánh và lưu bài học vào Sổ tay Tự học nhé!",
                        size=12,
                        color=ft.Colors.GREY_800
                    )
                ], spacing=6, tight=True),
                width=480
            ),
            actions=[
                ft.OutlinedButton(
                    "Xem lại trao đổi 💬",
                    on_click=close_dialog
                ),
                ft.FilledButton(
                    "Khám Phá Sơ Đồ Tư Duy Dạng Nhánh 🌿",
                    icon=ft.Icons.WORKSPACE_PREMIUM_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                    on_click=go_to_mindmap
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def navigate_to_step_4(self):
        """Hiển thị Bước 2: Chu trình đối thoại cùng Gia sư Socrates Nhí."""
        self.state.current_step = AppStep.STEP_4_SOCRATIC
        self._update_stepper_visuals(AppStep.STEP_4_SOCRATIC)

        problem_text = self.state.confirmed_problem.confirmed_text if self.state.confirmed_problem else ""

        self.socratic_view = SocraticChatView(
            page=self.page,
            problem_text=problem_text,
            on_session_complete=self._on_socratic_session_complete,
            is_standalone=False
        )

        btn_back_to_1 = ft.OutlinedButton(
            "Đặt câu hỏi khác / Chọn đề mới 📝",
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            on_click=lambda _: self.navigate_to_step_1()
        )

        btn_quick_notebook = ft.FilledButton(
            "Sổ Tay Của Em 📓",
            icon=ft.Icons.MENU_BOOK_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_800, color=ft.Colors.WHITE),
            tooltip="Bấm để mở Sổ tay Tự học (Xem lại các bài đã đúc kết và kiến thức cần nhớ)",
            on_click=lambda _: self._open_notebook_viewer()
        )

        def on_click_summary(_):
            if not self.state.is_socratic_completed:
                self._show_not_summarized_dialog()
            else:
                self.navigate_to_step_5()

        if self.state.is_socratic_completed:
            self.btn_to_summary = ft.FilledButton(
                "Xem Sơ đồ Tư duy Dạng Nhánh 🌿 (Đã mở khóa)",
                icon=ft.Icons.WORKSPACE_PREMIUM_ROUNDED,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                on_click=on_click_summary
            )
        else:
            self.btn_to_summary = ft.FilledButton(
                "Sơ đồ Tư duy Dạng Nhánh 🔒 (Cần đúc kết)",
                icon=ft.Icons.LOCK_ROUNDED,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_300, color=ft.Colors.GREY_700),
                on_click=on_click_summary
            )

        c_res = self.state.classification_result
        topic_title = c_res.topic if c_res else "Khoa học Tự nhiên 7"
        concepts_str = ", ".join(c_res.core_concepts) if (c_res and c_res.core_concepts) else "Quy luật KHTN"

        info_badge = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.INDIGO_700, size=16),
                    ft.Text(f"💡 {topic_title} • Khái niệm: {concepts_str}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                ft.TextButton(
                    "Xem Bản đồ Khái niệm 🗺️",
                    on_click=lambda _: self._show_concept_map_dialog()
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.INDIGO_50,
            padding=ft.Padding(12, 6, 12, 6),
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.INDIGO_200)
        )

        step_4_container = ft.Column(
            [
                ft.Row([
                    btn_back_to_1,
                    ft.Row([btn_quick_notebook, self.btn_to_summary], spacing=8)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                info_badge,
                self.socratic_view.build()
            ],
            spacing=8,
            expand=True
        )

        self.content_area.content = step_4_container
        self.page.update()

    def _on_socratic_session_complete(self, summary_data: dict):
        """Xử lý khi học sinh đúc kết thành công -> Đánh dấu hoàn thành, mở khóa sơ đồ và thông báo."""
        print(f"[Hoàn thành tự đúc kết] Lượt: {summary_data.get('turn_count')} - Pha: {summary_data.get('next_phase')}")
        self.state.is_socratic_completed = True

        # Cập nhật nút Sơ đồ tư duy dạng nhánh sang trạng thái ĐÃ MỞ KHÓA
        if hasattr(self, "btn_to_summary") and self.btn_to_summary:
            def on_click_summary(_):
                self.navigate_to_step_5()

            self.btn_to_summary.text = "Xem Sơ đồ Tư duy Dạng Nhánh 🌿 (Đã mở khóa)"
            self.btn_to_summary.icon = ft.Icons.WORKSPACE_PREMIUM_ROUNDED
            self.btn_to_summary.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
            self.btn_to_summary.on_click = on_click_summary
            try:
                self.btn_to_summary.update()
            except Exception:
                pass

        # Hiển thị thông báo chúc mừng & mở khóa
        turn_count = summary_data.get("turn_count", 4)
        self._show_congrats_unlock_dialog(turn_count=turn_count)

    def navigate_to_step_5(self, turn_count: int = 4):
        """Hiển thị Bước 5: Sơ đồ Tư duy & Tổng kết Khép phiên Học tập (Chức năng 5)."""
        self.state.current_step = AppStep.STEP_5_MINDMAP
        self._update_stepper_visuals(AppStep.STEP_5_MINDMAP)

        problem_text = self.state.confirmed_problem.confirmed_text if self.state.confirmed_problem else ""
        c_res = self.state.classification_result

        topic = c_res.topic if c_res else "Vật lý – Chuyển động và Tốc độ"
        strand = c_res.strand.value if c_res else "Vật lý THCS"
        facts = c_res.given_facts if c_res else ["s = 12 km", "t = 30 phút"]
        concepts = c_res.core_concepts if c_res else ["Tốc độ chuyển động"]
        target = c_res.target_variable if c_res else "Tốc độ v"

        view_5 = MindmapSummaryView(
            page=self.page,
            problem_text=problem_text,
            topic=topic,
            strand_name=strand,
            given_facts=facts,
            core_concepts=concepts,
            target_variable=target,
            total_turns=turn_count,
            on_restart=self.navigate_to_step_1,
            is_standalone=False
        )

        btn_back_to_4 = ft.OutlinedButton(
            "Quay lại trao đổi cùng Gia sư 💬",
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            on_click=lambda _: self.navigate_to_step_4()
        )

        btn_view_rubric = ft.FilledButton(
            "Xem Phiếu Chấm Rubric Tiến Bộ (0-6đ) 📊",
            icon=ft.Icons.ASSESSMENT_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE),
            on_click=lambda _: self._open_rubric_dashboard()
        )

        btn_open_nb = ft.FilledButton(
            "Mở Sổ Tay Của Em 📓",
            icon=ft.Icons.MENU_BOOK_ROUNDED,
            style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_800, color=ft.Colors.WHITE),
            on_click=lambda _: self._open_notebook_viewer()
        )

        step_5_container = ft.Column(
            [
                ft.Row([btn_back_to_4, ft.Row([btn_open_nb, btn_view_rubric], spacing=8)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                view_5.build()
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO
        )

        self.content_area.content = step_5_container
        self.page.update()

    def build(self) -> ft.Control:
        """Trả về toàn bộ khung ứng dụng hoàn chỉnh (điều phối Màn hình Đăng nhập và Không gian học tập)."""
        return self.main_container


def main(page: ft.Page):
    app = SocratesIntegratedApp(page)
    page.add(app.build())


if __name__ == "__main__":
    from app_tich_hop_socrates.app_launcher import safe_run_app
    safe_run_app(main)

