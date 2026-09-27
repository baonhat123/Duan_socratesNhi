"""
Module: classifier_view.py
Chức năng 3 (FR-03): Giao diện Bản đồ Phân loại Kiến thức KHTN 7
Đặc tả: Socrates Nhí v3.0 (Tương thích Flet 1.0+)

Giao diện trực quan và sư phạm:
1. Huy hiệu Mạch kiến thức (Cơ học, Hóa học, Sinh học) & Cấp độ nhận thức (Cơ bản, Thông hiểu, Vận dụng).
2. Thẻ dữ kiện cho trước (facts) và đại lượng cần tìm (target variable).
3. Các thẻ Khái niệm cốt lõi (Tối đa 3 thẻ chọn từ bản đồ đội soạn kèm công thức chuẩn).
4. Thẻ cảnh báo "Lỗi sai thường gặp cần tránh" để chuẩn bị tâm thế tự học.
5. Nút điều hướng tiếp tục sang Hội thoại Socratic 5 pha.
"""

from typing import Optional, Callable
import flet as ft

from .classifier_model import ClassificationResult, KnowledgeStrand, DifficultyLevel
from .classifier_engine import KnowledgeClassifier
from .concept_bank import CONCEPT_MAP


class KnowledgeClassifierView:
    """
    Component giao diện Flet cho Chức năng 3: Phân loại kiến thức bài toán & Bản đồ khái niệm.
    Phiên bản Giao diện Ed-Tech 2.0 Thân thiện Học sinh THCS.
    """
    def __init__(
        self,
        page: ft.Page,
        problem_text: str = "",
        on_proceed_to_socratic: Optional[Callable[[ClassificationResult], None]] = None,
        on_back: Optional[Callable[[], None]] = None,
        is_standalone: bool = False
    ):
        self.page = page
        self.problem_text = problem_text or (
            "Một người đi xe đạp chuyển động đều trên quãng đường thẳng s = 12 km "
            "trong thời gian t = 30 phút. Hãy xác định tốc độ v của người đó theo đơn vị km/h và m/s."
        )
        self.on_proceed = on_proceed_to_socratic
        self.on_back = on_back
        self.is_standalone = is_standalone

        self.classifier = KnowledgeClassifier()
        self.result = self.classifier.classify_problem(self.problem_text)

        # Xây dựng giao diện
        self._build_controls()

    def _build_controls(self):
        # 1. Header độc lập (Chỉ hiển thị khi chạy riêng lẻ Chức năng 3)
        self.standalone_header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_600, size=28),
                    ft.Text("Socrates Nhí 💡", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                ]),
                ft.Text("Chức năng 3: Phân loại kiến thức bài toán & Bản đồ khái niệm KHTN 7 (FR-03)", size=13, color=ft.Colors.GREY_700),
                ft.Container(height=5)
            ]),
            visible=self.is_standalone
        )

        # 2. Thẻ chỉ dẫn nhiệm vụ Trạm 3 (Mission Briefing Card)
        self.mission_card = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.EXPLORE_ROUNDED, color=ft.Colors.INDIGO_700, size=22),
                    bgcolor=ft.Colors.INDIGO_50,
                    radius=20
                ),
                ft.Column([
                    ft.Text("Trạm 3: Bản đồ Khái niệm & Phân loại bài toán KHTN", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.INDIGO_900),
                    ft.Text(
                        "Socrates Nhí đã tự động bóc tách dữ kiện, phân môn KHTN 7 và đề xuất các khái niệm cốt lõi. "
                        "Em hãy xem kỹ phần tóm tắt 'Cho gì & Tìm gì' trước khi bắt đầu nhé!",
                        size=12,
                        color=ft.Colors.GREY_700
                    )
                ], spacing=2, expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            padding=14,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.INDIGO_100),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        # 3. Thẻ Phân loại Mạch Kiến Thức & Cấp Độ Nhận Thức
        strand_theme = {
            KnowledgeStrand.MECHANICS: {
                "name": "Mạch 1: Vật lý THCS (Cơ học & Năng lượng)",
                "icon": ft.Icons.DIRECTIONS_BIKE_ROUNDED,
                "color": ft.Colors.INDIGO_700,
                "bg": ft.Colors.INDIGO_50,
                "border": ft.Colors.INDIGO_200
            },
            KnowledgeStrand.CHEMISTRY: {
                "name": "Mạch 2: Hóa học THCS (Chất & Sự biến đổi chất)",
                "icon": ft.Icons.SCIENCE_ROUNDED,
                "color": ft.Colors.TEAL_700,
                "bg": ft.Colors.TEAL_50,
                "border": ft.Colors.TEAL_200
            },
            KnowledgeStrand.BIOLOGY: {
                "name": "Mạch 3: Sinh học THCS (Vật sống & Môi trường)",
                "icon": ft.Icons.ECO_ROUNDED,
                "color": ft.Colors.GREEN_700,
                "bg": ft.Colors.GREEN_50,
                "border": ft.Colors.GREEN_200
            }
        }.get(self.result.strand, {
            "name": "Khoa học Tự nhiên 7",
            "icon": ft.Icons.CATEGORY_ROUNDED,
            "color": ft.Colors.INDIGO_700,
            "bg": ft.Colors.INDIGO_50,
            "border": ft.Colors.INDIGO_200
        })

        diff_badge_data = {
            DifficultyLevel.BASIC: ("Cơ bản (Nhận biết dữ kiện)", ft.Colors.GREEN_700, ft.Colors.GREEN_50, ft.Colors.GREEN_200),
            DifficultyLevel.UNDERSTANDING: ("Thông hiểu (Vận dụng 1 bước)", ft.Colors.AMBER_800, ft.Colors.AMBER_50, ft.Colors.AMBER_200),
            DifficultyLevel.APPLICATION: ("Vận dụng (Đổi đơn vị & Suy luận)", ft.Colors.PURPLE_700, ft.Colors.PURPLE_50, ft.Colors.PURPLE_200),
        }.get(self.result.difficulty, ("Chuẩn KHTN 7", ft.Colors.INDIGO_700, ft.Colors.INDIGO_50, ft.Colors.INDIGO_200))

        self.classification_banner = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(strand_theme["icon"], color=strand_theme["color"], size=22),
                    ft.Column([
                        ft.Text(strand_theme["name"], weight=ft.FontWeight.BOLD, size=13, color=strand_theme["color"]),
                        ft.Text(f"Chủ đề: {self.result.topic}", size=12, color=ft.Colors.GREY_800)
                    ], spacing=1)
                ], spacing=8),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.BAR_CHART_ROUNDED, color=diff_badge_data[1], size=16),
                        ft.Text(f"Cấp độ: {diff_badge_data[0]}", weight=ft.FontWeight.BOLD, size=11, color=diff_badge_data[1])
                    ]),
                    bgcolor=diff_badge_data[2],
                    padding=ft.Padding(10, 5, 10, 5),
                    border_radius=12,
                    border=ft.Border.all(1, diff_badge_data[3])
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=strand_theme["bg"],
            padding=12,
            border_radius=12,
            border=ft.Border.all(1, strand_theme["border"])
        )

        # 4. KHỐI TÓM TẮT BÀI TOÁN: "CHO GÌ & TÌM GÌ?" (Given vs Target)
        fact_chips = []
        for fact in self.result.given_facts:
            chip = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_ROUNDED, color=ft.Colors.BLUE_700, size=14),
                    ft.Text(fact, size=12, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_900)
                ], spacing=4),
                bgcolor=ft.Colors.WHITE,
                padding=ft.Padding(8, 4, 8, 4),
                border_radius=8,
                border=ft.Border.all(1, ft.Colors.BLUE_200)
            )
            fact_chips.append(chip)

        if not fact_chips:
            fact_chips.append(
                ft.Text("Đang phân tích dữ kiện từ bài toán...", size=12, italic=True, color=ft.Colors.GREY_600)
            )

        self.given_box = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PUSH_PIN_ROUNDED, color=ft.Colors.BLUE_700, size=16),
                    ft.Text("Dữ kiện đã cho (Giả thiết):", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.BLUE_900)
                ], spacing=6),
                ft.Row(fact_chips, wrap=True, spacing=6)
            ], spacing=8),
            bgcolor=ft.Colors.BLUE_50,
            padding=12,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.BLUE_200),
            expand=True
        )

        self.target_box = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.FLAG_CIRCLE_ROUNDED, color=ft.Colors.AMBER_800, size=18),
                    ft.Text("Mục tiêu cần tính (Kết luận):", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.AMBER_900)
                ], spacing=6),
                ft.Container(
                    content=ft.Text(
                        self.result.target_variable or "Đại lượng theo yêu cầu bài toán",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.AMBER_900
                    ),
                    bgcolor=ft.Colors.WHITE,
                    padding=ft.Padding(10, 6, 10, 6),
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.AMBER_300)
                )
            ], spacing=8),
            bgcolor=ft.Colors.AMBER_50,
            padding=12,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.AMBER_200),
            expand=True
        )

        self.facts_target_row = ft.Row([self.given_box, self.target_box], spacing=10)

        # 5. KHỐI BẢN ĐỒ KHÁI NIỆM CỐT LÕI (Core Concept Flashcards - Max 3)
        concept_cards = []
        for c_name in self.result.core_concepts[:3]:
            matched_c = next((c for c in CONCEPT_MAP.values() if c.name == c_name), None)
            formula_text = matched_c.formula if matched_c and matched_c.formula else "Quy luật KHTN"
            desc_text = matched_c.description if matched_c else "Khái niệm nền tảng trong chương trình KHTN 7."

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.LIGHTBULB_CIRCLE_ROUNDED, color=ft.Colors.INDIGO_600, size=18),
                        ft.Text(c_name, weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.INDIGO_900),
                    ], spacing=6),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.FUNCTIONS_ROUNDED, size=16, color=ft.Colors.INDIGO_800),
                            ft.Text(formula_text, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                        ], spacing=6),
                        bgcolor=ft.Colors.INDIGO_50,
                        padding=ft.Padding(10, 6, 10, 6),
                        border_radius=8,
                        border=ft.Border.all(1, ft.Colors.INDIGO_200)
                    ),
                    ft.Text(desc_text, size=11, color=ft.Colors.GREY_700)
                ], spacing=6),
                bgcolor=ft.Colors.WHITE,
                padding=12,
                border_radius=12,
                border=ft.Border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.03, ft.Colors.BLACK), offset=ft.Offset(0, 1)),
                expand=True
            )
            concept_cards.append(card)

        self.concepts_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.HUB_ROUNDED, color=ft.Colors.INDIGO_700, size=18),
                    ft.Text("Bản đồ Khái niệm Cốt lõi (Tối đa 3 khái niệm do đội biên soạn):", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
                ], spacing=6),
                ft.Row(concept_cards, spacing=10)
            ], spacing=8)
        )

        # 6. CHIẾC KHIÊN CẢNH BÁO: BẪY SAI LẦM CẦN TRÁNH (Pitfall Shield)
        mistake_items = []
        for m in self.result.common_mistakes[:3]:
            mistake_items.append(
                ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_900, size=16),
                    ft.Text(m, size=12, color=ft.Colors.AMBER_900, expand=True)
                ], spacing=6)
            )

        if not mistake_items:
            mistake_items.append(
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.AMBER_900, size=16),
                    ft.Text("Luôn đối chiếu đơn vị đo lường trước khi áp dụng công thức tính toán.", size=12, color=ft.Colors.AMBER_900)
                ], spacing=6)
            )

        self.pitfalls_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SHIELD_ROUNDED, color=ft.Colors.AMBER_900, size=18),
                    ft.Text("Chiếc khiên cảnh giác: Bẫy sai lầm học sinh THCS thường mắc phải:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
                ], spacing=6),
                ft.Column(mistake_items, spacing=4)
            ], spacing=6),
            bgcolor=ft.Colors.AMBER_50,
            border=ft.Border.all(1.5, ft.Colors.AMBER_300),
            border_radius=12,
            padding=12
        )

        # 7. XEM TRƯỚC LỘ TRÌNH 5 PHA SOCRATIC
        self.phases_preview = ft.Container(
            content=ft.Row([
                ft.Text("Lộ trình 5 Pha gợi mở sắp tới:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                ft.Text("1. Làm rõ đề  ➜  2. Nhớ kiến thức  ➜  3. Lập luận  ➜  4. Tự kiểm tra  ➜  5. Đúc kết", size=11, color=ft.Colors.INDIGO_700, weight=ft.FontWeight.W_500)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.GREY_50,
            padding=ft.Padding(12, 6, 12, 6),
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.GREY_200)
        )

        # 8. Dải nút điều hướng
        self.btn_proceed = ft.FilledButton(
            "Bắt đầu Hội thoại Gợi mở Socratic 5 Pha 🚀",
            icon=ft.Icons.FORUM_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.INDIGO_700,
                color=ft.Colors.WHITE,
                padding=20
            ),
            on_click=self._on_proceed_click
        )

        self.btn_back = ft.OutlinedButton(
            "Quay lại Bước 2 (Soát lại OCR)",
            icon=ft.Icons.ARROW_BACK,
            on_click=self._on_back_click
        )

    def _on_proceed_click(self, e):
        """Chuyển tiếp sang Bước 4 (Hội thoại Socratic)."""
        if self.on_proceed:
            self.on_proceed(self.result)

    def _on_back_click(self, e):
        """Quay lại màn hình trước."""
        if self.on_back:
            self.on_back()

    def build(self) -> ft.Control:
        """Trả về toàn bộ giao diện của Chức năng 3."""
        return ft.Container(
            content=ft.Column(
                [
                    self.standalone_header,
                    self.mission_card,
                    ft.Container(height=4),
                    self.classification_banner,
                    ft.Container(height=4),
                    self.facts_target_row,
                    ft.Container(height=4),
                    self.concepts_section,
                    ft.Container(height=4),
                    self.pitfalls_card,
                    ft.Container(height=2),
                    self.phases_preview,
                    ft.Container(height=8),
                    ft.Row(
                        [self.btn_proceed, self.btn_back],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=15
                    )
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=ft.Padding(20, 10, 20, 20)
        )
