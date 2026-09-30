"""
Module: notebook_manager.py
Chức năng: Quản lý Sổ tay Tự học (Personal Learning Notebook) cho Socrates Nhí
Đặc tả dự án: Socrates Nhí v3.0

Lưu trữ và quản lý các bài học đã hoàn thành:
- Vấn đề / Câu hỏi nghiên cứu
- Khái niệm hoàn chỉnh chuẩn SGK KHTN 7
- Kiến thức cốt lõi cần nhớ (Key Takeaways)
- Lời tự đúc kết của học sinh (3 dòng)
- Sơ đồ tư duy nhánh của bài học
- Đánh giá sao & Cảm nhận
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from chuc_nang_3_phan_loai_kien_thuc.concept_bank import CONCEPT_MAP

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_DIR = WORKSPACE_ROOT / "so_tay_hoc_tap"
NOTEBOOK_FILE = NOTEBOOK_DIR / "so_tay_tu_hoc.json"


import unicodedata


def strip_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt để so khớp từ khóa cả có dấu và không dấu."""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text.lower()


def get_curated_concept_details(
    problem_text: str = "",
    topic: str = "",
    core_concepts: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Trích xuất Khái niệm Hoàn chỉnh chuẩn SGK và Kiến thức Cần nhớ dựa trên chủ đề bài toán.
    Đảm bảo chính xác 100% theo chuẩn SGK KHTN 7, hỗ trợ cả tiếng Việt có dấu và không dấu.
    """
    comb_text = f"{topic} {problem_text} {' '.join(core_concepts or [])}".lower()
    comb_unaccented = strip_accents(comb_text)

    # 1. Quang học: Phản xạ ánh sáng trên gương phẳng
    optics_kws = [
        "gương", "gương phẳng", "phản xạ", "ánh sáng", "tia tới", "tia phản xạ", "pháp tuyến",
        "guong", "guong phang", "phan xa", "anh sang", "tia toi", "tia phan xa", "phap tuyen", "quang hoc"
    ]
    if any(w in comb_text or w in comb_unaccented for w in optics_kws):
        return {
            "concept_name": "Định luật phản xạ ánh sáng trên gương phẳng",
            "full_concept": (
                "Định luật phản xạ ánh sáng:\n"
                "1. Tia sáng phản xạ nằm trong mặt phẳng tới (mặt phẳng chứa tia tới và đường pháp tuyến của gương tại điểm tới).\n"
                "2. Góc phản xạ luôn bằng góc tới (kí hiệu: i' = i).\n"
                "Khi chùm sáng gặp mặt gương phẳng nhẵn bóng, ánh sáng không đi xuyên qua mà bị hắt ngược trở lại môi trường cũ."
            ),
            "key_takeaways": [
                "Tia sáng chiếu tới mặt gương gọi là tia tới; tia bị hắt ngược lại gọi là tia phản xạ.",
                "Đường pháp tuyến (vuông góc với mặt gương tại điểm tới) là đường chuẩn để đo góc tới (i) và góc phản xạ (i').",
                "Nếu chiếu tia sáng vuông góc với mặt gương (i = 0°), tia phản xạ sẽ bật thẳng ngược trở lại theo phương cũ (i' = 0°).",
                "Ảnh tạo bởi gương phẳng là ảnh ảo, không hứng được trên màn chắn và có độ lớn bằng đúng vật."
            ],
            "formula": "i' = i (Góc phản xạ = Góc tới)",
            "pitfall": "Nhầm lẫn góc tới là góc hợp bởi tia tới với mặt gương (chuẩn phải là góc giữa tia tới và pháp tuyến).",
            "suggested_rule": "Khi ánh sáng gặp gương phẳng: Ánh sáng bị phản xạ hắt trở lại, góc phản xạ bằng góc tới (i' = i).",
            "suggested_pitfall": "Nhầm góc tới là góc với mặt gương thay vì góc với đường pháp tuyến vuông góc.",
            "suggested_next_step": "Dựng đường pháp tuyến vuông góc tại điểm tới để xác định chính xác góc tới và vẽ tia phản xạ."
        }

    # 2. Sinh học: Quang hợp ở thực vật
    bio_kws = [
        "quang hợp", "diệp lục", "lá cây", "glucose", "lục lạp", "thực vật",
        "quang hop", "diep luc", "la cay", "glucose", "luc lap", "thuc vat", "sinh hoc"
    ]
    if any(w in comb_text or w in comb_unaccented for w in bio_kws):
        return {
            "concept_name": "Quang hợp ở thực vật",
            "full_concept": (
                "Quang hợp là quá trình lá cây sử dụng chất diệp lục trong lục lạp để hấp thụ năng lượng ánh sáng mặt trời, "
                "biến đổi nước (H₂O) từ rễ và khí carbon dioxide (CO₂) từ không khí thành chất hữu cơ (glucose/tinh bột) và giải phóng khí oxygen (O₂)."
            ),
            "key_takeaways": [
                "Phương trình chữ: Nước + Carbon dioxide + Năng lượng ánh sáng → Glucose + Oxygen.",
                "Diệp lục đóng vai trò chất xúc tác hấp thụ năng lượng ánh sáng mặt trời.",
                "Quang hợp cung cấp chất hữu cơ và khí O₂ cho sự sống, đồng thời hấp thụ CO₂ giúp điều hòa khí hậu Trái Đất."
            ],
            "formula": "Nước + CO₂ + Ánh sáng → Chất hữu cơ + O₂",
            "pitfall": "Nhầm lẫn khí thải ra của quang hợp là CO₂ thay vì O₂, hoặc nghĩ rằng cây chỉ quang hợp mà không hô hấp.",
            "suggested_rule": "Cây xanh quang hợp nhờ ánh sáng và diệp lục, biến nước và CO₂ thành chất hữu cơ và nhả khí O₂.",
            "suggested_pitfall": "Quên rằng ban đêm không có ánh sáng cây không quang hợp mà chỉ hô hấp hút O₂ và thải CO₂.",
            "suggested_next_step": "Xác định rõ các yếu tố nguyên liệu đầu vào và sản phẩm đầu ra của quá trình quang hợp."
        }

    # 3. Hóa học: Định luật bảo toàn khối lượng
    chem_kws = [
        "bảo toàn", "phản ứng", "sản phẩm", "tham gia", "phương trình", "hóa học",
        "bao toan", "phan ung", "san pham", "tham gia", "phuong trinh", "hoa hoc"
    ]
    if any(w in comb_text or w in comb_unaccented for w in chem_kws):
        return {
            "concept_name": "Định luật bảo toàn khối lượng trong phản ứng hóa học",
            "full_concept": (
                "Định luật bảo toàn khối lượng: Trong một phản ứng hóa học, tổng khối lượng của các chất tham gia phản ứng "
                "bằng tổng khối lượng của các sản phẩm tạo thành (m_tham_gia = m_san_pham)."
            ),
            "key_takeaways": [
                "Bản chất: Trong phản ứng hóa học chỉ có liên kết giữa các nguyên tử thay đổi, số lượng nguyên tử mỗi nguyên tố được bảo toàn.",
                "Biểu thức khối lượng: m_A + m_B = m_C + m_D.",
                "Khi tính toán cần lưu ý cả khối lượng của chất khí bay lên hoặc chất kết tủa lắng xuống."
            ],
            "formula": "m_tham_gia = m_san_pham",
            "pitfall": "Bỏ quên khối lượng của chất khí bay ra (O₂, CO₂) dẫn đến cảm giác khối lượng bị hụt đi.",
            "suggested_rule": "Tổng khối lượng các chất trước phản ứng luôn bằng tổng khối lượng các chất sau phản ứng.",
            "suggested_pitfall": "Quên tính khối lượng khí thoát ra môi trường khi bình phản ứng hở.",
            "suggested_next_step": "Viết phương trình chữ của phản ứng rồi lập biểu thức khối lượng tương ứng."
        }

    # 4. Cơ học: Tốc độ chuyển động
    speed_kws = [
        "tốc độ", "quãng đường", "vận tốc", "xe đạp", "chuyển động", "km/h", "m/s",
        "toc do", "quang duong", "van toc", "xe dap", "chuyen dong", "co hoc"
    ]
    if any(w in comb_text or w in comb_unaccented for w in speed_kws):
        return {
            "concept_name": "Tốc độ chuyển động",
            "full_concept": (
                "Tốc độ chuyển động đặc trưng cho mức độ nhanh hay chậm của chuyển động, được xác định bằng quãng đường "
                "vật đi được trong một đơn vị thời gian: v = s / t."
            ),
            "key_takeaways": [
                "Công thức tính: v = s / t. Từ đó suy ra: s = v * t và t = s / v.",
                "Đơn vị hợp pháp: km/h hoặc m/s.",
                "Quy đổi chuẩn: 1 m/s = 3.6 km/h (đổi km/h sang m/s: chia 3.6; đổi m/s sang km/h: nhân 3.6)."
            ],
            "formula": "v = s / t (1 m/s = 3.6 km/h)",
            "pitfall": "Quên đổi đơn vị thời gian (phút sang giờ hoặc giây) trước khi thực hiện phép tính chia.",
            "suggested_rule": "Tốc độ v = s / t; cần quy đổi quãng đường và thời gian về cùng hệ đơn vị tương thích.",
            "suggested_pitfall": "Lấy quãng đường nhân thời gian thay vì chia, hoặc quên đổi phút sang giờ.",
            "suggested_next_step": "Đổi các dữ kiện về chuẩn km và giờ, sau đó thay vào công thức v = s / t."
        }

    # 5. Mặc định an toàn: Tuyệt đối không gán ép công thức v = s / t
    return {
        "concept_name": topic or "Khoa học Tự nhiên 7",
        "full_concept": "Quy luật và nguyên lý cốt lõi của bài học theo chương trình KHTN 7.",
        "key_takeaways": [
            "Nắm vững định nghĩa và bản chất khoa học của hiện tượng.",
            "Xác định rõ mối liên hệ giữa các dữ kiện đã cho và đại lượng cần tìm.",
            "Luôn kiểm tra tính hợp lý của đơn vị và kết quả."
        ],
        "formula": "",
        "pitfall": "Chú ý đọc kỹ các điều kiện ràng buộc của đề bài.",
        "suggested_rule": f"Vận dụng quy tắc và định luật: {topic}",
        "suggested_pitfall": "Tránh nhầm lẫn giữa các dữ kiện và đại lượng.",
        "suggested_next_step": "Đối chiếu kết quả với thực tiễn đời sống."
    }


def load_notebook_entries() -> List[Dict[str, Any]]:
    """Tải toàn bộ các trang bài học trong Sổ tay Tự học từ tệp JSON."""
    if not NOTEBOOK_FILE.exists():
        return []
    try:
        with open(NOTEBOOK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                # Sắp xếp bài mới nhất lên đầu
                return sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)
            return []
    except Exception as e:
        print(f"[NotebookManager] Lỗi đọc sổ tay: {e}")
        return []


def save_notebook_entry(entry: Dict[str, Any]) -> bool:
    """Lưu một trang bài học mới vào Sổ tay Tự học."""
    try:
        NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
        entries = load_notebook_entries()

        # Gán mã bài học và thời gian nếu chưa có
        if "id" not in entry or not entry["id"]:
            entry["id"] = f"nb_{uuid.uuid4().hex[:8]}"
        if "created_at" not in entry or not entry["created_at"]:
            entry["created_at"] = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Cập nhật nếu đã có cùng id, hoặc thêm mới vào đầu
        existing_idx = next((i for i, x in enumerate(entries) if x.get("id") == entry["id"]), None)
        if existing_idx is not None:
            entries[existing_idx] = entry
        else:
            entries.insert(0, entry)

        with open(NOTEBOOK_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"[NotebookManager] Lỗi lưu sổ tay: {e}")
        return False


def delete_notebook_entry(entry_id: str) -> bool:
    """Xóa một bài học khỏi Sổ tay Tự học."""
    try:
        entries = load_notebook_entries()
        new_entries = [x for x in entries if x.get("id") != entry_id]
        with open(NOTEBOOK_FILE, "w", encoding="utf-8") as f:
            json.dump(new_entries, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[NotebookManager] Lỗi xóa bài học: {e}")
        return False
