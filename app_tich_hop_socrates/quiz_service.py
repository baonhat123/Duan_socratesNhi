# -*- coding: utf-8 -*-
"""
Module: quiz_service.py
Chức năng: Quản lý Bài Kiểm Tra Củng Cố Kiến Thức (Trắc Nghiệm & Tự Luận) & Ôn Tập Ngắt Quãng
Đặc tả dự án: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Nguyên tắc thiết kế Sư phạm Socratic:
1. "Học xong kiểm tra ngay" (Post-Lesson Check): Đánh giá mức độ làm chủ kiến thức ngay sau khi đúc kết bản đồ tư duy.
2. "Ôn tập ngày hôm sau" (Spaced Repetition Review): Gợi nhớ kiến thức ngắt quãng để ghi nhớ dài hạn.
3. Đa dạng hình thức:
   - Trắc nghiệm khách quan: 3 câu chọn 1 trong 4 đáp án (A, B, C, D) có phản hồi sư phạm giải thích vì sao đúng/sai.
   - Tự luận ngắn thực tế: 1 câu hỏi mở ứng dụng đời sống, học sinh tự diễn đạt, hệ thống chấm điểm và nhận xét gợi mở.
4. Báo cáo minh bạch: Lưu kết quả vào Sổ tay Tự học và đồng bộ sang Cổng Phụ Huynh.
5. Vận hành Offline 100% (có sẵn ngân hàng 12 chủ đề chuẩn KHTN 7) và Online linh hoạt qua AI.
"""

import json
import os
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
AUTH_DIR = WORKSPACE_ROOT / "so_tay_hoc_tap"
QUIZ_HISTORY_FILE = AUTH_DIR / "lich_su_kiem_tra.json"


@dataclass
class QuizQuestion:
    """Mô hình dữ liệu của một câu hỏi kiểm tra."""
    question_id: str
    q_type: str                         # "mcq" (Trắc nghiệm) hoặc "essay" (Tự luận)
    prompt: str                         # Nội dung câu hỏi
    options: List[str] = field(default_factory=list)  # Các lựa chọn A, B, C, D
    correct_index: int = 0              # Đáp án đúng (0: A, 1: B, 2: C, 3: D)
    explanation: str = ""               # Giải thích sư phạm vì sao đáp án đó đúng
    hint: str = ""                      # Gợi ý tư duy của Socrates
    key_points: List[str] = field(default_factory=list) # Từ khóa tiêu chí chấm tự luận
    sample_answer: str = ""             # Đáp án mẫu chuẩn SGK cho câu tự luận


@dataclass
class QuizRecord:
    """Bản ghi kết quả bài kiểm tra của học sinh."""
    quiz_id: str
    username: str
    student_name: str
    topic: str
    strand: str                         # "Vật lý", "Hóa học", "Sinh học"
    quiz_type: str                      # "pre_test" (Đầu vào), "post_lesson"/"post_test" (Đầu ra), "daily_review" (Ôn tập)
    created_at: str
    score: float                        # Thang điểm 10 (vd: 8.5)
    total_mcq: int
    correct_mcq: int
    essay_score: float                  # Thang điểm 4 (vd: 3.5)
    essay_feedback: str
    student_essay_answer: str
    badge_earned: str                   # "Xuất Sắc ⭐", "Khá Giỏi 🌟", "Đạt Chuẩn 💡"
    details: List[Dict[str, Any]] = field(default_factory=list)
    pre_test_score: Optional[float] = None       # Điểm bài khảo sát đầu vào (Pre-test)
    learning_gain: Optional[float] = None        # Độ tăng điểm số (Post - Pre)
    gain_percent: Optional[float] = None         # Tỷ lệ tiến bộ (%)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuizRecord":
        return cls(
            quiz_id=data.get("quiz_id", ""),
            username=data.get("username", ""),
            student_name=data.get("student_name", ""),
            topic=data.get("topic", ""),
            strand=data.get("strand", ""),
            quiz_type=data.get("quiz_type", "post_lesson"),
            created_at=data.get("created_at", ""),
            score=float(data.get("score", 0.0)),
            total_mcq=int(data.get("total_mcq", 3)),
            correct_mcq=int(data.get("correct_mcq", 0)),
            essay_score=float(data.get("essay_score", 0.0)),
            essay_feedback=data.get("essay_feedback", ""),
            student_essay_answer=data.get("student_essay_answer", ""),
            badge_earned=data.get("badge_earned", ""),
            details=list(data.get("details", [])),
            pre_test_score=data.get("pre_test_score"),
            learning_gain=data.get("learning_gain"),
            gain_percent=data.get("gain_percent")
        )


