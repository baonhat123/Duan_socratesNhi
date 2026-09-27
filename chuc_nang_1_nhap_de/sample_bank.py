"""
Module: sample_bank.py
Chức năng 1 (FR-01): Ngân hàng đề bài mẫu KHTN 7
Đặc tả: Socrates Nhí v3.0

Cung cấp các bài mẫu thuộc 3 mạch kiến thức để thử nghiệm nhanh chức năng nhập đề bài:
1. Cơ học / Đại lượng vật lý
2. Biến đổi chất / Phản ứng hóa học
3. Cơ thể sống / Môi trường
"""

from typing import List, Dict

SAMPLE_PROBLEMS: List[Dict[str, str]] = [
    {
        "id": "co_hoc_01",
        "strand": "Cơ học / Đại lượng vật lý",
        "title": "Tính tốc độ của người đi xe đạp",
        "content": (
            "Một người đi xe đạp chuyển động đều trên quãng đường thẳng dài 12 km "
            "trong thời gian 30 phút. Hãy xác định tốc độ chuyển động của người đó theo đơn vị km/h và m/s."
        ),
        "difficulty": "Cơ bản",
        "concepts": ["Tốc độ v = s/t", "Đổi đơn vị km/h sang m/s"]
    },
    {
        "id": "co_hoc_02",
        "strand": "Cơ học / Đại lượng vật lý",
        "title": "Phân biệt Khối lượng và Trọng lượng",
        "content": (
            "Một thùng hàng có khối lượng m = 45 kg đặt nằm yên trên mặt đất. "
            "Hỏi trọng lượng của thùng hàng đó bằng bao nhiêu Newton (lấy hệ số g = 10 N/kg)?"
        ),
        "difficulty": "Cơ bản",
        "concepts": ["Trọng lượng P = 10m", "Đơn vị Newton (N)"]
    },
    {
        "id": "hoa_hoc_01",
        "strand": "Biến đổi chất / Phản ứng hóa học",
        "title": "Hiện tượng vật lý hay hiện tượng hóa học?",
        "content": (
            "Khi đun nóng đường mía trong chảo, ban đầu đường nóng chảy thành chất lỏng màu vàng nâu, "
            "sau đó tiếp tục đun thì đường chuyển sang màu đen và có mùi khét. "
            "Hãy cho biết giai đoạn nào là hiện tượng vật lý, giai đoạn nào là hiện tượng hóa học? Vì sao?"
        ),
        "difficulty": "Thông hiểu",
        "concepts": ["Hiện tượng vật lý", "Hiện tượng hóa học", "Dấu hiệu tạo chất mới"]
    },
    {
        "id": "hoa_hoc_02",
        "strand": "Biến đổi chất / Phản ứng hóa học",
        "title": "Định luật bảo toàn khối lượng",
        "content": (
            "Đốt cháy hoàn toàn 6 gam bột than (chứa carbon C) trong bình kín chứa khí oxygen (O₂). "
            "Sau phản ứng, người ta thu được 22 gam khí carbon dioxide (CO₂). "
            "Hãy viết phương trình chữ của phản ứng và tính khối lượng khí oxygen đã tham gia phản ứng."
        ),
        "difficulty": "Vận dụng",
        "concepts": ["Phương trình chữ", "Bảo toàn khối lượng: m_C + m_O2 = m_CO2"]
    },
    {
        "id": "sinh_hoc_01",
        "strand": "Cơ thể sống / Môi trường",
        "title": "Phương trình và nguyên liệu của quang hợp",
        "content": (
            "Tại sao vào những ngày nắng gắt, đứng dưới bóng mát của tán cây xanh ta lại cảm thấy dễ chịu hơn "
            "so với đứng dưới mái che bằng tôn? Nêu vai trò của quá trình quang hợp đối với môi trường sống."
        ),
        "difficulty": "Vận dụng",
        "concepts": ["Quang hợp: H2O + CO2 -> C6H12O6 + O2", "Thoát hơi nước", "Điều hòa không khí"]
    },
    {
        "id": "sinh_hoc_02",
        "strand": "Cơ thể sống / Môi trường",
        "title": "Hô hấp tế bào và Trao đổi chất",
        "content": (
            "Giải thích vì sao khi lao động nặng hoặc chạy nhanh một quãng đường dài, "
            "nhịp thở và nhịp tim của con người lại tăng lên rõ rệt?"
        ),
        "difficulty": "Thông hiểu",
        "concepts": ["Hô hấp tế bào", "Nhu cầu năng lượng ATP", "Cung cấp O2 và thải CO2"]
    }
]


def get_all_samples() -> List[Dict[str, str]]:
    return SAMPLE_PROBLEMS


def get_sample_by_id(sample_id: str) -> Dict[str, str]:
    for item in SAMPLE_PROBLEMS:
        if item["id"] == sample_id:
            return item
    return SAMPLE_PROBLEMS[0]
