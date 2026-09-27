"""
Module: concept_bank.py
Chức năng 3 (FR-03): Bản đồ Khái niệm Khoa học tự nhiên 7 (Do đội biên soạn)
Đặc tả: Socrates Nhí v3.0 (Mục 2.2 & Mục 13 - Nguồn dữ liệu bản đồ khái niệm)

Quy tắc bắt buộc:
- Bản đồ khái niệm do đội biên soạn là NGUỒN CHÍNH THỨC DUY NHẤT.
- LLM chỉ được CHỌN tối đa 3 khái niệm từ danh sách này, TUYỆT ĐỐI KHÔNG TỰ BỊA.
- Mỗi bài toán có sẵn khái niệm, công thức và lỗi thường gặp để neo hội thoại.
- Bao phủ đầy đủ 12 bài mẫu KHTN 7 chuẩn SGK chia đều 3 mạch.
"""

from typing import Dict, List
from .classifier_model import KnowledgeStrand, CoreConcept

# Bản đồ khái niệm chính thức chuẩn SGK KHTN 7
CONCEPT_MAP: Dict[str, CoreConcept] = {
    # =========================================================================
    # MẠCH 1: CƠ HỌC / ĐẠI LƯỢNG VẬT LÝ
    # =========================================================================
    "toc_do": CoreConcept(
        name="Tốc độ chuyển động",
        formula="v = s / t",
        description="Đặc trưng cho mức độ nhanh hay chậm của chuyển động, tính bằng quãng đường đi được trong một đơn vị thời gian.",
        common_pitfalls=["Quên đổi đơn vị thời gian (phút sang giờ hoặc giây)", "Lấy quãng đường nhân thời gian thay vì chia"]
    ),
    "quang_duong_chuyen_dong": CoreConcept(
        name="Quãng đường chuyển động thẳng đều",
        formula="s = v * t",
        description="Quãng đường đi được bằng tích của tốc độ chuyển động và thời gian đi.",
        common_pitfalls=["Lấy tốc độ chia cho thời gian", "Không quy đổi thời gian phút về cùng hệ đo của tốc độ (km/h sang giờ)"]
    ),
    "doi_don_vi_toc_do": CoreConcept(
        name="Đổi đơn vị tốc độ (km/h ↔ m/s)",
        formula="1 m/s = 3.6 km/h",
        description="Quy đổi qua lại giữa hai đơn vị đo tốc độ chuẩn trong hệ đo lường.",
        common_pitfalls=["Nhầm lẫn giữa nhân 3.6 và chia 3.6 khi đổi từ km/h sang m/s"]
    ),
    "khoi_luong_trong_luong": CoreConcept(
        name="Trọng lượng và Khối lượng",
        formula="P = 10m",
        description="Khối lượng là lượng chất chứa trong vật (kg). Trọng lượng là độ lớn lực hút Trái Đất tác dụng lên vật (N).",
        common_pitfalls=["Đồng nhất trọng lượng và khối lượng là một", "Quên đổi khối lượng gam (g) ra kilôgam (kg) trước khi tính P"]
    ),
    "luc_ma_sat": CoreConcept(
        name="Lực ma sát",
        formula="F_ms",
        description="Lực xuất hiện ở bề mặt tiếp xúc giữa hai vật và cản trở chuyển động của vật.",
        common_pitfalls=["Nghĩ rằng ma sát luôn có hại mà quên vai trò giúp người đi lại được", "Nhầm giữa ma sát nghỉ và ma sát trượt"]
    ),
    "phan_xa_anh_sang": CoreConcept(
        name="Định luật phản xạ ánh sáng trên gương phẳng",
        formula="i' = i (Góc phản xạ = Góc tới)",
        description="Khi tia sáng gặp mặt gương phẳng, tia sáng bị phản xạ hắt trở lại môi trường cũ. Tia phản xạ nằm trong mặt phẳng tới và góc phản xạ bằng góc tới.",
        common_pitfalls=["Nghĩ rằng ánh sáng đi xuyên qua gương phẳng như qua kính trong suốt", "Nhầm lẫn góc tới là góc hợp bởi tia tới với mặt gương thay vì với pháp tuyến"]
    ),

    # =========================================================================
    # MẠCH 2: BIẾN ĐỔI CHẤT / PHẢN ỨNG HÓA HỌC
    # =========================================================================
    "hien_tuong_vat_ly_hoa_hoc": CoreConcept(
        name="Hiện tượng vật lý và Hiện tượng hóa học",
        formula="Chất ban đầu → Chất mới",
        description="Hiện tượng vật lý chỉ biến đổi về trạng thái, hình dạng. Hiện tượng hóa học có sự biến đổi chất này thành chất khác.",
        common_pitfalls=["Nhầm sự nóng chảy hoặc bay hơi là hiện tượng hóa học", "Chưa tìm ra dấu hiệu tạo chất mới (màu sắc, mùi, kết tủa)"]
    ),
    "bao_toan_khoi_luong": CoreConcept(
        name="Định luật bảo toàn khối lượng",
        formula="m_tham_gia = m_san_pham",
        description="Trong một phản ứng hóa học, tổng khối lượng của các chất tham gia bằng tổng khối lượng của các sản phẩm tạo thành.",
        common_pitfalls=["Bỏ quên khối lượng của chất khí thoát ra (O₂, CO₂)", "Cộng sai số hạng giữa các vế của phương trình"]
    ),
    "phuong_trinh_chu": CoreConcept(
        name="Phương trình chữ của phản ứng",
        formula="Chất tham gia 1 + Chất tham gia 2 → Sản phẩm",
        description="Cách biểu diễn phản ứng hóa học bằng tên các chất.",
        common_pitfalls=["Viết ngược vế sản phẩm sang chất tham gia", "Nhầm lẫn chất xúc tác với chất tham gia"]
    ),
    "nung_da_voi": CoreConcept(
        name="Phản ứng phân hủy đá vôi do nhiệt",
        formula="CaCO₃ → CaO + CO₂",
        description="Quá trình nung đá vôi (calcium carbonate) sinh ra vôi sống (calcium oxide) và giải phóng khí carbon dioxide.",
        common_pitfalls=["Quên khối lượng khí CO₂ thoát ra khi áp dụng bảo toàn khối lượng", "Nhầm phản ứng phân hủy với sự nóng chảy"]
    ),
    "nong_do_phan_tram": CoreConcept(
        name="Nồng độ phần trăm dung dịch (C%)",
        formula="C% = (m_ct / m_dd) * 100%",
        description="Cho biết số gam chất tan có trong 100 gam dung dịch. Khối lượng dung dịch bằng khối lượng chất tan cộng khối lượng dung môi.",
        common_pitfalls=["Lấy khối lượng chất tan chia cho khối lượng nước (dung môi) thay vì khối lượng dung dịch", "Quên nhân với 100%"]
    ),

    # =========================================================================
    # MẠCH 3: CƠ THỂ SỐNG / MÔI TRƯỜNG
    # =========================================================================
    "quang_hop": CoreConcept(
        name="Quang hợp ở thực vật",
        formula="6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂",
        description="Quá trình lục lạp hấp thụ năng lượng ánh sáng mặt trời để tổng hợp chất hữu cơ (glucose) và giải phóng khí oxygen.",
        common_pitfalls=["Nhầm khí thải ra của quang hợp là CO₂ thay vì O₂", "Quên vai trò bắt buộc của ánh sáng và diệp lục"]
    ),
    "ho_hap_te_bao": CoreConcept(
        name="Hô hấp tế bào",
        formula="Chất hữu cơ + O₂ → CO₂ + H₂O + Năng lượng (ATP)",
        description="Quá trình phân giải chất hữu cơ giải phóng năng lượng cung cấp cho các hoạt động sống của tế bào.",
        common_pitfalls=["Nghĩ rằng thực vật chỉ quang hợp mà không hô hấp", "Nhầm hô hấp tế bào với hô hấp ngoài (hít thở)"]
    ),
    "trao_doi_chat": CoreConcept(
        name="Trao đổi chất và Chuyển hóa năng lượng",
        formula="Đồng hóa ↔ Dị hóa",
        description="Tập hợp các biến đổi hóa học giúp sinh vật tiếp nhận chất từ môi trường và thải chất cặn bã ra ngoài.",
        common_pitfalls=["Tách rời trao đổi chất và chuyển hóa năng lượng"]
    ),
    "thoat_hoi_nuoc": CoreConcept(
        name="Thoát hơi nước qua khí khổng",
        formula="Nước bốc hơi qua bề mặt lá",
        description="Động lực đầu trên của dòng mạch gỗ, giúp vận chuyển nước và ion khoáng từ rễ lên lá, đồng thời hạ nhiệt độ bề mặt lá.",
        common_pitfalls=["Nghĩ rằng thoát hơi nước chỉ làm cây mất nước", "Quên vai trò đóng mở của tế bào hình hạt đậu ở khí khổng"]
    ),
    "cam_ung_thuc_vat": CoreConcept(
        name="Tính hướng sáng và Cảm ứng ở thực vật",
        formula="Ngọn cây uốn cong về nguồn sáng",
        description="Phản ứng sinh trưởng của thực vật đối với tác nhân kích thích ánh sáng từ một phía, giúp lá cây tiếp nhận tối đa năng lượng mặt trời.",
        common_pitfalls=["Nhầm lẫn giữa tính hướng sáng dương của thân và tính hướng trọng lực của rễ"]
    )
}


def get_all_curated_concepts() -> List[str]:
    """Trả về danh sách toàn bộ tên khái niệm chuẩn."""
    return [c.name for c in CONCEPT_MAP.values()]


def get_concept_by_key(key: str) -> CoreConcept:
    """Lấy thông tin chi tiết của khái niệm."""
    return CONCEPT_MAP.get(key, list(CONCEPT_MAP.values())[0])