# =============================================================================
# NGÂN HÀNG HỌC LIỆU CÂU HỎI KIỂM TRA CHUẨN KHTN 7 (OFFLINE CACHE BANK)
# =============================================================================
QUIZ_BANK: Dict[str, List[QuizQuestion]] = {
    # -------------------------------------------------------------------------
    # 1. TỐC ĐỘ CHUYỂN ĐỘNG & ĐƠN VỊ ĐO (VẬT LÝ)
    # -------------------------------------------------------------------------
    "chuyen_dong_toc_do": [
        QuizQuestion(
            question_id="CD_MCQ_1",
            q_type="mcq",
            prompt="Công thức nào sau đây dùng để xác định tốc độ chuyển động của một vật khi biết quãng đường s và thời gian t?",
            options=["A. v = s . t", "B. v = s / t", "C. v = t / s", "D. v = s + t"],
            correct_index=1,
            explanation="Tốc độ là đại lượng đặc trưng cho sự nhanh chậm của chuyển động, được tính bằng thương số giữa quãng đường đi được và khoảng thời gian đi quãng đường đó: v = s / t.",
            hint="Nhớ lại: Muốn biết trong 1 giây vật đi được bao nhiêu mét, ta lấy tổng quãng đường chia cho tổng thời gian."
        ),
        QuizQuestion(
            question_id="CD_MCQ_2",
            q_type="mcq",
            prompt="Một người đi xe máy với tốc độ 36 km/h. Giá trị tốc độ này tương ứng với bao nhiêu m/s?",
            options=["A. 5 m/s", "B. 10 m/s", "C. 15 m/s", "D. 20 m/s"],
            correct_index=1,
            explanation="Quy tắc đổi đơn vị chuẩn KHTN: Muốn đổi từ km/h sang m/s ta chia cho 3,6. Do đó: 36 / 3,6 = 10 m/s.",
            hint="1 km = 1000 m; 1 h = 3600 s. Ta lấy 36 x 1000 / 3600 = 10 m/s."
        ),
        QuizQuestion(
            question_id="CD_MCQ_3",
            q_type="mcq",
            prompt="Một đoàn tàu đi được quãng đường 120 km trong thời gian 2 giờ 30 phút. Tốc độ của đoàn tàu là:",
            options=["A. 48 km/h", "B. 50 km/h", "C. 60 km/h", "D. 40 km/h"],
            correct_index=0,
            explanation="Đổi 2 giờ 30 phút = 2,5 giờ. Tốc độ của tàu là: v = s / t = 120 / 2,5 = 48 km/h.",
            hint="Hãy đổi thời gian phút sang giờ trước khi thay vào công thức v = s / t nhé!"
        ),
        QuizQuestion(
            question_id="CD_ESSAY_1",
            q_type="essay",
            prompt="Tại sao trên các đoạn đường gần cổng trường học thường cắm biển báo giới hạn tốc độ 30 km/h? Em hãy giải thích lý do dựa trên mối liên hệ giữa tốc độ và khoảng cách dừng xe an toàn.",
            options=[],
            correct_index=0,
            explanation="Tốc độ càng cao thì quãng đường hãm phanh càng dài và thời gian phản xạ của tài xế càng hẹp. Giảm tốc độ xuống 30 km/h giúp giảm quãng đường dừng xe, bảo vệ an toàn cho học sinh qua đường.",
            hint="Hãy nhắc đến hai yếu tố: Thời gian phản ứng của tài xế và quãng đường phanh khi gặp sự cố bất ngờ.",
            key_points=["quãng đường phanh", "thời gian phản xạ", "an toàn", "dừng xe"],
            sample_answer="Khi xe chạy với tốc độ càng cao thì động năng càng lớn, khiến quãng đường phanh để dừng hẳn xe càng dài. Khu vực cổng trường học có nhiều học sinh qua lại bất ngờ; việc giới hạn tốc độ 30 km/h giúp người lái xe có đủ thời gian phản xạ và quãng đường phanh ngắn hơn, kịp thời dừng xe tránh tai nạn."
        )
    ],

    # -------------------------------------------------------------------------
    # 2. PHẢN XẠ ÁNH SÁNG & GƯƠNG PHẲNG (VẬT LÝ)
    # -------------------------------------------------------------------------
    "anh_sang_guong_phang": [
        QuizQuestion(
            question_id="AS_MCQ_1",
            q_type="mcq",
            prompt="Theo định luật phản xạ ánh sáng, nếu góc tới i = 35° thì góc phản xạ i' có độ lớn là bao nhiêu?",
            options=["A. 70°", "B. 55°", "C. 35°", "D. 90°"],
            correct_index=2,
            explanation="Định luật phản xạ ánh sáng khẳng định: Góc phản xạ luôn luôn bằng góc tới (i' = i). Do đó i' = 35°.",
            hint="Tia phản xạ đối xứng với tia tới qua pháp tuyến của mặt gương."
        ),
        QuizQuestion(
            question_id="AS_MCQ_2",
            q_type="mcq",
            prompt="Đặc điểm nào sau đây KHÔNG PHẢI là tính chất ảnh của một vật tạo bởi gương phẳng?",
            options=[
                "A. Ảnh là ảnh ảo không hứng được trên màn chắn",
                "B. Độ lớn của ảnh luôn lớn hơn độ lớn của vật",
                "C. Khoảng cách từ ảnh đến gương bằng khoảng cách từ vật đến gương",
                "D. Độ lớn của ảnh bằng độ lớn của vật"
            ],
            correct_index=1,
            explanation="Ảnh tạo bởi gương phẳng luôn có kích thước bằng đúng kích thước của vật, không lớn hơn cũng không nhỏ hơn.",
            hint="Em hãy soi gương phẳng mỗi ngày: Khuôn mặt em trong gương to hơn, nhỏ hơn hay bằng mặt thật?"
        ),
        QuizQuestion(
            question_id="AS_MCQ_3",
            q_type="mcq",
            prompt="Chiếu một tia sáng vuông góc với bề mặt gương phẳng. Góc tới và góc phản xạ trong trường hợp này lần lượt là:",
            options=["A. 90° và 90°", "B. 0° và 0°", "C. 0° và 90°", "D. 45° và 45°"],
            correct_index=1,
            explanation="Góc tới là góc hợp bởi tia tới và pháp tuyến. Khi tia sáng vuông góc với gương, tia tới trùng với pháp tuyến nên góc tới i = 0° => góc phản xạ i' = 0°.",
            hint="Góc tới tính từ tia tới đến đường pháp tuyến (đường vuông góc với mặt gương)."
        ),
        QuizQuestion(
            question_id="AS_ESSAY_1",
            q_type="essay",
            prompt="Tại sao trên các xe cứu thương, chữ 'AMBULANCE' ở đầu xe lại thường được in ngược từ phải sang trái (Chữ ngược)?",
            options=[],
            correct_index=0,
            explanation="Do tính chất đối xứng của ảnh qua gương phẳng, tài xế xe phía trước nhìn qua gương chiếu hậu sẽ thấy hình ảnh đảo ngược trở lại thành chữ xuôi bình thường để nhường đường kịp thời.",
            hint="Gương chiếu hậu của xe phía trước tạo ra ảnh có tính chất đối xứng trái - phải như thế nào?",
            key_points=["gương chiếu hậu", "đối xứng", "ảnh ngược", "nhường đường"],
            sample_answer="Gương phẳng có tính chất tạo ảnh đối xứng với vật qua mặt gương (đảo ngược chiều trái - phải). Khi chữ AMBULANCE được in ngược sẵn ở đầu xe, tài xế xe chạy phía trước nhìn vào gương chiếu hậu sẽ thấy chữ đảo ngược lại thành xuôi bình thường, từ đó nhận diện ngay xe cứu thương và chủ động nhường đường."
        )
    ],

    # -------------------------------------------------------------------------
    # 3. QUANG HỢP Ở THỰC VẬT (SINH HỌC)
    # -------------------------------------------------------------------------
    "quang_hop_thuc_vat": [
        QuizQuestion(
            question_id="QH_MCQ_1",
            q_type="mcq",
            prompt="Bào quan nào trong tế bào thực vật trực tiếp thực hiện quá trình quang hợp?",
            options=["A. Ti thể", "B. Nhân tế bào", "C. Lục lạp (chứa diệp lục)", "D. Không bào"],
            correct_index=2,
            explanation="Lục lạp chứa chất diệp lục có khả năng hấp thụ năng lượng ánh sáng mặt trời để tổng hợp chất hữu cơ.",
            hint="Bào quan này có màu xanh lục đặc trưng ở lá cây."
        ),
        QuizQuestion(
            question_id="QH_MCQ_2",
            q_type="mcq",
            prompt="Sản phẩm của quá trình quang hợp ở thực vật bao gồm những chất nào sau đây?",
            options=[
                "A. Nước và khí Carbon dioxide",
                "B. Chất hữu cơ (Glucose) và khí Oxygen",
                "C. Khí Nitrogen và muối khoáng",
                "D. Khí Carbon dioxide và năng lượng nhiệt"
            ],
            correct_index=1,
            explanation="Phương trình quang hợp: Nước + Carbon dioxide + Năng lượng ánh sáng -> Chất hữu cơ (Glucose) + Oxygen.",
            hint="Quá trình này tạo ra chất dinh dưỡng cho cây và nhả ra khí cần thiết cho hô hấp của sinh vật."
        ),
        QuizQuestion(
            question_id="QH_MCQ_3",
            q_type="mcq",
            prompt="Cấu trúc nào trên bề mặt biểu bì lá cây đóng vai trò chủ yếu trong việc trao đổi khí và thoát hơi nước?",
            options=["A. Gân lá", "B. Khí khổng", "C. Cuống lá", "D. Diệp lục"],
            correct_index=1,
            explanation="Khí khổng có hai tế bào hình hạt đậu có khả năng đóng mở, là cửa ngõ trao đổi khí CO2, O2 và thoát hơi nước.",
            hint="Bộ phận này có khả năng đóng mở linh hoạt tùy vào điều kiện ánh sáng và độ ẩm."
        ),
        QuizQuestion(
            question_id="QH_ESSAY_1",
            q_type="essay",
            prompt="Tại sao khi nuôi cá cảnh trong bể kính kín trong nhà, người ta thường trồng thêm rong đuôi chó hoặc cây thủy sinh nhỏ?",
            options=[],
            correct_index=0,
            explanation="Cây thủy sinh quang hợp dưới ánh đèn sẽ hấp thụ khí CO2 do cá thải ra và nhả khí O2 hòa tan vào nước giúp cá hô hấp, đồng thời lọc sạch môi trường nước.",
            hint="Em hãy liên hệ giữa quá trình hô hấp của cá (thải CO2, cần O2) và quá trình quang hợp của rong thủy sinh.",
            key_points=["quang hợp", "oxygen", "carbon dioxide", "hô hấp của cá"],
            sample_answer="Khi có ánh sáng, rong thủy sinh sẽ thực hiện quá trình quang hợp: hấp thụ khí Carbon dioxide (CO2) do cá thải ra và nhả ra khí Oxygen (O2) hòa tan trong nước. Lượng Oxygen này cung cấp trực tiếp cho cá hô hấp và sinh trưởng khỏe mạnh, đồng thời giúp cân bằng hệ sinh thái trong bể cá."
        )
    ],

    # -------------------------------------------------------------------------
    # 4. ĐỊNH LUẬT BẢO TOÀN KHỐI LƯỢNG & PHẢN ỨNG HÓA HỌC (HÓA HỌC)
    # -------------------------------------------------------------------------
    "bao_toan_khoi_luong": [
        QuizQuestion(
            question_id="BT_MCQ_1",
            q_type="mcq",
            prompt="Định luật bảo toàn khối lượng khẳng định: Trong một phản ứng hóa học,",
            options=[
                "A. Tổng khối lượng các chất sản phẩm lớn hơn chất tham gia",
                "B. Tổng khối lượng các chất sản phẩm bằng tổng khối lượng các chất tham gia",
                "C. Tổng khối lượng các chất sản phẩm nhỏ hơn chất tham gia",
                "D. Khối lượng luôn bị hao hụt thành năng lượng"
            ],
            correct_index=1,
            explanation="Theo định luật Lomonosov - Lavoisier: Tổng khối lượng của các chất sản phẩm luôn bằng tổng khối lượng của các chất tham gia phản ứng.",
            hint="Trong phản ứng hóa học, số lượng các nguyên tử của mỗi nguyên tố được giữ nguyên vẹn."
        ),
        QuizQuestion(
            question_id="BT_MCQ_2",
            q_type="mcq",
            prompt="Đốt cháy hoàn toàn 12 gam Carbon (than đá) cần dùng vừa đủ 32 gam khí Oxygen. Khối lượng khí Carbon dioxide (CO2) sinh ra là:",
            options=["A. 20 gam", "B. 40 gam", "C. 44 gam", "D. 24 gam"],
            correct_index=2,
            explanation="Áp dụng định luật bảo toàn khối lượng: m(C) + m(O2) = m(CO2) => m(CO2) = 12 + 32 = 44 gam.",
            hint="Lấy khối lượng chất tham gia thứ nhất cộng khối lượng chất tham gia thứ hai."
        ),
        QuizQuestion(
            question_id="BT_MCQ_3",
            q_type="mcq",
            prompt="Dấu hiệu nào sau đây CHẮC CHẮN chứng tỏ có phản ứng hóa học xảy ra?",
            options=[
                "A. Nước đá tan chảy thành nước lỏng",
                "B. Hòa tan đường vào nước tạo thành dung dịch nước đường",
                "C. Xuất hiện chất mới có màu sắc khác, có kết tủa hoặc sinh bọt khí",
                "D. Xé nhỏ một tờ giấy trắng thành nhiều mảnh vụn"
            ],
            correct_index=2,
            explanation="Bản chất phản ứng hóa học là biến đổi chất này thành chất khác. Sự xuất hiện chất mới (kết tủa, khí bay lên, đổi màu) là dấu hiệu nhận biết.",
            hint="Phản ứng hóa học phải có sự tạo thành chất mới, khác với hiện tượng vật lý chỉ thay đổi trạng thái."
        ),
        QuizQuestion(
            question_id="BT_ESSAY_1",
            q_type="essay",
            prompt="Một thanh sắt để ngoài không khí ẩm lâu ngày bị gỉ sét. Khi đem cân thanh gỉ sắt, người ta thấy khối lượng của nó NẶNG HƠN thanh sắt ban đầu. Điều này có mâu thuẫn với định luật bảo toàn khối lượng không? Vì sao?",
            options=[],
            correct_index=0,
            explanation="Không hề mâu thuẫn vì thanh gỉ sắt là sản phẩm kết hợp giữa sắt (Fe) với khí Oxygen (O2) và hơi nước trong không khí. Tổng khối lượng sắt + khí O2 tham gia bằng khối lượng gỉ sắt.",
            hint="Sắt để ngoài không khí đã kết hợp với chất gì có trong không khí mà mắt thường không nhìn thấy?",
            key_points=["không mâu thuẫn", "oxygen", "không khí", "bảo toàn"],
            sample_answer="Hiện tượng này KHÔNG mâu thuẫn với định luật bảo toàn khối lượng. Vì khi sắt bị gỉ trong không khí ẩm, sắt đã phản ứng hóa học kết hợp với khí Oxygen và hơi nước trong không khí để tạo thành gỉ sắt (oxit sắt). Do đó, khối lượng gỉ sắt thu được bằng khối lượng thanh sắt ban đầu CỘNG VỚI khối lượng khí Oxygen và nước đã tham gia phản ứng."
        )
    ],

    # -------------------------------------------------------------------------
    # 5. QUÃNG ĐƯỜNG CHUYỂN ĐỘNG THẲNG ĐỀU (VẬT LÝ)
    # -------------------------------------------------------------------------
    "quang_duong_chuyen_dong": [
        QuizQuestion(
            question_id="QD_MCQ_1",
            q_type="mcq",
            prompt="Một đoàn tàu đang chuyển động thẳng đều với tốc độ không đổi v = 45 km/h. Quãng đường s đoàn tàu đi được trong thời gian t = 20 phút là:",
            options=["A. 15 km", "B. 900 km", "C. 22,5 km", "D. 30 km"],
            correct_index=0,
            explanation="Đổi 20 phút = 20/60 = 1/3 giờ. Quãng đường s = v * t = 45 * (1/3) = 15 km.",
            hint="Em nhớ đổi 20 phút sang đơn vị giờ trước khi nhân với tốc độ 45 km/h nhé!"
        ),
        QuizQuestion(
            question_id="QD_MCQ_2",
            q_type="mcq",
            prompt="Công thức nào sau đây dùng để tính quãng đường đi được s khi biết tốc độ v và thời gian chuyển động t?",
            options=["A. s = v * t", "B. s = v / t", "C. s = t / v", "D. s = v + t"],
            correct_index=0,
            explanation="Từ công thức v = s / t, ta suy ra quãng đường s bằng tích của tốc độ và thời gian: s = v * t.",
            hint="Quãng đường đi được bằng tốc độ nhân với thời gian."
        ),
        QuizQuestion(
            question_id="QD_MCQ_3",
            q_type="mcq",
            prompt="Một người đi bộ với tốc độ không đổi 4 km/h trong thời gian 45 phút. Quãng đường người đó đi được là:",
            options=["A. 3 km", "B. 2 km", "C. 4 km", "D. 180 km"],
            correct_index=0,
            explanation="Đổi 45 phút = 0,75 giờ. Quãng đường: s = 4 * 0,75 = 3 km.",
            hint="45 phút bằng 3/4 giờ (0,75 h)."
        ),
        QuizQuestion(
            question_id="QD_ESSAY_1",
            q_type="essay",
            prompt="Trên đường cao tốc, tại sao các biển báo giao thông luôn yêu cầu tài xế xe ô tô giữ khoảng cách an toàn tối thiểu 35 m khi chạy với tốc độ 60 km/h? Hãy giải thích dựa trên công thức s = v * t và thời gian phản xạ dừng xe.",
            options=[],
            correct_index=0,
            explanation="Khi chạy 60 km/h (khoảng 16,7 m/s), trong 1 giây tài xế phản xạ xe đã đi được gần 17 m. Cộng thêm quãng đường hãm phanh thì xe cần ít nhất 30-35 m để dừng hẳn mà không đâm va.",
            hint="Hãy tính xem trong 1 giây phản xạ của tài xế, xe đi được quãng đường bao nhiêu mét.",
            key_points=["quãng đường", "thời gian phản xạ", "khoảng cách an toàn", "hãm phanh"],
            sample_answer="Khi xe chạy với tốc độ 60 km/h (tương đương 16,7 m/s), chỉ trong khoảng 1 giây phản xạ của tài xế khi phát hiện chướng ngại vật thì xe đã đi thêm quãng đường s = v * t = 16,7 m. Sau đó xe tiếp tục trượt thêm một quãng đường phanh nữa mới dừng hẳn. Giữ khoảng cách tối thiểu 35 m đảm bảo xe dừng lại an toàn mà không va chạm với xe phía trước."
        )
    ],

    # -------------------------------------------------------------------------
    # 6. KHỐI LƯỢNG VÀ TRỌNG LƯỢNG (VẬT LÝ)
    # -------------------------------------------------------------------------
    "khoi_luong_trong_luong": [
        QuizQuestion(
            question_id="KL_MCQ_1",
            q_type="mcq",
            prompt="Ở gần bề mặt Trái Đất, mối liên hệ giữa trọng lượng P (đơn vị N) và khối lượng m (đơn vị kg) của một vật được xác định bởi công thức nào?",
            options=["A. P = 10 * m", "B. m = 10 * P", "C. P = m / 10", "D. P = m + 10"],
            correct_index=0,
            explanation="Gần mặt đất, lực hút Trái Đất tác dụng lên mỗi 1 kg khối lượng có độ lớn xấp xỉ 10 N, do đó P = 10m.",
            hint="Cứ mỗi 1 kg khối lượng thì có trọng lượng tương ứng khoảng 10 Newton."
        ),
        QuizQuestion(
            question_id="KL_MCQ_2",
            q_type="mcq",
            prompt="Một thùng hàng có khối lượng m = 45 kg đặt trên mặt sàn phòng học. Trọng lượng của thùng hàng đó là:",
            options=["A. 450 N", "B. 45 N", "C. 4,5 N", "D. 4500 N"],
            correct_index=0,
            explanation="Áp dụng công thức P = 10 * m = 10 * 45 = 450 N.",
            hint="Lấy khối lượng 45 kg nhân với 10."
        ),
        QuizQuestion(
            question_id="KL_MCQ_3",
            q_type="mcq",
            prompt="Đơn vị đo chuẩn trong hệ đo lường KHTN của khối lượng và trọng lượng lần lượt là gì?",
            options=[
                "A. Kilôgam (kg) và Newton (N)",
                "B. Newton (N) và Kilôgam (kg)",
                "C. Gam (g) và Jun (J)",
                "D. Mét (m) và Giây (s)"
            ],
            correct_index=0,
            explanation="Khối lượng đo bằng kilôgam (kg), còn trọng lượng là độ lớn lực hút của Trái Đất nên đo bằng Newton (N).",
            hint="Khối lượng là kg, trọng lượng là lực nên đo bằng N."
        ),
        QuizQuestion(
            question_id="KL_ESSAY_1",
            q_type="essay",
            prompt="Một phi hành gia khi đổ bộ lên Mặt Trăng thấy mình di chuyển rất nhẹ nhàng và có thể nhảy cao gấp 6 lần so với trên Trái Đất. Em hãy phân tích xem khối lượng (kg) và trọng lượng (N) của phi hành gia đã thay đổi như thế nào?",
            options=[],
            correct_index=0,
            explanation="Khối lượng là lượng chất cấu tạo nên cơ thể nên không đổi ở bất cứ đâu. Trọng lượng là lực hấp dẫn tác dụng lên người, do lực hút Mặt Trăng chỉ bằng 1/6 Trái Đất nên trọng lượng giảm 6 lần.",
            hint="Lượng chất bên trong cơ thể có bị mất đi không? Lực hút của Mặt Trăng so với Trái Đất thế nào?",
            key_points=["khối lượng không đổi", "trọng lượng giảm", "lực hút", "mặt trăng"],
            sample_answer="Khối lượng của phi hành gia KHÔNG ĐỔI vì khối lượng là lượng chất chứa trong cơ thể, không phụ thuộc vào vị trí trong vũ trụ. Trong khi đó, trọng lượng của phi hành gia GIẢM đi 6 lần vì lực hút hấp dẫn của Mặt Trăng chỉ bằng khoảng 1/6 lực hút của Trái Đất. Vì thế phi hành gia cảm thấy nhẹ nhàng và nhảy cao hơn."
        )
    ],

    # -------------------------------------------------------------------------
    # 7. LỰC MA SÁT VÀ CHUYỂN ĐỘNG KÉO BÀN (VẬT LÝ)
    # -------------------------------------------------------------------------
    "luc_ma_sat": [
        QuizQuestion(
            question_id="MS_MCQ_1",
            q_type="mcq",
            prompt="Lực nào sau đây xuất hiện tại bề mặt tiếp xúc giữa hai vật và có tác dụng cản trở chuyển động của vật?",
            options=["A. Trọng lực", "B. Lực ma sát", "C. Lực từ", "D. Lực đàn hồi"],
            correct_index=1,
            explanation="Lực ma sát là lực xuất hiện ở bề mặt tiếp xúc giữa hai vật, có chiều ngược chiều chuyển động hoặc xu hướng chuyển động và cản trở chuyển động của vật.",
            hint="Lực này sinh ra khi các bề mặt cọ xát vào nhau."
        ),
        QuizQuestion(
            question_id="MS_MCQ_2",
            q_type="mcq",
            prompt="Một học sinh dùng lực kéo một chiếc bàn trên sàn phòng học nhưng chiếc bàn vẫn đứng yên. Lực nào đã triệt tiêu lực kéo và giữ chiếc bàn nằm yên?",
            options=["A. Lực ma sát trượt", "B. Lực ma sát nghỉ", "C. Lực ma sát lăn", "D. Lực đẩy Archimedes"],
            correct_index=1,
            explanation="Khi có lực kéo tác dụng mà vật vẫn đứng yên, lực ma sát nghỉ xuất hiện ở mặt tiếp xúc cân bằng với lực kéo, giữ cho vật không chuyển động.",
            hint="Lực ma sát xuất hiện khi vật đang 'nghỉ' (đứng yên) gọi là gì?"
        ),
        QuizQuestion(
            question_id="MS_MCQ_3",
            q_type="mcq",
            prompt="Khi chiếc bàn đã bắt đầu chuyển động trượt đều trên sàn phòng học, để giảm lực ma sát giúp kéo bàn nhẹ nhàng hơn, biện pháp nào sau đây là hiệu quả nhất?",
            options=[
                "A. Đặt thêm nhiều chồng sách nặng lên bàn",
                "B. Làm cho mặt sàn nhám và gồ ghề hơn",
                "C. Lắp thêm các bánh xe lăn dưới chân bàn hoặc lau sàn nhẵn bóng",
                "D. Kéo bàn thật nhanh"
            ],
            correct_index=2,
            explanation="Thay ma sát trượt bằng ma sát lăn (dùng bánh xe) hoặc làm nhẵn bóng mặt tiếp xúc là biện pháp giảm lực ma sát cản trở chuyển động hiệu quả nhất.",
            hint="Bánh xe lăn hay bôi trơn bề mặt tiếp xúc sẽ giúp giảm lực cản ma sát."
        ),
        QuizQuestion(
            question_id="MS_ESSAY_1",
            q_type="essay",
            prompt="Một học sinh kéo một chiếc bàn trên sàn phòng học. Hãy giải thích tại sao khi mới bắt đầu kéo thì thấy rất nặng, nhưng khi bàn đã trượt đều thì kéo nhẹ hơn? Lực nào đã cản trở chuyển động của chiếc bàn?",
            options=[],
            correct_index=0,
            explanation="Lực cản trở chuyển động là lực ma sát. Ban đầu phải thắng lực ma sát nghỉ cực đại nên thấy rất nặng. Khi bàn đã trượt đều, lực cản là ma sát trượt có độ lớn nhỏ hơn ma sát nghỉ cực đại nên kéo nhẹ hơn.",
            hint="Hãy phân biệt giữa lực ma sát nghỉ cực đại lúc bắt đầu kéo và lực ma sát trượt khi bàn đã chuyển động.",
            key_points=["lực ma sát", "ma sát nghỉ cực đại", "ma sát trượt", "nhỏ hơn", "cản trở"],
            sample_answer="Lực cản trở chuyển động của chiếc bàn chính là lực ma sát giữa chân bàn và mặt sàn. Khi mới bắt đầu kéo, học sinh phải tác dụng lực đủ lớn để thắng lực ma sát nghỉ cực đại giữa các bề mặt tiếp xúc nên cảm thấy rất nặng. Khi chiếc bàn đã trượt đều, lực cản trở lúc này là lực ma sát trượt, và độ lớn của lực ma sát trượt thường nhỏ hơn lực ma sát nghỉ cực đại, vì vậy việc kéo bàn trở nên nhẹ nhàng hơn."
        )
    ],

    # -------------------------------------------------------------------------
    # 8. PHẢN ỨNG NUNG ĐÁ VÔI (HÓA HỌC)
    # -------------------------------------------------------------------------
    "nung_da_voi": [
        QuizQuestion(
            question_id="DV_MCQ_1",
            q_type="mcq",
            prompt="Khi nung đá vôi (thành phần chính là Calcium carbonate CaCO3) ở nhiệt độ cao, sản phẩm thu được gồm những chất nào?",
            options=[
                "A. Vôi sống (Calcium oxide CaO) và khí Carbon dioxide (CO2)",
                "B. Khí Oxygen (O2) và kim loại Calcium",
                "C. Nước vôi trong và khí Hydrogen",
                "D. Than chì và khí Carbonic"
            ],
            correct_index=0,
            explanation="Phương trình phân hủy đá vôi do nhiệt: CaCO3 -(t°)-> CaO + CO2 (khí).",
            hint="Sản phẩm gồm một chất rắn màu trắng (vôi sống) và một chất khí thoát ra."
        ),
        QuizQuestion(
            question_id="DV_MCQ_2",
            q_type="mcq",
            prompt="Nung 100 kg đá vôi (CaCO3), sau phản ứng thu được 56 kg vôi sống (CaO). Khối lượng khí CO2 thoát ra là bao nhiêu?",
            options=["A. 44 kg", "B. 156 kg", "C. 56 kg", "D. 28 kg"],
            correct_index=0,
            explanation="Theo định luật bảo toàn khối lượng: m(CaCO3) = m(CaO) + m(CO2) => m(CO2) = 100 - 56 = 44 kg.",
            hint="Lấy khối lượng đá vôi ban đầu trừ đi khối lượng vôi sống thu được."
        ),
        QuizQuestion(
            question_id="DV_MCQ_3",
            q_type="mcq",
            prompt="Quá trình nung đá vôi tạo thành vôi sống và khí carbon dioxide thuộc loại biến đổi nào sau đây?",
            options=[
                "A. Hiện tượng vật lý",
                "B. Phản ứng hóa học (phân hủy do nhiệt độ cao)",
                "C. Sự bay hơi của đá",
                "D. Sự hòa tan chất rắn"
            ],
            correct_index=1,
            explanation="Có chất mới sinh ra (CaO và CO2) khác biệt hoàn toàn với chất ban đầu (CaCO3) nên đây là phản ứng hóa học.",
            hint="Có chất mới sinh ra hay không?"
        ),
        QuizQuestion(
            question_id="DV_ESSAY_1",
            q_type="essay",
            prompt="Tại sao sau khi nung đá vôi trong lò thủ công hở miệng, người ta đem cân mẻ vôi sống thu được thì thấy khối lượng GIẢM so với khối lượng đá vôi ban đầu? Hiện tượng này có mâu thuẫn với định luật bảo toàn khối lượng không? Vì sao?",
            options=[],
            correct_index=0,
            explanation="Không mâu thuẫn vì khí CO2 sinh ra đã bay vào không khí qua miệng lò hở. Nếu cân cả lượng khí CO2 đã bay đi thì tổng khối lượng vẫn bằng đá vôi ban đầu.",
            hint="Lò nung hở miệng thì chất khí sinh ra sẽ đi đâu?",
            key_points=["không mâu thuẫn", "khí CO2", "bay vào không khí", "bảo toàn khối lượng"],
            sample_answer="Hiện tượng này KHÔNG mâu thuẫn với định luật bảo toàn khối lượng. Vì trong quá trình nung đá vôi (CaCO3 -> CaO + CO2), phản ứng sinh ra khí Carbon dioxide (CO2). Lò nung hở miệng khiến lượng khí CO2 này thoát ra ngoài không khí. Khối lượng vôi sống (CaO) còn lại trong lò giảm đi chính bằng đúng khối lượng khí CO2 đã bay mất."
        )
    ],

    # -------------------------------------------------------------------------
    # 9. DUNG DỊCH VÀ NỒNG ĐỘ PHẦN TRĂM C% (HÓA HỌC)
    # -------------------------------------------------------------------------
    "dung_dich_nong_do": [
        QuizQuestion(
            question_id="ND_MCQ_1",
            q_type="mcq",
            prompt="Công thức nào sau đây dùng để tính nồng độ phần trăm (C%) của một dung dịch?",
            options=[
                "A. C% = (m_ct / m_dd) * 100%",
                "B. C% = (m_dd / m_ct) * 100%",
                "C. C% = (m_ct / m_dm) * 100%",
                "D. C% = m_ct * m_dd * 100%"
            ],
            correct_index=0,
            explanation="Nồng độ phần trăm cho biết số gam chất tan có trong 100 gam dung dịch: C% = (m_ct / m_dd) * 100%.",
            hint="Lấy khối lượng chất tan chia cho tổng khối lượng dung dịch rồi nhân 100%."
        ),
        QuizQuestion(
            question_id="ND_MCQ_2",
            q_type="mcq",
            prompt="Hòa tan hoàn toàn 15 gam muối ăn (NaCl) vào 85 gam nước cất. Nồng độ phần trăm của dung dịch muối ăn thu được là:",
            options=["A. 15%", "B. 17,6%", "C. 85%", "D. 12%"],
            correct_index=0,
            explanation="Khối lượng dung dịch = 15 + 85 = 100 gam. Nồng độ: C% = (15 / 100) * 100% = 15%.",
            hint="Tính tổng khối lượng dung dịch trước: m_dd = m_ct + m_nước."
        ),
        QuizQuestion(
            question_id="ND_MCQ_3",
            q_type="mcq",
            prompt="Trong dung dịch nước muối ăn, chất tan và dung môi lần lượt là các chất nào?",
            options=[
                "A. Muối ăn là chất tan, nước cất là dung môi",
                "B. Nước cất là chất tan, muối ăn là dung môi",
                "C. Cả hai chất đều là dung môi",
                "D. Muối ăn là dung dịch"
            ],
            correct_index=0,
            explanation="Chất tan là chất bị hòa tan (muối ăn), còn dung môi là chất dùng để hòa tan chất khác (nước).",
            hint="Chất nào bị hòa tan, chất nào đóng vai trò chất lỏng hòa tan?"
        ),
        QuizQuestion(
            question_id="ND_ESSAY_1",
            q_type="essay",
            prompt="Nước muối sinh lý thường dùng trong y tế để súc họng và rửa vết thương có nồng độ 0,9%. Em hãy tính lượng muối ăn (NaCl) tinh khiết và lượng nước cất cần dùng để pha chế được 500 gam nước muối sinh lý 0,9%.",
            options=[],
            correct_index=0,
            explanation="Áp dụng công thức: m_ct = (C% * m_dd) / 100% = (0,9 * 500) / 100 = 4,5 gam muối. Lượng nước cất = 500 - 4,5 = 495,5 gam.",
            hint="Áp dụng công thức m_ct = (C% * m_dd) / 100% để tìm khối lượng muối ăn cần lấy.",
            key_points=["4,5 gam muối", "495,5 gam nước", "m_ct = (C% * m_dd)/100%"],
            sample_answer="Để pha 500 gam dung dịch nước muối sinh lý 0,9%, ta cần:\n- Khối lượng muối ăn tinh khiết: m_NaCl = (0,9 * 500) / 100 = 4,5 gam.\n- Khối lượng nước cất cần lấy: m_nước = 500 - 4,5 = 495,5 gam (tương đương 495,5 mL nước cất).\nCân 4,5 gam muối và hòa tan hoàn toàn vào 495,5 gam nước cất ta được dung dịch yêu cầu."
        )
    ],

    # -------------------------------------------------------------------------
    # 10. HIỆN TƯỢNG VẬT LÝ VÀ HIỆN TƯỢNG HÓA HỌC (HÓA HỌC)
    # -------------------------------------------------------------------------
    "hien_tuong_vat_ly_hoa_hoc": [
        QuizQuestion(
            question_id="PL_MCQ_1",
            q_type="mcq",
            prompt="Hiện tượng nào sau đây là hiện tượng hóa học?",
            options=[
                "A. Đun nóng đường mía bị cháy chuyển sang màu đen và có mùi khét",
                "B. Nước đá tan chảy thành nước lỏng",
                "C. Cồn để trong lọ hở bị bay hơi",
                "D. Cắt nhỏ một củ khoai tây"
            ],
            correct_index=0,
            explanation="Đường bị cháy tạo thành than carbon màu đen và hơi nước (chất mới có màu sắc và mùi khác hẳn) nên là hiện tượng hóa học.",
            hint="Hiện tượng nào có sự biến đổi tạo thành chất mới?"
        ),
        QuizQuestion(
            question_id="PL_MCQ_2",
            q_type="mcq",
            prompt="Dấu hiệu quan trọng nhất để phân biệt hiện tượng hóa học với hiện tượng vật lý là gì?",
            options=[
                "A. Có sự sinh ra chất mới",
                "B. Có sự thay đổi kích thước của vật",
                "C. Có sự chuyển thể từ rắn sang lỏng",
                "D. Có sự thay đổi vị trí của vật"
            ],
            correct_index=0,
            explanation="Bản chất của hiện tượng hóa học là có sự biến đổi từ chất này thành chất khác (xuất hiện chất mới).",
            hint="Dấu hiệu cốt lõi là tạo ra chất mới."
        ),
        QuizQuestion(
            question_id="PL_MCQ_3",
            q_type="mcq",
            prompt="Khi đun nóng nhẹ đường mía trong chảo, ban đầu đường nóng chảy từ thể rắn sang chất lỏng sệt màu vàng nâu. Giai đoạn này là hiện tượng gì?",
            options=[
                "A. Hiện tượng vật lý (sự chuyển thể nóng chảy)",
                "B. Hiện tượng hóa học",
                "C. Phản ứng phân hủy",
                "D. Sự quang hợp"
            ],
            correct_index=0,
            explanation="Đường mới chỉ nóng chảy chuyển từ thể rắn sang lỏng, chưa bị biến đổi thành chất khác nên là hiện tượng vật lý.",
            hint="Chỉ biến đổi trạng thái rắn sang lỏng, chưa có chất mới."
        ),
        QuizQuestion(
            question_id="PL_ESSAY_1",
            q_type="essay",
            prompt="Khi nấu nướng thức ăn bị cháy khét, ta thấy thức ăn biến màu đen và có mùi khét nồng nặc. Đó là hiện tượng vật lý hay hiện tượng hóa học? Hãy giải thích và nêu cách phòng tránh thức ăn bị cháy khét.",
            options=[],
            correct_index=0,
            explanation="Đó là hiện tượng hóa học vì nhiệt độ cao đã phân hủy các chất hữu cơ trong thức ăn thành than carbon (màu đen) và các khí có mùi khét (chất mới).",
            hint="Màu đen và mùi khét có phải là chất mới sinh ra do nhiệt độ cao phân hủy chất hữu cơ không?",
            key_points=["hiện tượng hóa học", "chất mới", "màu đen than carbon", "mùi khét", "nhiệt độ"],
            sample_answer="Đó là HIỆN TƯỢNG HÓA HỌC. Bởi vì dưới tác dụng của nhiệt độ quá cao, các chất hữu cơ trong thức ăn (đường, đạm, tinh bột) đã bị phân hủy tạo ra các chất mới: than carbon (màu đen) và các hợp chất khí bay lên gây mùi khét nồng. Để phòng tránh, khi nấu cần điều chỉnh ngọn lửa vừa phải, đảo đều tay và cho đủ lượng dầu/nước phù hợp."
        )
    ],

    # -------------------------------------------------------------------------
    # 11. HÔ HẤP TẾ BÀO (SINH HỌC)
    # -------------------------------------------------------------------------
    "ho_hap_te_bao": [
        QuizQuestion(
            question_id="HH_MCQ_1",
            q_type="mcq",
            prompt="Bào quan nào trong tế bào được ví là 'nhà máy năng lượng', nơi diễn ra chủ yếu quá trình hô hấp tế bào?",
            options=["A. Ti thể", "B. Lục lạp", "C. Nhân tế bào", "D. Không bào"],
            correct_index=0,
            explanation="Ti thể là bào quan thực hiện hô hấp tế bào, phân giải chất hữu cơ giải phóng năng lượng ATP cung cấp cho tế bào.",
            hint="Bào quan có màng kép với các mào gấp nếp bên trong tế bào."
        ),
        QuizQuestion(
            question_id="HH_MCQ_2",
            q_type="mcq",
            prompt="Sản phẩm của quá trình hô hấp tế bào bao gồm những yếu tố nào sau đây?",
            options=[
                "A. Khí Carbon dioxide (CO2), Nước (H2O) và Năng lượng (ATP)",
                "B. Khí Oxygen (O2) và Chất hữu cơ (Glucose)",
                "C. Khí Nitrogen và Muối khoáng",
                "D. Tinh bột và Vitamin"
            ],
            correct_index=0,
            explanation="Phương trình hô hấp tế bào: Glucose + O2 -> CO2 + H2O + Năng lượng (ATP + nhiệt).",
            hint="Hô hấp thải ra khí gì khi ta thở ra và sinh ra năng lượng gì cho cơ thể?"
        ),
        QuizQuestion(
            question_id="HH_MCQ_3",
            q_type="mcq",
            prompt="Khi em chạy nhanh hoặc chơi thể thao mạnh, nhịp thở và nhịp tim của em tăng lên nhanh chóng nhằm mục đích gì?",
            options=[
                "A. Cung cấp thêm khí Oxygen cho tế bào hô hấp tạo năng lượng vận động",
                "B. Làm cơ bắp được nghỉ ngơi",
                "C. Giảm lượng mồ hôi thoát ra",
                "D. Tích lũy thêm khí Carbon dioxide"
            ],
            correct_index=0,
            explanation="Cơ bắp hoạt động mạnh tiêu tốn nhiều ATP, cơ thể cần nạp nhiều O2 qua hô hấp và tuần hoàn máu nhanh để ti thể phân giải năng lượng đáp ứng nhu cầu.",
            hint="Vận động mạnh cần nhiều năng lượng nên cơ thể cần nạp thêm khí gì?"
        ),
        QuizQuestion(
            question_id="HH_ESSAY_1",
            q_type="essay",
            prompt="Tại sao người ta khuyên không nên để nhiều chậu hoa hoặc cây cảnh xanh tốt trong phòng ngủ đóng kín cửa vào ban đêm? Em hãy giải thích lý do dựa trên quá trình quang hợp và hô hấp của thực vật.",
            options=[],
            correct_index=0,
            explanation="Ban đêm không có ánh sáng nên cây ngừng quang hợp, chỉ thực hiện hô hấp: hấp thụ khí O2 và thải khí CO2. Phòng kín sẽ bị thiếu dưỡng khí O2, gây ngột ngạt cho con người khi ngủ.",
            hint="Vào ban đêm cây có quang hợp được không? Cây thực hiện quá trình gì thải ra khí gì?",
            key_points=["ban đêm", "ngừng quang hợp", "chỉ hô hấp", "hút O2 thải CO2", "phòng kín"],
            sample_answer="Vào ban đêm khi không có ánh sáng mặt trời, cây xanh NGỪNG quá trình quang hợp nhưng vẫn liên tục thực hiện quá trình HÔ HẤP TẾ BÀO. Khi đó, cây hấp thụ khí Oxygen (O2) và thải ra khí Carbon dioxide (CO2). Trong phòng ngủ đóng kín cửa, cây xanh sẽ tranh giành khí O2 với con người và làm tăng nồng độ khí CO2, khiến người ngủ dễ bị ngạt thở, mệt mỏi và nguy hiểm đến sức khỏe."
        )
    ],

    # -------------------------------------------------------------------------
    # 12. THOÁT HƠI NƯỚC QUA KHÍ KHỔNG (SINH HỌC)
    # -------------------------------------------------------------------------
    "thoat_hoi_nuoc": [
        QuizQuestion(
            question_id="TH_MCQ_1",
            q_type="mcq",
            prompt="Bộ phận nào trên bề mặt biểu bì lá cây đóng vai trò là cơ quan chủ yếu thoát hơi nước ra môi trường bên ngoài?",
            options=["A. Khí khổng", "B. Gân lá", "C. Cuống lá", "D. Lục lạp"],
            correct_index=0,
            explanation="Khí khổng nằm trên lớp biểu bì lá (chủ yếu ở mặt dưới) có khả năng đóng mở, thoát hơi nước chiếm phần lớn lượng nước thoát của cây.",
            hint="Cấu trúc có hai tế bào hình hạt đậu ghép lại với nhau."
        ),
        QuizQuestion(
            question_id="TH_MCQ_2",
            q_type="mcq",
            prompt="Thoát hơi nước qua lá có vai trò sinh học quan trọng nào đối với cây trồng?",
            options=[
                "A. Tạo lực hút kéo dòng nước và muối khoáng từ rễ lên lá, đồng thời hạ nhiệt độ bề mặt lá",
                "B. Giữ toàn bộ lượng nước trong thân cây không cho bay hơi",
                "C. Làm cho cây nặng hơn",
                "D. Giúp cây hấp thụ trực tiếp ánh sáng mặt trời"
            ],
            correct_index=0,
            explanation="Thoát hơi nước là động lực đầu trên của dòng mạch gỗ, hút nước và khoáng từ rễ lên, đồng thời làm mát bề mặt lá dưới trời nắng.",
            hint="Nước bay hơi qua lá giúp hút nước từ dưới rễ lên và làm mát lá cây."
        ),
        QuizQuestion(
            question_id="TH_MCQ_3",
            q_type="mcq",
            prompt="Vào những ngày trời trưa nắng gắt và khô hạn, khí khổng ở lá thường có xu hướng đóng bớt lại nhằm mục đích gì?",
            options=[
                "A. Hạn chế sự mất nước quá mức làm cây bị héo",
                "B. Tăng cường đón gió mát",
                "C. Tăng lượng khí CO2 vào lá",
                "D. Làm cho rễ mọc dài hơn"
            ],
            correct_index=0,
            explanation="Khi trời nắng gắt, khí khổng khép bớt để giảm thoát hơi nước, bảo vệ cây không bị mất nước kiệt quệ dẫn đến chết khô.",
            hint="Đóng lại để giữ gì cho cây không bị héo?"
        ),
        QuizQuestion(
            question_id="TH_ESSAY_1",
            q_type="essay",
            prompt="Tại sao khi bứng cây xanh đem trồng sang một vị trí mới, người làm vườn thường phải cắt tỉa bớt các cành lá sum suê? Hãy giải thích lợi ích sinh học của việc làm này.",
            options=[],
            correct_index=0,
            explanation="Khi bứng cây, rễ cây bị tổn thương chưa hút được đủ nước. Cắt bớt cành lá giúp giảm diện tích thoát hơi nước, tránh cho cây bị mất nước héo úa trước khi rễ mới kịp hồi phục.",
            hint="Bộ rễ khi bứng bị đứt có hút được nhiều nước không? Nếu lá vẫn nhiều thì cây sẽ mất nước ra sao?",
            key_points=["rễ bị tổn thương", "giảm thoát hơi nước", "tránh héo cây", "cân bằng nước"],
            sample_answer="Khi bứng cây sang chỗ trồng mới, bộ rễ của cây đã bị đứt và tổn thương nên khả năng hút nước bị suy giảm rất mạnh. Trong khi đó, nếu để lại nhiều cành lá thì diện tích thoát hơi nước qua khí khổng vẫn rất lớn, khiến cây nhanh chóng bị mất nước kiệt quệ và héo chết. Việc cắt tỉa bớt cành lá giúp giảm lượng nước thoát ra ngoài, cân bằng lượng nước trong cây cho đến khi bộ rễ mới phục hồi và hút được nước bình thường."
        )
    ],

    # -------------------------------------------------------------------------
    # 13. TÍNH HƯỚNG SÁNG VÀ CẢM ỨNG Ở THỰC VẬT (SINH HỌC)
    # -------------------------------------------------------------------------
    "cam_ung_thuc_vat": [
        QuizQuestion(
            question_id="CU_MCQ_1",
            q_type="mcq",
            prompt="Hiện tượng ngọn cây trồng cạnh bậu cửa sổ luôn sinh trưởng uốn cong về phía có ánh sáng chiếu vào được gọi là:",
            options=["A. Tính hướng sáng dương", "B. Tính hướng trọng lực", "C. Tính hướng nước", "D. Tính hướng tiếp xúc"],
            correct_index=0,
            explanation="Ngọn cây sinh trưởng hướng về phía nguồn kích thích ánh sáng gọi là tính hướng sáng dương.",
            hint="Ngọn cây uốn cong về phía có 'ánh sáng'."
        ),
        QuizQuestion(
            question_id="CU_MCQ_2",
            q_type="mcq",
            prompt="Ý nghĩa sinh học quan trọng nhất của tính hướng sáng ở thực vật là gì?",
            options=[
                "A. Giúp phiến lá tiếp nhận tối đa nguồn năng lượng ánh sáng cho quá trình quang hợp",
                "B. Giúp thân cây mọc dài nhanh hơn",
                "C. Giúp rễ cây bám chặt vào đất",
                "D. Giúp cây nở hoa nhanh hơn"
            ],
            correct_index=0,
            explanation="Lá cây hướng về phía có ánh sáng sẽ hấp thụ được nhiều photon ánh sáng nhất để quang hợp tổng hợp chất hữu cơ.",
            hint="Quá trình quang hợp cần năng lượng gì từ mặt trời?"
        ),
        QuizQuestion(
            question_id="CU_MCQ_3",
            q_type="mcq",
            prompt="Bộ phận nào sau đây của cây thể hiện tính hướng sáng âm (sinh trưởng uốn cong tránh xa nguồn sáng)?",
            options=["A. Rễ cây", "B. Ngọn thân", "C. Phiến lá", "D. Chồi nách"],
            correct_index=0,
            explanation="Rễ cây sinh trưởng tránh xa ánh sáng, đâm sâu xuống lòng đất ẩm tối để hút nước và dinh dưỡng.",
            hint="Bộ phận mọc dưới lòng đất tránh xa ánh sáng mặt trời."
        ),
        QuizQuestion(
            question_id="CU_ESSAY_1",
            q_type="essay",
            prompt="Em hãy đề xuất một thí nghiệm đơn giản tại nhà để chứng minh tính hướng sáng của ngọn cây bằng chậu hạt đậu xanh gieo trong hộp các-tông. Nêu cách bố trí thí nghiệm và hiện tượng quan sát được sau vài ngày.",
            options=[],
            correct_index=0,
            explanation="Gieo hạt đậu vào chậu nhỏ, đặt vào hộp các-tông kín chỉ khoét 1 lỗ tròn ở một bên sườn cho ánh sáng lọt vào. Sau 3-5 ngày, ngọn mầm đậu sẽ uốn cong vươn thẳng về phía lỗ thủng đó.",
            hint="Dùng một hộp kín chỉ có 1 khe sáng chiếu vào một phía và quan sát ngọn cây mầm.",
            key_points=["hộp các-tông", "khoét lỗ một bên", "chiếu sáng một phía", "ngọn uốn cong về lỗ thủng"],
            sample_answer="Cách bố trí thí nghiệm:\n1. Gieo vài hạt đậu xanh vào chậu đất nhỏ, tưới ẩm cho hạt nảy mầm.\n2. Đặt chậu vào trong một hộp các-tông kín, khoét một lỗ tròn đường kính khoảng 3 cm ở MỘT BÊN THÀNH HỘP để ánh sáng chỉ lọt vào từ một hướng cố định.\n3. Đặt hộp ở nơi thoáng đãng và tưới nước giữ ẩm hàng ngày.\nHiện tượng quan sát được:\nSau 3 - 5 ngày, các cây mầm đậu xanh đều sinh trưởng uốn cong thân vươn thẳng về phía lỗ tròn có ánh sáng chiếu vào. Điều này chứng minh ngọn cây có tính hướng sáng dương."
        )
    ]
}


