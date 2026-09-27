"""
Module: sample_bank.py
Chức năng 1 (FR-01): Ngân hàng đề bài mẫu KHTN 7 Đủ 12 Bài Chuẩn SGK
Đặc tả: Socrates Nhí v3.0 (Mục 2.2, Mục 13 & Mục 18.1)

Cung cấp đầy đủ 12 bài mẫu chia đều 3 mạch kiến thức KHTN 7 chuẩn SGK:
- Mạch 1: Cơ học / Đại lượng vật lý (4 bài: VL01, VL02, VL03, VL04)
- Mạch 2: Biến đổi chất / Phản ứng hóa học (4 bài: HH01, HH02, HH03, HH04)
- Mạch 3: Cơ thể sống / Môi trường (4 bài: SH01, SH02, SH03, SH04)

Đồng bộ 100% với Chức năng 7 (offline_bank.py) và hỗ trợ bí danh cũ (co_hoc_01, hoa_hoc_01...).
"""

from typing import List, Dict, Optional

# Danh mục 12 bài mẫu chính thức KHTN 7
SAMPLE_PROBLEMS: List[Dict[str, any]] = [
    # =========================================================================
    # MẠCH 1: VẬT LÝ THCS (CƠ HỌC & ĐẠI LƯỢNG ĐO LƯỜNG) - 4 BÀI
    # =========================================================================
    {
        "id": "VL01",
        "alias_id": "co_hoc_01",
        "strand": "Cơ học / Đại lượng vật lý",
        "strand_short": "Vật lý",
        "title": "Tính tốc độ của người đi xe đạp",
        "content": (
            "Một người đi xe đạp chuyển động đều trên quãng đường thẳng dài 12 km "
            "trong thời gian 30 phút. Hãy xác định tốc độ chuyển động của người đó theo đơn vị km/h và m/s."
        ),
        "difficulty": "Cơ bản",
        "concepts": ["Tốc độ v = s/t", "Đổi đơn vị km/h sang m/s"],
        "icon": "directions_bike_rounded"
    },
    {
        "id": "VL02",
        "alias_id": "co_hoc_03",
        "strand": "Cơ học / Đại lượng vật lý",
        "strand_short": "Vật lý",
        "title": "Quãng đường đoàn tàu chuyển động thẳng đều",
        "content": (
            "Một đoàn tàu đang chuyển động thẳng đều với tốc độ không đổi v = 45 km/h. "
            "Tính quãng đường s mà đoàn tàu đi được trong khoảng thời gian t = 20 phút."
        ),
        "difficulty": "Thông hiểu",
        "concepts": ["Tốc độ chuyển động", "Công thức quãng đường s = v * t"],
        "icon": "train_rounded"
    },
    {
        "id": "VL03",
        "alias_id": "co_hoc_02",
        "strand": "Cơ học / Đại lượng vật lý",
        "strand_short": "Vật lý",
        "title": "Phân biệt Khối lượng và Trọng lượng",
        "content": (
            "Một thùng hàng có khối lượng m = 45 kg đặt nằm yên trên mặt đất. "
            "Hỏi trọng lượng của thùng hàng đó bằng bao nhiêu Newton (lấy hệ số g = 10 N/kg)?"
        ),
        "difficulty": "Cơ bản",
        "concepts": ["Trọng lượng P = 10m", "Đơn vị Newton (N)"],
        "icon": "fitness_center_rounded"
    },
    {
        "id": "VL04",
        "alias_id": "co_hoc_04",
        "strand": "Cơ học / Đại lượng vật lý",
        "strand_short": "Vật lý",
        "title": "Lực ma sát cản trở chuyển động kéo bàn",
        "content": (
            "Một học sinh kéo một chiếc bàn trên sàn phòng học. Hãy giải thích tại sao khi mới bắt đầu kéo "
            "thì thấy rất nặng, nhưng khi bàn đã trượt đều thì kéo nhẹ hơn? Lực nào đã cản trở chuyển động của chiếc bàn?"
        ),
        "difficulty": "Vận dụng",
        "concepts": ["Lực ma sát trượt và ma sát nghỉ", "Tác dụng cản trở chuyển động"],
        "icon": "pan_tool_rounded"
    },

    # =========================================================================
    # MẠCH 2: HÓA HỌC THCS (BIẾN ĐỔI CHẤT & PHẢN ỨNG HÓA HỌC) - 4 BÀI
    # =========================================================================
    {
        "id": "HH01",
        "alias_id": "hoa_hoc_02",
        "strand": "Biến đổi chất / Phản ứng hóa học",
        "strand_short": "Hóa học",
        "title": "Định luật bảo toàn khối lượng khi đốt than",
        "content": (
            "Đốt cháy hoàn toàn 6 gam bột than (chứa carbon C) trong bình kín chứa khí oxygen (O₂). "
            "Sau phản ứng, người ta thu được 22 gam khí carbon dioxide (CO₂). "
            "Hãy viết phương trình chữ của phản ứng và tính khối lượng khí oxygen đã tham gia phản ứng."
        ),
        "difficulty": "Vận dụng",
        "concepts": ["Phương trình chữ", "Bảo toàn khối lượng: m_C + m_O2 = m_CO2"],
        "icon": "local_fire_department_rounded"
    },
    {
        "id": "HH02",
        "alias_id": "hoa_hoc_03",
        "strand": "Biến đổi chất / Phản ứng hóa học",
        "strand_short": "Hóa học",
        "title": "Nung đá vôi tạo vôi sống và khí carbon dioxide",
        "content": (
            "Nung 100 kg đá vôi (thành phần chính là calcium carbonate CaCO₃), thu được 56 kg vôi sống "
            "(calcium oxide CaO) và một lượng khí carbon dioxide (CO₂) thoát ra. "
            "Tính khối lượng khí CO₂ sinh ra từ phản ứng này."
        ),
        "difficulty": "Thông hiểu",
        "concepts": ["Bảo toàn khối lượng", "Phản ứng phân hủy do nhiệt"],
        "icon": "science_rounded"
    },
    {
        "id": "HH03",
        "alias_id": "hoa_hoc_04",
        "strand": "Biến đổi chất / Phản ứng hóa học",
        "strand_short": "Hóa học",
        "title": "Pha chế dung dịch muối ăn và Nồng độ phần trăm",
        "content": (
            "Hòa tan hoàn toàn 15 gam muối ăn (NaCl) vào 85 gam nước cất. "
            "Hãy tính khối lượng dung dịch thu được và nồng độ phần trăm (C%) của dung dịch muối ăn này."
        ),
        "difficulty": "Vận dụng",
        "concepts": ["Khối lượng dung dịch = m_ct + m_dm", "Nồng độ C% = (m_ct / m_dd) * 100%"],
        "icon": "opacity_rounded"
    },
    {
        "id": "HH04",
        "alias_id": "hoa_hoc_01",
        "strand": "Biến đổi chất / Phản ứng hóa học",
        "strand_short": "Hóa học",
        "title": "Hiện tượng vật lý hay hiện tượng hóa học?",
        "content": (
            "Khi đun nóng đường mía trong chảo, ban đầu đường nóng chảy thành chất lỏng màu vàng nâu, "
            "sau đó tiếp tục đun thì đường chuyển sang màu đen và có mùi khét. "
            "Hãy cho biết giai đoạn nào là hiện tượng vật lý, giai đoạn nào là hiện tượng hóa học? Vì sao?"
        ),
        "difficulty": "Thông hiểu",
        "concepts": ["Hiện tượng vật lý", "Hiện tượng hóa học", "Dấu hiệu tạo chất mới"],
        "icon": "bubble_chart_rounded"
    },

    # =========================================================================
    # MẠCH 3: SINH HỌC THCS (CƠ THỂ SỐNG & MÔI TRƯỜNG) - 4 BÀI
    # =========================================================================
    {
        "id": "SH01",
        "alias_id": "sinh_hoc_01",
        "strand": "Cơ thể sống / Môi trường",
        "strand_short": "Sinh học",
        "title": "Phương trình và nguyên liệu của quang hợp",
        "content": (
            "Tại sao vào những ngày nắng gắt, đứng dưới bóng mát của tán cây xanh ta lại cảm thấy dễ chịu hơn "
            "so với đứng dưới mái che bằng tôn? Nêu vai trò của quá trình quang hợp đối với môi trường sống."
        ),
        "difficulty": "Thông hiểu",
        "concepts": ["Quang hợp ở thực vật", "Thoát hơi nước", "Điều hòa không khí"],
        "icon": "eco_rounded"
    },
    {
        "id": "SH02",
        "alias_id": "sinh_hoc_02",
        "strand": "Cơ thể sống / Môi trường",
        "strand_short": "Sinh học",
        "title": "Hô hấp tế bào và Trao đổi chất",
        "content": (
            "Giải thích vì sao khi lao động nặng hoặc chạy nhanh một quãng đường dài, "
            "nhịp thở và nhịp tim của con người lại tăng lên rõ rệt?"
        ),
        "difficulty": "Thông hiểu",
        "concepts": ["Hô hấp tế bào", "Nhu cầu năng lượng ATP", "Cung cấp O2 và thải CO2"],
        "icon": "favorite_rounded"
    },
    {
        "id": "SH03",
        "alias_id": "sinh_hoc_03",
        "strand": "Cơ thể sống / Môi trường",
        "strand_short": "Sinh học",
        "title": "Thoát hơi nước qua khí khổng ở lá cây",
        "content": (
            "Tại sao phần lớn các loài thực vật trên cạn có số lượng khí khổng ở mặt dưới của lá nhiều hơn mặt trên? "
            "Quá trình thoát hơi nước có vai trò gì đối với việc vận chuyển nước và muối khoáng trong cây?"
        ),
        "difficulty": "Vận dụng",
        "concepts": ["Khí khổng và thoát hơi nước", "Động lực hút dòng nước", "Điều hòa nhiệt độ"],
        "icon": "water_drop_rounded"
    },
    {
        "id": "SH04",
        "alias_id": "sinh_hoc_04",
        "strand": "Cơ thể sống / Môi trường",
        "strand_short": "Sinh học",
        "title": "Cảm ứng hướng sáng ở thực vật",
        "content": (
            "Khi đặt một chậu cây cảnh bên bậu cửa sổ có ánh sáng chiếu từ một phía, sau một thời gian "
            "ta quan sát thấy ngọn cây uốn cong về phía ánh sáng. Đây là hiện tượng gì? Nêu ý nghĩa sinh học của nó."
        ),
        "difficulty": "Thông hiểu",
        "concepts": ["Tính hướng sáng", "Cảm ứng ở thực vật", "Hấp thụ ánh sáng quang hợp"],
        "icon": "wb_sunny_rounded"
    }
]


def get_all_samples() -> List[Dict[str, any]]:
    """Trả về toàn bộ 12 bài mẫu KHTN 7."""
    return SAMPLE_PROBLEMS


def get_sample_by_id(sample_id: str) -> Dict[str, any]:
    """Tìm bài mẫu theo ID chính thức (VL01..) hoặc Alias cũ (co_hoc_01..)."""
    for item in SAMPLE_PROBLEMS:
        if item["id"] == sample_id or item.get("alias_id") == sample_id:
            return item
    return SAMPLE_PROBLEMS[0]


def get_samples_by_strand(strand_filter: str) -> List[Dict[str, any]]:
    """Lọc danh sách bài tập mẫu theo mạch kiến thức ('Vật lý', 'Hóa học', 'Sinh học')."""
    if not strand_filter or strand_filter.lower() in ["tất cả", "all"]:
        return SAMPLE_PROBLEMS
    return [
        s for s in SAMPLE_PROBLEMS
        if strand_filter.lower() in s["strand"].lower() or strand_filter.lower() in s.get("strand_short", "").lower()
    ]
