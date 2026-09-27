"""
Module: offline_bank.py
Chức năng 7: Ngân hàng Học liệu Cache 12 Bài Mẫu KHTN 7 Đủ 5 Pha Socratic (FR-10)
Đặc tả dự án: Socrates Nhí v3.0 (Mục 13 & Mục 18 - Vận hành lúc thi)

Kiến trúc 12 Bài mẫu chuẩn KHTN 7:
- MẠCH 1: VẬT LÝ THCS (4 bài: Tốc độ xe đạp, Quãng đường đoàn tàu, Trọng lượng & Khối lượng, Lực ma sát).
- MẠCH 2: HÓA HỌC THCS (4 bài: Đốt than bảo toàn khối lượng, Nung đá vôi, Nồng độ phần trăm, Hiện tượng vật lý/hóa học).
- MẠCH 3: SINH HỌC THCS (4 bài: Quang hợp ở lá cây, Hô hấp tế bào, Thoát hơi nước qua khí khổng, Cảm ứng hướng sáng).
"""

from typing import Dict, List, Optional
from .offline_model import OfflineSampleProblem, SocraticPhaseDialogue, KnowledgeStrand


OFFLINE_SAMPLE_PROBLEMS: Dict[str, OfflineSampleProblem] = {
    # =========================================================================
    # MẠCH 1: VẬT LÝ THCS (CƠ HỌC & NĂNG LƯỢNG) - 4 BÀI
    # =========================================================================
    "VL01": OfflineSampleProblem(
        problem_id="VL01",
        title="Tốc độ của người đi xe đạp",
        strand=KnowledgeStrand.PHYSICS,
        problem_text=(
            "Một người đi xe đạp chuyển động đều trên quãng đường thẳng s = 12 km trong thời gian t = 30 phút. "
            "Hãy xác định tốc độ v của người đó theo đơn vị km/h và m/s."
        ),
        given_facts=["Quãng đường s = 12 km", "Thời gian t = 30 phút"],
        core_concepts=["Tốc độ chuyển động", "Đổi đơn vị tốc độ (km/h ↔ m/s)"],
        target_variable="Tốc độ v (km/h và m/s)",
        common_pitfall="Lấy quãng đường nhân thời gian hoặc quên đổi phút sang giờ (30 phút = 0.5 h).",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Chúng mình cùng bắt đầu khám phá bài toán chuyển động nhé.",
                question="Đề bài cho biết quãng đường và thời gian là bao nhiêu? Đơn vị của chúng đã đồng nhất để tính ra km/h chưa?",
                micro_hint="Đề bài cho s = 12 km và t = 30 phút. Em hãy chú ý đơn vị phút nhé.",
                quick_replies=["s = 12 km, t = 30 phút", "Cần đổi 30 phút ra giờ", "Thời gian là phút, cần đổi ra giờ"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Rất tốt! Em đã phát hiện ra dữ kiện và sự chưa đồng nhất đơn vị thời gian.",
                question="Để tính tốc độ khi biết quãng đường s và thời gian t, em sử dụng công thức nào đã học?",
                micro_hint="Công thức liên hệ tốc độ, quãng đường và thời gian: v = s / t.",
                quick_replies=["v = s / t", "v = s chia t", "Tốc độ bằng quãng đường chia thời gian"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Chính xác! Công thức v = s / t hoàn toàn đúng.",
                question="Trước khi thay số vào tính, em hãy đổi 30 phút sang đơn vị giờ (h) bằng cách nào?",
                micro_hint="1 giờ có 60 phút. Muốn đổi từ phút sang giờ, ta lấy số phút chia cho 60.",
                quick_replies=["30 phút = 30/60 = 0.5 giờ", "30 phút = 1/2 giờ", "Chia cho 60 ra 0.5 h"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Lập luận rất chuẩn xác! Bước đổi đơn vị thời gian sang giờ rất quan trọng.",
                question="Sau khi tính ra tốc độ theo km/h, để đổi sang đơn vị m/s, em chia cho con số nào?",
                micro_hint="Quy tắc chuẩn KHTN 7: đổi từ km/h sang m/s ta chia cho 3.6.",
                quick_replies=["Chia cho 3.6", "1 m/s = 3.6 km/h nên ta lấy kết quả chia 3.6", "Chia cho 3.6 để ra m/s"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Tuyệt vời! Em đã làm chủ trọn vẹn phương pháp giải bài toán tính tốc độ!",
                question="Em hãy tóm tắt lại: Khi tính tốc độ chuyển động, cần đặc biệt lưu ý bước kiểm tra nào trước khi thay số?",
                micro_hint="Luôn đồng nhất đơn vị đo (km tương ứng với giờ, mét tương ứng với giây).",
                quick_replies=["Luôn đổi đơn vị thời gian về cùng hệ đo", "Đồng nhất km đi với h, m đi với s", "Kiểm tra đơn vị trước khi tính"]
            )
        }
    ),

    "VL02": OfflineSampleProblem(
        problem_id="VL02",
        title="Quãng đường đoàn tàu chuyển động",
        strand=KnowledgeStrand.PHYSICS,
        problem_text=(
            "Một đoàn tàu đang chuyển động thẳng đều với tốc độ không đổi v = 45 km/h. "
            "Tính quãng đường s mà đoàn tàu đi được trong khoảng thời gian t = 20 phút."
        ),
        given_facts=["Tốc độ v = 45 km/h", "Thời gian t = 20 phút"],
        core_concepts=["Tốc độ chuyển động", "Công thức quãng đường s = v * t"],
        target_variable="Quãng đường s (km)",
        common_pitfall="Nhân trực tiếp 45 với 20 mà không đổi 20 phút ra giờ.",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Đoàn tàu đang chạy với tốc độ ổn định nè.",
                question="Đề bài cho biết những đại lượng nào và yêu cầu chúng mình tìm đại lượng gì?",
                micro_hint="Tìm xem v và t bằng bao nhiêu, và câu hỏi yêu cầu tính s hay v nhé.",
                quick_replies=["Cho v = 45 km/h, t = 20 phút, tìm s", "Tìm quãng đường s", "Cho tốc độ và thời gian"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Đúng rồi! Chúng mình cần tìm quãng đường s.",
                question="Từ công thức gốc v = s / t, em hãy suy ra công thức để tính quãng đường s?",
                micro_hint="Muốn tìm số bị chia (quãng đường), ta lấy thương nhân với số chia: s = v * t.",
                quick_replies=["s = v * t", "s = v nhân t", "Quãng đường bằng tốc độ nhân thời gian"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Xuất sắc! Công thức s = v * t rất chính xác.",
                question="Tốc độ đang tính theo km/h, vậy thời gian 20 phút cần chuyển đổi ra đơn vị nào trước khi nhân?",
                micro_hint="Cần đổi 20 phút ra giờ bằng cách lấy 20 chia cho 60 (ra phân số 1/3 giờ).",
                quick_replies=["Đổi 20 phút ra giờ: 20/60 = 1/3 h", "Đổi ra giờ bằng cách chia 60", "20 phút = 1/3 giờ"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Lập luận rất sắc bén! Phép đổi đơn vị 20 phút = 1/3 giờ rất chuẩn.",
                question="Khi lấy v (km/h) nhân với t (h), đơn vị của kết quả quãng đường s thu được sẽ là gì?",
                micro_hint="km/h nhân h thì đơn vị giờ triệt tiêu, còn lại kilômét (km).",
                quick_replies=["Đơn vị là km (kilômét)", "Đơn vị là km", "Quãng đường có đơn vị là kilômét"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Chúc mừng em! Em đã tự mình giải quyết bài toán biến đổi công thức rất khéo léo.",
                question="Theo em, tam giác công thức giữa s, v, t giúp em ghi nhớ các phép biến đổi như thế nào?",
                micro_hint="s ở đỉnh tam giác, v và t ở hai góc đáy: s = v*t; v = s/t; t = s/v.",
                quick_replies=["s = v*t, v = s/t, t = s/v", "Nhớ s ở trên cùng, v và t ở dưới", "Ghi nhớ bộ ba đại lượng s, v, t"]
            )
        }
    ),

    "VL03": OfflineSampleProblem(
        problem_id="VL03",
        title="Trọng lượng và Khối lượng bao gạo",
        strand=KnowledgeStrand.PHYSICS,
        problem_text=(
            "Một bao gạo có khối lượng m = 45 kg đặt yên trên sàn nhà. "
            "Hãy xác định độ lớn trọng lượng P của bao gạo và nêu rõ đơn vị đo lực tương ứng."
        ),
        given_facts=["Khối lượng bao gạo m = 45 kg"],
        core_concepts=["Trọng lượng và Khối lượng", "Hệ thức P = 10m"],
        target_variable="Trọng lượng P (Newton)",
        common_pitfall="Nhầm lẫn đơn vị giữa khối lượng (kg) và trọng lượng (Newton).",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Bài toán này gắn liền với đời sống hàng ngày của chúng mình.",
                question="Đề bài cho biết khối lượng của bao gạo là bao nhiêu và hỏi đại lượng nào?",
                micro_hint="Khối lượng m = 45 kg, đề bài hỏi trọng lượng P.",
                quick_replies=["Khối lượng m = 45 kg, hỏi trọng lượng P", "Cho m = 45 kg, tìm P", "Tìm trọng lượng của bao gạo"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Chính xác! Đề bài hỏi trọng lượng P của bao gạo.",
                question="Ở gần bề mặt Trái Đất, trọng lượng P và khối lượng m của một vật liên hệ với nhau qua hệ thức nào?",
                micro_hint="Hệ thức gần đúng trong SGK KHTN 7: P = 10 * m.",
                quick_replies=["P = 10m", "P = 10 * m", "Trọng lượng bằng 10 lần khối lượng"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Rất chuẩn! P = 10m là công thức cốt lõi.",
                question="Khối lượng m của vật bắt buộc phải có đơn vị là gì thì mới áp dụng được công thức P = 10m?",
                micro_hint="Trong hệ đo lường quốc tế, khối lượng m phải tính bằng kilôgam (kg).",
                quick_replies=["Bắt buộc là kilôgam (kg)", "Đơn vị chuẩn là kg", "Khối lượng phải là kg"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Rất chính xác! Đề bài đã cho sẵn đơn vị kg nên không cần đổi nữa.",
                question="Đơn vị chuẩn của trọng lượng (và mọi loại lực) trong hệ đo lường KHTN là gì?",
                micro_hint="Được đặt theo tên nhà bác học Isaac Newton, ký hiệu là N.",
                quick_replies=["Newton (kí hiệu N)", "Đơn vị Newton (N)", "Kí hiệu là N"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Em làm rất tốt! Phân biệt rành mạch giữa khối lượng và trọng lượng là nền tảng quan trọng.",
                question="Em hãy nêu sự khác nhau cơ bản nhất giữa khối lượng (kg) và trọng lượng (N)?",
                micro_hint="Khối lượng chỉ lượng chất chứa trong vật; trọng lượng là lực hút Trái Đất tác dụng lên vật.",
                quick_replies=["Khối lượng là lượng chất (kg), trọng lượng là lực hút (N)", "Một cái là chất (kg), một cái là lực (N)"]
            )
        }
    ),

    "VL04": OfflineSampleProblem(
        problem_id="VL04",
        title="Lực ma sát khi kéo khối gỗ",
        strand=KnowledgeStrand.PHYSICS,
        problem_text=(
            "Một bạn học sinh kéo một khối gỗ trượt đều trên mặt bàn nằm ngang với lực kéo theo phương ngang F_kéo = 15 N. "
            "Biết rằng khối gỗ chuyển động thẳng đều, hãy cho biết độ lớn của lực ma sát trượt tác dụng lên khối gỗ."
        ),
        given_facts=["Lực kéo F_kéo = 15 N theo phương ngang", "Khối gỗ chuyển động thẳng đều"],
        core_concepts=["Lực ma sát", "Hai lực cân bằng"],
        target_variable="Lực ma sát trượt F_ms (N)",
        common_pitfall="Không chú ý cụm từ 'chuyển động thẳng đều' để áp dụng tính chất hai lực cân bằng.",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Đây là thí nghiệm đo lực ma sát rất quen thuộc trong phòng thực hành KHTN.",
                question="Trong đề bài, cụm từ nào mô tả trạng thái chuyển động của khối gỗ khi đang bị kéo?",
                micro_hint="Chú ý từ khóa: 'chuyển động thẳng đều'.",
                quick_replies=["Chuyển động thẳng đều", "Khối gỗ trượt thẳng đều", "F_kéo = 15 N và thẳng đều"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Rất tinh tế! Từ khóa 'chuyển động thẳng đều' là chìa khóa mở bài toán.",
                question="Khi một vật đang chuyển động thẳng đều dưới tác dụng của hai lực nằm ngang, hai lực đó có quan hệ gì với nhau?",
                micro_hint="Đó là hai lực cân bằng (cùng phương, ngược chiều, cùng độ lớn).",
                quick_replies=["Hai lực cân bằng", "Hai lực có độ lớn bằng nhau", "Cùng độ lớn, ngược chiều"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Chính xác! Lực kéo và lực ma sát trượt là hai lực cân bằng nhau.",
                question="Vì hai lực này cân bằng, em hãy suy luận xem độ lớn của lực ma sát trượt so với lực kéo 15 N như thế nào?",
                micro_hint="Hai lực cân bằng có cùng độ lớn, nên F_ms = F_kéo.",
                quick_replies=["Bằng nhau, F_ms = 15 N", "F_ms có cùng độ lớn với F_kéo", "Độ lớn bằng 15 N"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Lập luận rất logic và chặt chẽ!",
                question="Nếu bề mặt bàn được bôi một lớp dầu trơn nhẵn, em dự đoán lực kéo cần thiết để khối gỗ trượt đều sẽ tăng hay giảm?",
                micro_hint="Dầu làm giảm ma sát tiếp xúc, nên lực kéo cần thiết sẽ giảm đi.",
                quick_replies=["Lực kéo sẽ giảm vì ma sát giảm", "Giảm đi vì bề mặt trơn hơn", "Ma sát giảm nên kéo nhẹ hơn"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Tuyệt vời! Em đã hiểu sâu sắc bản chất của lực cản trở và lực cân bằng.",
                question="Trong đời sống, em hãy kể tên một ví dụ lực ma sát có ích và một ví dụ ma sát có hại?",
                micro_hint="Có ích: đế giày giúp không trượt té; Có hại: làm mòn lốp xe, nóng trục quay.",
                quick_replies=["Có ích giúp đi lại không ngã; Có hại làm mòn lốp xe", "Ma sát ở phanh xe có ích; mòn xích xe có hại"]
            )
        }
    ),

    # =========================================================================
    # MẠCH 2: HÓA HỌC THCS (CHẤT & BIẾN ĐỔI HÓA HỌC) - 4 BÀI
    # =========================================================================
    "HH01": OfflineSampleProblem(
        problem_id="HH01",
        title="Định luật bảo toàn khối lượng khi đốt than",
        strand=KnowledgeStrand.CHEMISTRY,
        problem_text=(
            "Đốt cháy hoàn toàn 12 g carbon (than) trong bình chứa khí oxygen. "
            "Sau phản ứng, người ta thu được 44 g khí carbon dioxide (CO₂). "
            "Hãy áp dụng định luật bảo toàn khối lượng để tính khối lượng khí oxygen đã tham gia phản ứng."
        ),
        given_facts=["m_Carbon = 12 g", "m_CO₂ tạo thành = 44 g"],
        core_concepts=["Định luật bảo toàn khối lượng", "Phương trình chữ của phản ứng"],
        target_variable="Khối lượng oxygen đã phản ứng m_O₂ (g)",
        common_pitfall="Cộng hai số lại thay vì lấy sản phẩm trừ đi chất tham gia đã biết.",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Chúng mình cùng tìm hiểu định luật quan trọng nhất của hóa học nhé.",
                question="Trước phản ứng có những chất tham gia nào và sau phản ứng sinh ra chất sản phẩm nào?",
                micro_hint="Chất tham gia: Carbon và Oxygen. Sản phẩm: Khí Carbon dioxide (CO₂).",
                quick_replies=["Tham gia: Carbon + Oxygen; Sản phẩm: CO₂", "Carbon cháy trong Oxygen tạo ra CO₂", "Chất phản ứng là C và O₂"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Rất chính xác! Em đã xác định đúng chất tham gia và sản phẩm.",
                question="Nội dung chính của Định luật bảo toàn khối lượng phát biểu về mối liên hệ giữa khối lượng chất tham gia và sản phẩm như thế nào?",
                micro_hint="Tổng khối lượng các chất tham gia bằng tổng khối lượng các sản phẩm: m_tham_gia = m_san_pham.",
                quick_replies=["Tổng m chất tham gia = Tổng m sản phẩm", "m_Carbon + m_Oxygen = m_CO₂", "Khối lượng trước và sau phản ứng bằng nhau"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Chuẩn xác! Biểu thức m_C + m_O₂ = m_CO₂ là chìa khóa của bài toán.",
                question="Muốn tìm khối lượng khí oxygen đã phản ứng (m_O₂), em thực hiện phép tính biến đổi như thế nào từ biểu thức trên?",
                micro_hint="Chuyển vế: m_O₂ = m_CO₂ - m_C.",
                quick_replies=["m_O₂ = m_CO₂ - m_C", "Lấy khối lượng CO₂ trừ đi khối lượng Carbon", "Lấy 44 trừ đi 12"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Lập luận toán học trong hóa học rất chặt chẽ!",
                question="Nếu thực hiện phản ứng này trong một cái chén để hở ngoài không khí, khối lượng còn lại trong chén sẽ nặng hơn hay nhẹ hơn ban đầu, vì sao?",
                micro_hint="Khí CO₂ sinh ra sẽ bay vào không khí, nên phần còn lại trong chén sẽ giảm đi.",
                quick_replies=["Nhẹ hơn vì khí CO₂ bay đi mất", "Giảm khối lượng do khí thoát ra", "Khí bay mất nên chén nhẹ hơn"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Tuyệt vời! Em đã nắm rất vững định luật bảo toàn khối lượng của Lomonosov - Lavoisier.",
                question="Em hãy rút ra kết luận: Khi áp dụng định luật bảo toàn khối lượng, cần chú ý điều gì đối với các chất khí sinh ra?",
                micro_hint="Phải tính cả khối lượng của chất khí bay lên hoặc chất kết tủa, không được bỏ sót.",
                quick_replies=["Phải tính đủ cả chất khí bay ra", "Không được bỏ qua chất khí", "Tính toàn bộ các chất tham gia và sản phẩm"]
            )
        }
    ),

    "HH02": OfflineSampleProblem(
        problem_id="HH02",
        title="Phản ứng nung đá vôi",
        strand=KnowledgeStrand.CHEMISTRY,
        problem_text=(
            "Nung 100 g đá vôi (thành phần chính là calcium carbonate CaCO₃), sau một thời gian phản ứng thu được "
            "56 g vôi sống (calcium oxide CaO) và một lượng khí carbon dioxide (CO₂) thoát ra. "
            "Tính khối lượng khí CO₂ đã sinh ra."
        ),
        given_facts=["m_CaCO₃ ban đầu = 100 g", "m_CaO thu được = 56 g"],
        core_concepts=["Định luật bảo toàn khối lượng", "Phản ứng phân hủy"],
        target_variable="Khối lượng khí CO₂ thoát ra (g)",
        common_pitfall="Nghĩ rằng khối lượng bị mất đi do phản ứng hóa học chứ không nhận ra khí CO₂ thoát ra.",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Nung đá vôi là quy trình sản xuất vôi tôi lâu đời trong dân gian.",
                question="Chất ban đầu đem nung là chất nào và sinh ra hai chất mới nào sau phản ứng?",
                micro_hint="Ban đầu: CaCO₃ (100 g). Sinh ra: CaO (56 g) và khí CO₂.",
                quick_replies=["Ban đầu là đá vôi CaCO₃, sinh ra CaO và CO₂", "CaCO₃ phân hủy thành CaO và CO₂", "Chất phản ứng: CaCO₃, sản phẩm: CaO + CO₂"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Đúng rồi! Phản ứng xảy ra là: Đá vôi → Vôi sống + Khí carbon dioxide.",
                question="Theo định luật bảo toàn khối lượng, tổng khối lượng của sản phẩm (CaO + CO₂) có bằng khối lượng đá vôi ban đầu không?",
                micro_hint="Định luật bảo toàn khối lượng luôn đúng: m_CaCO₃ = m_CaO + m_CO₂.",
                quick_replies=["Bằng nhau: m_CaCO₃ = m_CaO + m_CO₂", "Luôn bằng nhau", "Tổng khối lượng sản phẩm bằng khối lượng chất ban đầu"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Rất chính xác! m_CaCO₃ = m_CaO + m_CO₂.",
                question="Để tìm khối lượng khí CO₂ thoát ra ngoài, em làm thế nào từ khối lượng 100 g và 56 g?",
                micro_hint="Khối lượng CO₂ = m_CaCO₃ - m_CaO.",
                quick_replies=["Lấy m_CaCO₃ trừ m_CaO", "m_CO₂ = 100 - 56", "Lấy tổng trừ đi chất đã biết"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Lập luận rất sắc bén và chuẩn xác!",
                question="Em hãy cộng lại khối lượng của CaO và CO₂ xem có đúng bằng 100 g ban đầu không?",
                micro_hint="Cộng khối lượng CaO và CO₂ xem có đúng bằng 100 g đá vôi ban đầu không nhé.",
                quick_replies=["56 + 44 = 100 g, hoàn toàn trùng khớp", "Đúng bằng 100 g", "Đã kiểm tra lại và đúng"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Xuất sắc! Em đã chứng minh rằng vật chất không tự nhiên sinh ra hay mất đi.",
                question="Tại sao khi đốt cháy hay nung chất ngoài trời, người ta hay có cảm giác khối lượng bị 'hao hụt'?",
                micro_hint="Do có các chất khí nhẹ hơn bay lên không khí mà mắt thường khó nhìn thấy.",
                quick_replies=["Vì chất khí sinh ra bay vào không khí", "Khí bay mất nên tưởng hao hụt", "Do khí thoát ra môi trường"]
            )
        }
    ),

    "HH03": OfflineSampleProblem(
        problem_id="HH03",
        title="Tính nồng độ phần trăm dung dịch muối ăn",
        strand=KnowledgeStrand.CHEMISTRY,
        problem_text=(
            "Hòa tan hoàn toàn 15 g muối ăn (chất tan NaCl) vào 185 g nước cất (dung môi). "
            "Hãy xác định khối lượng dung dịch thu được và tính nồng độ phần trăm (C%) của dung dịch muối ăn này."
        ),
        given_facts=["Khối lượng chất tan m_ct = 15 g", "Khối lượng dung môi m_dm = 185 g"],
        core_concepts=["Khối lượng dung dịch m_dd = m_ct + m_dm", "Nồng độ phần trăm C%"],
        target_variable="Nồng độ phần trăm C% (%)",
        common_pitfall="Lấy chất tan chia thẳng cho dung môi (15 / 185) thay vì chia cho khối lượng dung dịch (15 / 200).",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Pha chế nước muối sinh lý là một ứng dụng rất phổ biến trong y tế.",
                question="Đề bài cho biết chất tan là gì, dung môi là gì và khối lượng của từng chất là bao nhiêu?",
                micro_hint="Chất tan là muối ăn (15 g), dung môi là nước (185 g).",
                quick_replies=["Chất tan: muối 15 g; Dung môi: nước 185 g", "m_ct = 15 g, m_dm = 185 g", "Muối 15 g và nước 185 g"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Đúng rồi! Em đã phân biệt rất rõ giữa chất tan và dung môi.",
                question="Dung dịch là hỗn hợp của chất tan và dung môi. Vậy khối lượng dung dịch (m_dd) được tính bằng công thức nào?",
                micro_hint="m_dd = m_ct + m_dm (khối lượng dung dịch = khối lượng chất tan + khối lượng dung môi).",
                quick_replies=["m_dd = m_ct + m_dm", "Khối lượng dung dịch = chất tan + nước", "m_dd bằng tổng chất tan và dung môi"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Chính xác! m_dd = 15 + 185 = 200 g.",
                question="Công thức chuẩn để tính nồng độ phần trăm C% của dung dịch trong SGK KHTN 7 là gì?",
                micro_hint="C% = (m_ct / m_dd) * 100%.",
                quick_replies=["C% = (m_ct / m_dd) * 100%", "C% = chất tan chia dung dịch nhân 100", "Lấy m_ct chia m_dd rồi nhân 100%"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Rất xuất sắc! Nhớ chia cho m_dd chứ không chia cho m_dm nhé!",
                question="Theo em, nếu ta cho thêm nước vào dung dịch trên thì nồng độ phần trăm C% sẽ tăng lên hay giảm đi?",
                micro_hint="Thêm dung môi nước thì dung dịch bị pha loãng ra, nên C% sẽ giảm đi.",
                quick_replies=["C% sẽ giảm đi vì dung dịch bị loãng", "Giảm nồng độ vì thêm nước", "Dung dịch loãng hơn nên C% giảm"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Tuyệt vời! Em đã tránh được lỗi sai kinh điển nhất của học sinh khi tính nồng độ.",
                question="Lỗi sai phổ biến nhất khi tính C% là gì và cách phòng tránh như thế nào?",
                micro_hint="Lỗi sai là lấy chất tan chia cho nước. Phải luôn cộng m_dd trước khi tính C%.",
                quick_replies=["Quên cộng khối lượng dung môi để ra m_dd", "Lấy nhầm m_dm thay vì m_dd", "Phải tính m_dd = m_ct + m_dm trước"]
            )
        }
    ),

    "HH04": OfflineSampleProblem(
        problem_id="HH04",
        title="Phân biệt hiện tượng vật lý và hiện tượng hóa học",
        strand=KnowledgeStrand.CHEMISTRY,
        problem_text=(
            "Hãy xét hai hiện tượng sau: (1) Cồn để trong lọ không đậy nắp bị bay hơi dần; "
            "(2) Đốt cháy cồn trong đĩa tạo thành khí carbon dioxide và hơi nước. "
            "Hiện tượng nào là hiện tượng vật lý, hiện tượng nào là hiện tượng hóa học? Vì sao?"
        ),
        given_facts=["Hiện tượng 1: Cồn bay hơi", "Hiện tượng 2: Cồn cháy sinh ra CO₂ và H₂O"],
        core_concepts=["Hiện tượng vật lý", "Hiện tượng hóa học", "Dấu hiệu tạo chất mới"],
        target_variable="Phân loại hiện tượng 1 và 2 kèm lý giải",
        common_pitfall="Không nêu được dấu hiệu cốt lõi là 'có chất mới sinh ra hay không'.",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Đây là bài học nền tảng giúp phân biệt rõ ranh giới giữa Vật lý và Hóa học.",
                question="Ở hiện tượng (1), cồn bị biến đổi về mặt nào (hình dạng, trạng thái hay thành chất khác)?",
                micro_hint="Cồn từ thể lỏng chuyển sang thể hơi (chỉ thay đổi trạng thái, vẫn là chất cồn).",
                quick_replies=["Chỉ đổi từ lỏng sang hơi, vẫn là cồn", "Thay đổi trạng thái vật chất", "Biến đổi trạng thái lỏng sang khí"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Rất đúng! Chất cồn không hề mất đi mà chỉ hóa hơi.",
                question="Dấu hiệu then chốt nhất để khẳng định một quá trình là hiện tượng hóa học là gì?",
                micro_hint="Phải có sự biến đổi chất này thành chất khác (có chất mới sinh ra).",
                quick_replies=["Có chất mới tạo thành", "Tạo ra chất mới khác chất ban đầu", "Biến đổi thành chất khác"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Hoàn toàn chính xác! 'Có sinh ra chất mới' là tiêu chí duy nhất.",
                question="Ở hiện tượng (2), khi đốt cồn, những chất mới nào đã xuất hiện mà ban đầu không có?",
                micro_hint="Xuất hiện khí carbon dioxide (CO₂) và hơi nước (H₂O).",
                quick_replies=["Sinh ra CO₂ và hơi nước H₂O", "Tạo thành chất mới là CO₂ và nước", "Khí CO₂ và nước"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Lập luận rất sắc bén! Em đã liên kết hiện tượng với bản chất phân tử rất tốt.",
                question="Từ hai lập luận trên, em kết luận: Hiện tượng (1) và hiện tượng (2) thuộc loại hiện tượng nào?",
                micro_hint="(1) là hiện tượng vật lý; (2) là hiện tượng hóa học.",
                quick_replies=["(1) là vật lý, (2) là hóa học", "1: Hiện tượng vật lý; 2: Hiện tượng hóa học"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Tuyệt đỉnh! Em đã phân biệt rành rẽ giữa biến đổi vật lý và phản ứng hóa học.",
                question="Khi em xé vụn một tờ giấy và khi em châm lửa đốt tờ giấy, hai hành động đó khác nhau thế nào?",
                micro_hint="Xé giấy: chỉ đổi kích thước (vật lý). Đốt giấy: cháy thành tro và khói (hóa học).",
                quick_replies=["Xé giấy là vật lý, đốt giấy là hóa học", "Xé là đổi hình dạng, đốt tạo ra tro than mới"]
            )
        }
    ),

    # =========================================================================
    # MẠCH 3: SINH HỌC THCS (CƠ THỂ SỐNG & TRAO ĐỔI CHẤT) - 4 BÀI
    # =========================================================================
    "SH01": OfflineSampleProblem(
        problem_id="SH01",
        title="Quang hợp ở thực vật",
        strand=KnowledgeStrand.BIOLOGY,
        problem_text=(
            "Viết phương trình chữ của quá trình quang hợp ở thực vật. "
            "Chỉ rõ nguyên liệu lấy vào, sản phẩm tạo thành và điều kiện bắt buộc để quá trình quang hợp diễn ra."
        ),
        given_facts=["Quá trình quang hợp diễn ra ở lá cây"],
        core_concepts=["Quang hợp ở thực vật", "Diệp lục và Ánh sáng", "Chất hữu cơ (glucose) và Oxygen"],
        target_variable="Phương trình chữ quang hợp + Nguyên liệu/Sản phẩm/Điều kiện",
        common_pitfall="Nhầm lẫn khí lấy vào là oxygen và khí thải ra là carbon dioxide (nhầm với hô hấp).",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Lá cây được ví như những nhà máy xanh kỳ diệu của Trái Đất.",
                question="Để quang hợp được, cây xanh phải hấp thụ những chất gì từ đất và không khí xung quanh?",
                micro_hint="Lấy nước từ rễ hút trong đất và lấy khí carbon dioxide (CO₂) từ không khí qua khí khổng.",
                quick_replies=["Lấy nước từ rễ và khí CO₂ từ không khí", "Nước và Carbon dioxide", "Hút nước từ đất, hấp thụ CO₂"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Chính xác! Đó chính là hai nguyên liệu đầu vào.",
                question="Để biến đổi hai nguyên liệu đó thành chất hữu cơ, cây xanh cần có hai điều kiện bắt buộc nào?",
                micro_hint="Cần có năng lượng ánh sáng mặt trời và chất diệp lục trong bào quan lục lạp.",
                quick_replies=["Ánh sáng và chất diệp lục", "Cần ánh sáng mặt trời và lục lạp", "Ánh sáng + diệp lục"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Rất chuẩn! Không có ánh sáng và diệp lục thì không thể quang hợp.",
                question="Sau khi tổng hợp, quang hợp tạo ra chất hữu cơ chính nào nuôi cây và giải phóng ra khí gì cho sinh giới?",
                micro_hint="Tạo ra chất hữu cơ (glucose/tinh bột) và giải phóng khí oxygen (O₂).",
                quick_replies=["Tạo chất hữu cơ (glucose) và khí Oxygen", "Sinh ra tinh bột và khí O₂", "Chất hữu cơ + Khí oxygen"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Em trả lời rất chuẩn xác! Các thành phần đều đã đầy đủ.",
                question="Em hãy ghép lại thành phương trình chữ hoàn chỉnh dạng: Nguyên liệu --(Điều kiện)--> Sản phẩm?",
                micro_hint="Nước + Khí carbon dioxide --(Ánh sáng, Diệp lục)--> Chất hữu cơ + Khí oxygen.",
                quick_replies=[
                    "Nước + Carbon dioxide → Chất hữu cơ + Oxygen",
                    "Nước + CO₂ --(Ánh sáng/Diệp lục)--> Glucose + O₂"
                ]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Tuyệt vời! Em đã nắm vững cơ chế nuôi sống cả sinh quyển của cây xanh.",
                question="Tại sao người ta thường khuyên không nên để nhiều chậu cây xanh trong phòng ngủ đóng kín cửa vào ban đêm?",
                micro_hint="Ban đêm không có ánh sáng, cây không quang hợp mà chỉ hô hấp lấy O₂ và thải CO₂.",
                quick_replies=["Vì ban đêm cây không quang hợp mà hô hấp lấy oxy", "Cây hô hấp thải CO₂ gây ngạt thở vào ban đêm"]
            )
        }
    ),

    "SH02": OfflineSampleProblem(
        problem_id="SH02",
        title="Hô hấp tế bào ở hạt nảy mầm",
        strand=KnowledgeStrand.BIOLOGY,
        problem_text=(
            "Khi ngâm hạt giống trong nước ấm để ủ nảy mầm, người ta thấy nhiệt độ của đống hạt tăng lên rõ rệt "
            "và lượng khí oxygen trong bình ủ giảm dần. Quá trình sinh học nào đang diễn ra mạnh mẽ trong hạt giống? Giải thích."
        ),
        given_facts=["Hạt đang ủ nảy mầm", "Nhiệt độ đống hạt tăng lên", "Lượng khí O₂ giảm dần"],
        core_concepts=["Hô hấp tế bào", "Chuyển hóa năng lượng (ATP và Nhiệt)", "Tiêu hao Oxygen"],
        target_variable="Tên quá trình (Hô hấp tế bào) và lý giải hiện tượng tỏa nhiệt/tiêu hao O₂",
        common_pitfall="Nghĩ rằng hạt giống quang hợp được hoặc không biết năng lượng tỏa ra một phần dưới dạng nhiệt.",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Hạt nảy mầm là một hiện tượng thú vị biểu hiện sự sống mãnh liệt.",
                question="Hiện tượng đống hạt nóng lên và lượng khí O₂ giảm chứng tỏ hạt đang hấp thụ khí gì và giải phóng gì?",
                micro_hint="Hạt đang hấp thụ khí oxygen (O₂) và tỏa năng lượng nhiệt ra ngoài.",
                quick_replies=["Hạt hút khí oxygen và tỏa nhiệt", "Hấp thụ O₂ và sinh nhiệt", "Hạt đang lấy O₂ để thở"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Rất chính xác! Hiện tượng đó gắn liền với sự chuyển hóa năng lượng.",
                question="Quá trình tế bào sử dụng oxygen để phân giải chất hữu cơ giải phóng năng lượng được gọi là gì?",
                micro_hint="Đó là quá trình 'Hô hấp tế bào' (diễn ra trong bào quan ty thể).",
                quick_replies=["Hô hấp tế bào", "Quá trình hô hấp tế bào", "Hô hấp ở thực vật"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Đúng rồi! Đó chính là quá trình Hô hấp tế bào.",
                question="Năng lượng giải phóng từ hô hấp tế bào được tích lũy dưới dạng phân tử nào và tỏa ra môi trường dưới dạng gì?",
                micro_hint="Tích lũy trong các phân tử ATP (cung cấp cho hạt mọc mầm) và một phần tỏa ra dưới dạng nhiệt.",
                quick_replies=["Tích lũy dạng ATP và tỏa ra dạng nhiệt", "Dạng năng lượng ATP và nhiệt năng", "ATP để lớn lên và nhiệt làm ấm"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Lập luận sinh học rất chuẩn xác và sâu sắc!",
                question="Nếu ta đậy kín nắp bình ủ hạt và không cho không khí lọt vào, chuyện gì sẽ xảy ra với các hạt mầm?",
                micro_hint="Thiếu oxygen, hạt không hô hấp được, thiếu năng lượng sẽ bị thối và chết.",
                quick_replies=["Hạt bị ngạt, không hô hấp được và chết", "Hạt không nảy mầm được do thiếu O₂", "Hạt bị thối mầm"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Xuất sắc! Em đã hiểu rõ bản chất của hô hấp ở cấp độ tế bào.",
                question="Giữa quang hợp và hô hấp tế bào có mối quan hệ qua lại như thế nào đối với cây xanh?",
                micro_hint="Quang hợp tổng hợp chất hữu cơ và tích lũy năng lượng; Hô hấp phân giải chất hữu cơ để giải phóng năng lượng.",
                quick_replies=["Quang hợp tích lũy năng lượng, hô hấp giải phóng năng lượng", "Hai quá trình trái ngược nhưng bổ trợ cho nhau"]
            )
        }
    ),

    "SH03": OfflineSampleProblem(
        problem_id="SH03",
        title="Thoát hơi nước qua khí khổng ở lá cây",
        strand=KnowledgeStrand.BIOLOGY,
        problem_text=(
            "Vào những ngày nắng nóng gay gắt, người ta quan sát thấy nhiệt độ bề mặt của lá cây thường thấp hơn "
            "nhiệt độ của không khí xung quanh từ vài độ C. Bộ phận nào ở lá giúp cây làm được điều này và quá trình đó mang lại ý nghĩa gì?"
        ),
        given_facts=["Ngày nắng nóng", "Lá cây mát hơn không khí xung quanh"],
        core_concepts=["Thoát hơi nước", "Khí khổng ở biểu bì lá", "Động lực hút nước của rễ"],
        target_variable="Khí khổng + Quá trình thoát hơi nước + Ý nghĩa làm mát/hút khoáng",
        common_pitfall="Chỉ nghĩ thoát hơi nước làm mất nước có hại mà không biết vai trò làm mát và kéo cột nước.",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Đây là cơ chế tự bảo vệ rất tài tình của thế giới thực vật.",
                question="Lá cây làm mát cơ thể bằng cách giải phóng lượng nước trong cơ thể ra ngoài qua quá trình sinh lý nào?",
                micro_hint="Quá trình 'Thoát hơi nước' (chủ yếu qua khí khổng ở lá).",
                quick_replies=["Quá trình thoát hơi nước", "Thoát hơi nước qua lá", "Nhờ thoát hơi nước"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Chính xác! Nước bốc hơi mang theo nhiệt lượng làm mát mặt lá.",
                question="Hơi nước chủ yếu thoát ra ngoài môi trường thông qua cấu trúc nhỏ li ti nào trên bề mặt lá?",
                micro_hint="Đó là các 'Khí khổng' nằm ở lớp biểu bì của lá (nhiều nhất ở mặt dưới).",
                quick_replies=["Khí khổng ở biểu bì lá", "Các lỗ khí khổng", "Qua khí khổng"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Rất đúng! Cấu tạo đóng mở của khí khổng điều tiết lượng hơi nước thoát ra.",
                question="Ngoài việc làm mát lá cây, lực hút do thoát hơi nước ở lá còn đóng vai trò quan trọng nào đối với hệ thống rễ?",
                micro_hint="Tạo lực hút kéo dòng nước và muối khoáng hòa tan từ rễ đi lên thân và lá cây.",
                quick_replies=["Tạo lực hút kéo nước và muối khoáng từ rễ lên", "Giúp rễ hút nước và khoáng", "Hút dòng nước đi ngược lên ngọn"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Lập luận rất chuẩn! Thoát hơi nước là động lực đầu trên của dòng mạch gỗ.",
                question="Khi trời nắng quá gắt và đất bị khô hạn, khí khổng sẽ tự động đóng lại hay mở rộng ra? Vì sao?",
                micro_hint="Khí khổng sẽ đóng lại để hạn chế mất nước, tránh cho cây bị héo khô.",
                quick_replies=["Đóng lại để tránh mất nước gây héo", "Tự đóng lại để giữ nước", "Đóng lại bảo vệ cây khỏi mất nước"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Tuyệt vời! Em đã thấu hiểu một trong những cơ chế sinh lý quan trọng nhất của thực vật.",
                question="Em hãy tóm tắt 2 ý nghĩa to lớn nhất của quá trình thoát hơi nước đối với đời sống của cây?",
                micro_hint="1. Làm mát lá khi trời nắng; 2. Tạo động lực kéo nước và muối khoáng từ rễ lên.",
                quick_replies=["Làm mát lá và hút nước khoáng từ rễ lên", "Giảm nhiệt độ lá + hút nước từ dưới đất"]
            )
        }
    ),

    "SH04": OfflineSampleProblem(
        problem_id="SH04",
        title="Tính hướng sáng của ngọn cây",
        strand=KnowledgeStrand.BIOLOGY,
        problem_text=(
            "Khi đặt một chậu cây cảnh ở gần cửa sổ chỉ có ánh sáng chiếu từ một phía, sau vài ngày người ta thấy "
            "ngọn cây mọc uốn cong về phía có ánh sáng. Hiện tượng này thuộc hình thức cảm ứng nào ở thực vật và có ý nghĩa gì đối với cây?"
        ),
        given_facts=["Chậu cây đặt gần cửa sổ", "Ánh sáng chiếu từ một phía", "Ngọn cây uốn cong về phía ánh sáng"],
        core_concepts=["Cảm ứng ở sinh vật", "Tính hướng sáng (hướng động dương)", "Ý nghĩa thu nhận ánh sáng quang hợp"],
        target_variable="Tính hướng sáng (hướng động dương) + Ý nghĩa thu nhận ánh sáng",
        common_pitfall="Nhầm tính hướng sáng với tính hướng trọng lực hoặc không nêu được vai trò của quang hợp.",
        cached_phases={
            "clarify": SocraticPhaseDialogue(
                phase_name="clarify",
                feedback="Chào em! Cây cối tuy không biết đi nhưng lại có những phản ứng phản xạ rất kỳ diệu.",
                question="Hiện tượng ngọn cây uốn cong về phía có ánh sáng là phản ứng của cây đối với tác nhân nào từ môi trường?",
                micro_hint="Tác nhân kích thích ở đây chính là 'Ánh sáng'.",
                quick_replies=["Tác nhân là ánh sáng chiếu từ một phía", "Ánh sáng mặt trời", "Kích thích từ ánh sáng"]
            ),
            "recall": SocraticPhaseDialogue(
                phase_name="recall",
                feedback="Đúng rồi! Ánh sáng là nhân tố định hướng cho sự sinh trưởng của ngọn cây.",
                question="Khả năng cơ thể sinh vật phản ứng lại các kích thích của môi trường để thích nghi được gọi là gì?",
                micro_hint="Đó là hiện tượng 'Cảm ứng' (ở thực vật gọi là tính hướng động).",
                quick_replies=["Hiện tượng cảm ứng", "Cảm ứng ở thực vật", "Tính hướng động"]
            ),
            "reason": SocraticPhaseDialogue(
                phase_name="reason",
                feedback="Rất chính xác! Hiện tượng ngọn cây hướng về nguồn sáng được gọi cụ thể là 'Tính hướng sáng'.",
                question="Tại sao ngọn cây lại cần uốn cong về phía có ánh sáng mạnh nhất? Điều đó giúp ích gì cho cây?",
                micro_hint="Giúp các lá cây tiếp nhận được nhiều ánh sáng nhất để thực hiện quá trình quang hợp.",
                quick_replies=["Để hấp thụ nhiều ánh sáng cho quang hợp", "Thu nhận ánh sáng để quang hợp tốt hơn", "Quang hợp thuận lợi hơn"]
            ),
            "check": SocraticPhaseDialogue(
                phase_name="check",
                feedback="Lập luận sinh thái và sinh lý thực vật rất gắn kết!",
                question="Nếu ngọn cây có tính hướng sáng dương (hướng về phía ánh sáng), thì bộ rễ cây dưới đất lại hướng về phía nào?",
                micro_hint="Rễ cây hướng xuống lòng đất (hướng trọng lực dương và hướng sáng âm).",
                quick_replies=["Rễ hướng xuống đất tìm nước (hướng trọng lực)", "Rễ tránh ánh sáng và tìm nguồn nước", "Hướng xuống lòng đất"]
            ),
            "generalize": SocraticPhaseDialogue(
                phase_name="generalize",
                feedback="Xuất sắc! Em đã hoàn thành trọn vẹn chuỗi tìm hiểu về tập tính thích nghi của thực vật.",
                question="Trong trồng trọt, người nông dân ứng dụng tính hướng sáng của cây như thế nào khi gieo trồng cây trồng?",
                micro_hint="Trồng cây với mật độ hợp lý, tỉa cành để cây không che khuất ánh sáng của nhau.",
                quick_replies=["Trồng đúng khoảng cách để cây nhận đủ ánh sáng", "Tỉa bớt cành lá để cây đón nắng", "Bố trí mật độ gieo trồng phù hợp"]
            )
        }
    )
}


def get_all_offline_problems() -> List[OfflineSampleProblem]:
    """Trả về danh sách 12 bài toán mẫu có sẵn trong cache."""
    return list(OFFLINE_SAMPLE_PROBLEMS.values())


def get_offline_problem_by_id(prob_id: str) -> Optional[OfflineSampleProblem]:
    """Tìm kiếm bài mẫu theo mã định danh (VL01, HH01, SH01...)."""
    return OFFLINE_SAMPLE_PROBLEMS.get(prob_id)


def get_offline_problems_by_strand(strand: KnowledgeStrand) -> List[OfflineSampleProblem]:
    """Lọc danh sách bài mẫu theo mạch kiến thức KHTN 7."""
    return [p for p in OFFLINE_SAMPLE_PROBLEMS.values() if p.strand == strand]