class QuizService:
    """
    Dịch vụ quản lý ngân hàng câu hỏi kiểm tra, chấm bài trắc nghiệm & tự luận Socratic.
    Tích hợp tạo đề tự động thông minh bằng AI bám sát câu hỏi của học sinh và dữ liệu Internet SGK.
    """

    @classmethod
    def get_quiz_bank_keys(cls) -> List[str]:
        return list(QUIZ_BANK.keys())

    @classmethod
    def detect_topic_key(cls, topic_text: str) -> str:
        """
        Tự động phân tích từ khóa bài học hoặc đề bài để tìm bộ câu hỏi kiểm tra phù hợp nhất.
        Ưu tiên các từ khóa đặc thù trước để tránh nhầm lẫn (ví dụ: lực ma sát trước chuyển động).
        """
        t = topic_text.lower()

        # 1. Lực ma sát (Kiểm tra trước "chuyển động" để tránh nhầm với tốc độ)
        if any(w in t for w in ["ma sát", "kéo bàn", "lực cản", "chân bàn", "khối gỗ"]):
            return "luc_ma_sat"

        # 2. Khối lượng và Trọng lượng
        if any(w in t for w in ["trọng lượng", "p = 10m", "khối lượng m", "newton", "lực hút trái đất", "m = 45 kg"]):
            return "khoi_luong_trong_luong"

        # 3. Quãng đường chuyển động thẳng đều (Đoàn tàu)
        if any(w in t for w in ["đoàn tàu", "quãng đường s", "s = v * t", "s = v.t", "tính quãng đường"]):
            return "quang_duong_chuyen_dong"

        # 4. Phản xạ ánh sáng gương phẳng
        if any(w in t for w in ["phản xạ", "gương", "gương phẳng", "góc tới", "góc phản xạ", "ánh sáng", "quang học"]):
            return "anh_sang_guong_phang"

        # 5. Nung đá vôi
        if any(w in t for w in ["nung đá", "vôi sống", "đá vôi", "caco3", "caco₃", "cao"]):
            return "nung_da_voi"

        # 6. Dung dịch và Nồng độ phần trăm C%
        if any(w in t for w in ["nồng độ", "c%", "dung dịch", "muối ăn", "chất tan", "dung môi", "nacl"]):
            return "dung_dich_nong_do"

        # 7. Hiện tượng vật lý và Hiện tượng hóa học (Đun đường)
        if any(w in t for w in ["đun đường", "đường mía", "hiện tượng vật lý", "hiện tượng hóa học", "màu đen và có mùi khét"]):
            return "hien_tuong_vat_ly_hoa_hoc"

        # 8. Bảo toàn khối lượng (Đốt than)
        if any(w in t for w in ["bảo toàn", "than", "đốt than", "bột than", "carbon"]):
            return "bao_toan_khoi_luong"

        # 9. Cảm ứng và Tính hướng sáng
        if any(w in t for w in ["hướng sáng", "cảm ứng", "uốn cong", "bậu cửa"]):
            return "cam_ung_thuc_vat"

        # 10. Thoát hơi nước qua khí khổng
        if any(w in t for w in ["thoát hơi nước", "khí khổng"]):
            return "thoat_hoi_nuoc"

        # 11. Hô hấp tế bào
        if any(w in t for w in ["hô hấp", "nhịp tim", "nhịp thở", "ti thể", "năng lượng atp"]):
            return "ho_hap_te_bao"

        # 12. Quang hợp thực vật
        if any(w in t for w in ["quang hợp", "lục lạp", "lá cây", "diệp lục", "thực vật"]):
            return "quang_hop_thuc_vat"

        # 13. Tốc độ chuyển động (Xe đạp, v = s/t)
        if any(w in t for w in ["tốc độ", "vận tốc", "xe đạp", "km/h", "m/s", "v = s / t", "chuyển động"]):
            return "chuyen_dong_toc_do"

        return "chuyen_dong_toc_do"  # Mặc định

    @classmethod
    def shuffle_question_options(cls, question: QuizQuestion) -> QuizQuestion:
        """
        Xáo trộn ngẫu nhiên thứ tự các phương án A, B, C, D để đáp án đúng không bị cố định ở phương án A,
        tạo tính khách quan và trải nghiệm khảo sát/kiểm tra chân thực cho học sinh.
        """
        if question.q_type != "mcq" or not question.options or len(question.options) < 2:
            return question

        orig_correct_idx = question.correct_index if 0 <= question.correct_index < len(question.options) else 0

        def clean_opt(s: str) -> str:
            s = s.strip()
            if len(s) > 2 and s[0] in "ABCDabcd" and s[1] in ".:)":
                return s[2:].strip()
            return s

        clean_options = [clean_opt(opt) for opt in question.options]

        # Ghép cặp (vị trí ban đầu, nội dung phương án) rồi xáo trộn ngẫu nhiên
        import random
        indexed = list(enumerate(clean_options))
        random.shuffle(indexed)

        new_options = []
        new_correct_idx = 0
        for new_idx, (orig_i, text) in enumerate(indexed):
            letter = chr(65 + new_idx)
            new_options.append(f"{letter}. {text}")
            if orig_i == orig_correct_idx:
                new_correct_idx = new_idx

        return QuizQuestion(
            question_id=question.question_id,
            q_type=question.q_type,
            prompt=question.prompt,
            options=new_options,
            correct_index=new_correct_idx,
            explanation=question.explanation,
            hint=question.hint,
            key_points=list(question.key_points),
            sample_answer=question.sample_answer
        )

    @classmethod
    def generate_quiz_via_ai(
        cls,
        problem_text: str,
        topic: str = "",
        strand: str = "",
        quiz_type: str = "pre_test"
    ) -> Optional[List[QuizQuestion]]:
        """
        Dùng AI Socrates tổng hợp bộ câu hỏi kiểm tra đánh giá (Pre-test hoặc Post-test)
        bám sát ĐÚNG TRỌNG TÂM KHOA HỌC của bài toán học sinh cung cấp,
        tham khảo ngân hàng đề thi THCS và học liệu SGK KHTN 7 chuẩn từ Internet.
        """
        try:
            from app_tich_hop_socrates.ai_service import call_ai_chat_completion, get_ai_config
            from chuc_nang_7_demo_offline_cache.offline_engine import GLOBAL_OFFLINE_ENGINE

            cfg = get_ai_config()
            if GLOBAL_OFFLINE_ENGINE.is_offline() or not cfg["has_key"]:
                return None

            clean_problem = problem_text.strip()
            if not clean_problem:
                clean_problem = topic

            is_pre = (quiz_type == "pre_test")

            system_prompt = (
                "Bạn là Chuyên gia Khảo thí và Giáo viên KHTN 7 (Khoa học Tự nhiên THCS chuẩn Bộ GD&ĐT Việt Nam). "
                "Nhiệm vụ của bạn là biên soạn bộ câu hỏi kiểm tra đánh giá năng lực học sinh "
                "bám sát ĐÚNG NỘI DUNG VÀ BẢN CHẤT KHOA HỌC của bài toán được cung cấp, "
                "tham khảo các dạng câu hỏi trắc nghiệm/tự luận phổ biến nhất trên Internet (đề thi THCS, Violet, VnDoc, SGK KHTN 7 Chân trời sáng tạo, Cánh Diều, Kết nối tri thức).\n\n"
                "NGUYÊN TẮC SƯ PHẠM QUAN TRỌNG:\n"
                "1. TUYỆT ĐỐI KHÔNG ra đề lệch chủ đề. Phải tập trung vào đúng hiện tượng và kiến thức cốt lõi của bài toán "
                "(Ví dụ: nếu bài toán nói về Lực ma sát khi kéo bàn thì câu hỏi PHẢI về ma sát trượt, ma sát nghỉ, tác dụng cản trở, tăng giảm ma sát; "
                "TUYỆT ĐỐI KHÔNG hỏi về tính vận tốc hay công thức v = s/t).\n"
                "2. Câu hỏi phải rõ ràng, ngắn gọn, phù hợp trình độ học sinh THCS (Lớp 7).\n"
                "3. Mỗi câu trắc nghiệm (mcq) phải có 4 lựa chọn (A, B, C, D), 1 đáp án đúng duy nhất. "
                "VỊ TRÍ ĐÁP ÁN ĐÚNG PHẢI PHÂN BỐ NGẪU NHIÊN giữa A (0), B (1), C (2), D (3). "
                "TUYỆT ĐỐI KHÔNG để tất cả câu hỏi đều có đáp án đúng là A (0).\n"
                "4. Định dạng đầu ra: JSON hợp lệ duy nhất có cấu trúc:\n"
                "{\n"
                '  "questions": [\n'
                '    {\n'
                '      "question_id": "AI_MCQ_1",\n'
                '      "q_type": "mcq",\n'
                '      "prompt": "Nội dung câu hỏi trắc nghiệm...",\n'
                '      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],\n'
                '      "correct_index": 2,\n'
                '      "explanation": "Giải thích chi tiết vì sao đáp án này đúng...",\n'
                '      "hint": "Gợi ý tư duy Socratic ngắn gọn..."\n'
                '    }\n'
                '  ]\n'
                "}"
            )

            if is_pre:
                req_desc = (
                    "Yêu cầu: Tạo đúng 3 CÂU TRẮC NGHIỆM (mcq) cho bài KHẢO SÁT ĐẦU VÀO (Pre-test 2 phút). "
                    "Mục tiêu là khảo sát nhận thức ban đầu về hiện tượng trong bài toán."
                )
            else:
                req_desc = (
                    "Yêu cầu: Tạo đúng 3 CÂU TRẮC NGHIỆM (mcq) + 1 CÂU TỰ LUẬN VẬN DỤNG THỰC TẾ (essay) "
                    "cho bài KIỂM TRA ĐẦU RA (Post-test). "
                    "Câu tự luận cần có các trường: 'prompt', 'explanation', 'hint', 'key_points' (danh sách từ khóa), 'sample_answer' (đáp án mẫu SGK)."
                )

            user_prompt = (
                f"Chủ đề bài học: {topic}\n"
                f"Mạch kiến thức: {strand}\n"
                f"Đề bài/Câu hỏi cụ thể của học sinh:\n\"{clean_problem}\"\n\n"
                f"{req_desc}\n"
                "Hãy tổng hợp và tạo bộ câu hỏi chất lượng cao nhất!"
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            ok, content, data, err = call_ai_chat_completion(messages, json_mode=True, timeout=22.0)
            if not ok or not data:
                return None

            raw_list = data.get("questions", [])
            if not isinstance(raw_list, list) or len(raw_list) == 0:
                return None

            questions: List[QuizQuestion] = []
            for i, item in enumerate(raw_list, 1):
                q_type = str(item.get("q_type", "mcq")).lower()
                q_id = str(item.get("question_id", f"AI_{q_type.upper()}_{i}"))
                prompt = str(item.get("prompt", "")).strip()
                if not prompt:
                    continue

                if q_type == "mcq":
                    options = [str(opt) for opt in item.get("options", [])]
                    if len(options) < 2:
                        continue
                    correct_idx = int(item.get("correct_index", 0))
                    if correct_idx < 0 or correct_idx >= len(options):
                        correct_idx = 0
                    explanation = str(item.get("explanation", ""))
                    hint = str(item.get("hint", ""))
                    raw_mcq = QuizQuestion(
                        question_id=q_id,
                        q_type="mcq",
                        prompt=prompt,
                        options=options,
                        correct_index=correct_idx,
                        explanation=explanation,
                        hint=hint
                    )
                    # Xáo trộn ngẫu nhiên thứ tự phương án A, B, C, D
                    questions.append(cls.shuffle_question_options(raw_mcq))
                elif q_type == "essay" and not is_pre:
                    key_points = [str(k) for k in item.get("key_points", [])]
                    sample_answer = str(item.get("sample_answer", ""))
                    explanation = str(item.get("explanation", ""))
                    hint = str(item.get("hint", ""))
                    questions.append(QuizQuestion(
                        question_id=q_id,
                        q_type="essay",
                        prompt=prompt,
                        options=[],
                        correct_index=0,
                        explanation=explanation,
                        hint=hint,
                        key_points=key_points,
                        sample_answer=sample_answer
                    ))

            if len(questions) >= (3 if is_pre else 3):
                return questions
            return None
        except Exception as e:
            print(f"[QuizService] Lỗi tạo đề thi AI: {e}")
            return None

    @classmethod
    def get_quiz_for_problem(
        cls,
        problem_text: str = "",
        topic: str = "",
        strand: str = "",
        quiz_type: str = "post_lesson",
        use_ai: bool = False
    ) -> List[QuizQuestion]:
        """
        Lấy bộ câu hỏi kiểm tra cho bài toán:
        - Nếu use_ai=True: Thử gọi AI tạo đề theo bài toán & học liệu trực tuyến.
        - Fallback: Lấy từ ngân hàng offline chuẩn xác theo từ khóa bài toán.
        """
        if use_ai and (problem_text or topic):
            ai_questions = cls.generate_quiz_via_ai(problem_text=problem_text, topic=topic, strand=strand, quiz_type=quiz_type)
            if ai_questions:
                return ai_questions

        # Fallback offline
        search_key = f"{problem_text} {topic}".strip()
        return cls.get_quiz_for_topic(search_key, quiz_type=quiz_type)

    @classmethod
    def get_quiz_for_topic(cls, topic_text: str, quiz_type: str = "post_lesson") -> List[QuizQuestion]:
        """
        Lấy danh sách câu hỏi theo bài học và loại bài kiểm tra:
        - pre_test: 3 câu trắc nghiệm nhận diện nhanh trình độ đầu vào (2 phút).
        - post_lesson / post_test / daily_review: Đầy đủ 4 câu (3 trắc nghiệm + 1 tự luận vận dụng thực tế).
        Tất cả các câu trắc nghiệm đều được xáo trộn ngẫu nhiên phương án A, B, C, D.
        """
        key = cls.detect_topic_key(topic_text)
        all_q = QUIZ_BANK.get(key, QUIZ_BANK["chuyen_dong_toc_do"])
        if quiz_type == "pre_test":
            # Chỉ lấy các câu trắc nghiệm cho bài khảo sát ban đầu
            return [cls.shuffle_question_options(q) for q in all_q if q.q_type == "mcq"]
        return [cls.shuffle_question_options(q) for q in all_q]

    @classmethod
    def grade_pre_test(
        cls,
        questions: List[QuizQuestion],
        mcq_answers: Dict[str, int]
    ) -> Tuple[float, int, List[Dict[str, Any]]]:
        """
        Chấm bài khảo sát trình độ đầu vào (Pre-test):
        - Thang điểm 10.0 (chia đều cho các câu trắc nghiệm).
        - Đánh giá năng lực nền tảng trước bài học.
        """
        correct_count = 0
        details = []
        mcq_questions = [q for q in questions if q.q_type == "mcq"]
        total_q = len(mcq_questions) or 3

        for q in mcq_questions:
            chosen = mcq_answers.get(q.question_id, -1)
            is_correct = (chosen == q.correct_index)
            if is_correct:
                correct_count += 1
            details.append({
                "question_id": q.question_id,
                "prompt": q.prompt,
                "q_type": "mcq",
                "options": q.options,
                "chosen_index": chosen,
                "correct_index": q.correct_index,
                "is_correct": is_correct,
                "explanation": q.explanation
            })

        score = round((correct_count / total_q) * 10.0, 1)
        return score, correct_count, details

    @classmethod
    def compare_pre_post(cls, pre_score: float, post_score: float) -> Dict[str, Any]:
        """
        Tính toán chỉ số tiến bộ sư phạm (Learning Gain) đối chứng trước & sau bài học:
        - Delta điểm số = Post - Pre
        - Tỷ lệ chuẩn hóa Hake Normalized Gain
        - Nhận xét sư phạm truyền cảm hứng
        """
        diff = round(post_score - pre_score, 1)
        if pre_score < 10.0:
            hake_gain = round(((post_score - pre_score) / (10.0 - pre_score)) * 100, 1)
        else:
            hake_gain = 100.0

        if diff >= 3.0:
            badge = "Tiến Bộ Vượt Bậc 🚀"
            comment = f"Tuyệt vời! Em đã bứt phá ngoạn mục +{diff} điểm sau khi học cùng Socrates Nhí. Tư duy khoa học phát triển rõ rệt!"
            color = "#15803D"
        elif diff > 0:
            badge = "Có Tiến Bộ Tốt 🌟"
            comment = f"Rất tốt! Em đã nâng cao thêm +{diff} điểm so với ban đầu. Em đã nắm vững các khái niệm cốt lõi."
            color = "#047857"
        elif diff == 0:
            badge = "Giữ Vững Phong Độ 💡"
            comment = "Em duy trì tốt phong độ làm chủ kiến thức vững chắc từ trước đến sau bài học."
            color = "#1D4ED8"
        else:
            badge = "Cần Củng Cố Lại 🌿"
            comment = "Hãy đọc lại sơ đồ tư duy và trao đổi thêm với Socrates ở các phần chưa chắc chắn nhé."
            color = "#B45309"

        return {
            "pre_score": pre_score,
            "post_score": post_score,
            "diff": diff,
            "diff_str": f"+{diff}đ" if diff > 0 else f"{diff}đ",
            "hake_gain": max(0.0, hake_gain),
            "badge": badge,
            "comment": comment,
            "color": color
        }

    @classmethod
    def evaluate_essay_answer(
        cls,
        student_text: str,
        question: QuizQuestion
    ) -> Tuple[float, str]:
        """
        Chấm điểm câu tự luận theo thang điểm 4.0.
        Có hỗ trợ AI nếu có mạng hoặc bộ phân tích từ khóa sư phạm chuẩn xác khi Offline.
        """
        text = student_text.strip()
        if not text:
            return 0.0, "Em chưa viết câu trả lời. Hãy đọc lại gợi ý của Socrates và tự tin diễn đạt suy nghĩ nhé!"

        # 1. Thử gọi AI trực tuyến nếu có cấu hình OpenAI
        try:
            from app_tich_hop_socrates.ai_service import get_ai_config
            from chuc_nang_7_demo_offline_cache.offline_engine import GLOBAL_OFFLINE_ENGINE

            cfg = get_ai_config()
            is_online = (not GLOBAL_OFFLINE_ENGINE.is_offline()) and cfg["has_key"]

            if is_online:
                import urllib.request
                api_key = cfg["api_key"]
                base_url = cfg["base_url"].rstrip("/")
                model = cfg["model"]

                system_prompt = (
                    "Bạn là Gia sư Socrates Nhí chấm câu trả lời tự luận KHTN 7 của học sinh. "
                    "Hãy chấm điểm theo thang 4.0 và viết lời nhận xét ngắn gọn (tối đa 3 câu), ân cần, chỉ rõ điểm sáng và góp ý hoàn thiện. "
                    "Định dạng trả về JSON duy nhất: {\"score\": float, \"feedback\": string}."
                )
                user_prompt = (
                    f"Câu hỏi: {question.prompt}\n"
                    f"Đáp án chuẩn: {question.sample_answer}\n"
                    f"Từ khóa cốt lõi: {', '.join(question.key_points)}\n"
                    f"Câu trả lời của học sinh: {text}\n"
                )

                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3
                }

                req = urllib.request.Request(
                    f"{base_url}/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    }
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    content_str = res_data["choices"][0]["message"]["content"]
                    # Trích xuất JSON từ phản hồi
                    match = re.search(r"\{.*\}", content_str, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        ai_score = min(4.0, max(0.5, float(parsed.get("score", 3.0))))
                        ai_feedback = str(parsed.get("feedback", "Câu trả lời của em thể hiện tư duy tốt!"))
                        return round(ai_score, 1), ai_feedback
        except Exception:
            pass  # Fallback sang chấm Offline rule-based

        # 2. Bộ chấm điểm Socratic Offline chuẩn xác (Rule-based)
        score = 1.0  # Điểm khởi đầu cho việc cố gắng trả lời
        matched_keys = []
        lower_text = text.lower()

        for kp in question.key_points:
            if kp.lower() in lower_text:
                matched_keys.append(kp)

        # Chấm điểm dựa trên từ khóa cốt lõi
        match_ratio = len(matched_keys) / max(1, len(question.key_points))
        score += match_ratio * 2.5

        # Thưởng độ dài và tính mạch lạc
        word_count = len(text.split())
        if word_count >= 20:
            score += 0.5
        elif word_count >= 10:
            score += 0.3

        score = min(4.0, round(score, 1))

        # Soạn nhận xét sư phạm gợi mở
        if score >= 3.5:
            feedback = f"🌟 Xuất sắc! Em đã nắm rất chắc bản chất hiện tượng và lập luận rất thuyết phục (nhắc được các ý: {', '.join(matched_keys)})."
        elif score >= 2.5:
            feedback = f"👍 Khá tốt! Em đã chỉ ra được trọng tâm vấn đề. Em có thể tham khảo thêm đáp án mẫu để hoàn thiện câu cú mạch lạc hơn nữa nhé!"
        else:
            feedback = "💡 Em đã có nỗ lực tư duy! Hãy đọc kỹ phần giải thích chi tiết và đáp án mẫu của Socrates để bổ sung các ý khoa học còn thiếu nhé."

        return score, feedback

    @classmethod
    def grade_full_quiz(
        cls,
        questions: List[QuizQuestion],
        mcq_answers: Dict[str, int],  # q_id -> chosen index
        student_essay: str
    ) -> Tuple[float, int, float, str, List[Dict[str, Any]]]:
        """
        Chấm toàn diện bài kiểm tra:
        - 3 câu trắc nghiệm: Mỗi câu 2.0 điểm (Tổng 6.0đ).
        - 1 câu tự luận: Thang điểm 4.0 điểm.
        - Tổng điểm: Thang điểm 10.0.
        """
        correct_mcq = 0
        details = []

        for q in questions:
            if q.q_type == "mcq":
                chosen = mcq_answers.get(q.question_id, -1)
                is_correct = (chosen == q.correct_index)
                if is_correct:
                    correct_mcq += 1

                details.append({
                    "question_id": q.question_id,
                    "prompt": q.prompt,
                    "q_type": "mcq",
                    "options": q.options,
                    "chosen_index": chosen,
                    "correct_index": q.correct_index,
                    "is_correct": is_correct,
                    "explanation": q.explanation
                })
            else:
                # Câu tự luận
                essay_score, essay_feedback = cls.evaluate_essay_answer(student_essay, q)
                details.append({
                    "question_id": q.question_id,
                    "prompt": q.prompt,
                    "q_type": "essay",
                    "student_answer": student_essay,
                    "score": essay_score,
                    "max_score": 4.0,
                    "feedback": essay_feedback,
                    "sample_answer": q.sample_answer,
                    "explanation": q.explanation
                })

        mcq_score = correct_mcq * 2.0  # 3 câu * 2đ = 6.0đ
        total_score = round(mcq_score + essay_score, 1)
        total_score = min(10.0, max(0.0, total_score))

        return total_score, correct_mcq, essay_score, essay_feedback, details

    @classmethod
    def load_quiz_history(cls) -> List[QuizRecord]:
        """Tải toàn bộ lịch sử các bài kiểm tra đã lưu."""
        if not QUIZ_HISTORY_FILE.exists():
            return []
        try:
            with open(QUIZ_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [QuizRecord.from_dict(item) for item in data]
        except Exception:
            return []

    @classmethod
    def save_quiz_record(cls, record: QuizRecord) -> bool:
        """Lưu một bài kiểm tra mới vào lịch sử."""
        try:
            history = cls.load_quiz_history()
            history.insert(0, record)  # Thêm vào đầu danh sách
            # Giới hạn tối đa 50 bài gần nhất
            history = history[:50]

            AUTH_DIR.mkdir(parents=True, exist_ok=True)
            with open(QUIZ_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([r.to_dict() for r in history], f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    @classmethod
    def get_student_records(cls, username: str) -> List[QuizRecord]:
        """Lấy danh sách các bài kiểm tra của một học sinh cụ thể."""
        all_records = cls.load_quiz_history()
        return [r for r in all_records if r.username == username]

    @classmethod
    def get_student_quiz_stats(cls, username: str) -> Dict[str, Any]:
        """Thống kê tổng hợp điểm kiểm tra của học sinh cho Cổng Phụ Huynh."""
        records = cls.get_student_records(username)
        if not records:
            return {
                "total_quizzes": 0,
                "average_score": 0.0,
                "last_score": None,
                "last_topic": None,
                "last_date": None,
                "mastery_level": "Chưa làm bài kiểm tra nào",
                "excellent_count": 0,
                "recent_records": []
            }

        scores = [r.score for r in records]
        avg_score = round(sum(scores) / len(scores), 1)
        excellent_count = sum(1 for s in scores if s >= 8.0)

        if avg_score >= 8.5:
            mastery = "Nắm rất vững bản chất KHTN ⭐"
        elif avg_score >= 7.0:
            mastery = "Nắm vững kiến thức trọng tâm 🌟"
        elif avg_score >= 5.0:
            mastery = "Đang rèn luyện tiến bộ 💡"
        else:
            mastery = "Cần tăng cường ôn tập thêm ⚠️"

        return {
            "total_quizzes": len(records),
            "average_score": avg_score,
            "last_score": records[0].score,
            "last_topic": records[0].topic,
            "last_date": records[0].created_at,
            "mastery_level": mastery,
            "excellent_count": excellent_count,
            "recent_records": [r.to_dict() for r in records[:5]]
        }

    @classmethod
    def get_pending_daily_review(cls, username: str) -> Optional[Dict[str, Any]]:
        """
        Kiểm tra tính năng Ôn tập ngắt quãng ngày hôm sau (Spaced Repetition).
        Nếu học sinh có bài học từ ngày hôm qua trở về trước mà hôm nay chưa ôn tập,
        hệ thống sẽ gợi ý bài ôn tập của ngày hôm nay.
        """
        today_str = date.today().isoformat()
        records = cls.get_student_records(username)

        # Kiểm tra xem hôm nay học sinh đã làm bài ôn tập ngày mới chưa
        today_reviews = [r for r in records if r.created_at.startswith(today_str) and r.quiz_type == "daily_review"]
        if today_reviews:
            return None  # Hôm nay đã làm rồi

        # Tìm bài học gần nhất từ ngày hôm qua trở về trước
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()
        for r in records:
            if not r.created_at.startswith(today_str):
                return {
                    "topic": r.topic,
                    "strand": r.strand,
                    "previous_score": r.score,
                    "date": r.created_at.split("T")[0]
                }

        # Nếu chưa có bài cũ, lấy bài mẫu mặc định để khởi động
        return {
            "topic": "Tốc độ của người đi xe đạp",
            "strand": "Vật lý",
            "previous_score": None,
            "date": "Hôm qua"
        }
