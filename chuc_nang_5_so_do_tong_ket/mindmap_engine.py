"""
Module: mindmap_engine.py
Chức năng 5: Xây dựng Sơ đồ Tư duy & Quản lý Nhật ký Khép phiên (FR-06, FR-08, FR-09)
Đặc tả dự án: Socrates Nhí v3.0

Nhiệm vụ cốt lõi:
1. FR-06: Khởi tạo Sơ đồ tư duy 3–6 nút liên kết logic (Chủ đề -> Dữ kiện -> Khái niệm -> Kiểm tra).
2. FR-06: Kiểm duyệt chống rò rỉ đáp số trên mọi nút của sơ đồ.
3. FR-08: Ghi nhật ký học tập ẩn danh ra file JSON cục bộ (không lưu PII).
4. FR-09: Xử lý dọn dẹp và xóa an toàn các tệp ảnh tạm sau khi kết thúc buổi học.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Optional

from .mindmap_model import (
    MindmapNode,
    MindmapNodeType,
    MindmapGraph,
    SessionSummary,
    StudentSummary
)
from chuc_nang_3_phan_loai_kien_thuc.concept_bank import CONCEPT_MAP


class MindmapBuilder:
    """
    Bộ xây dựng Sơ đồ tư duy học tập chuẩn hóa sư phạm.
    """
    @staticmethod
    def build_mindmap(
        topic: str = "Chuyển động và Tốc độ",
        strand_name: str = "Vật lý THCS",
        given_facts: Optional[List[str]] = None,
        core_concepts: Optional[List[str]] = None,
        target_variable: str = ""
    ) -> MindmapGraph:
        """
        Tạo sơ đồ tư duy gồm từ 3 đến 6 nút, không tiết lộ đáp số.
        """
        nodes: List[MindmapNode] = []
        connections = []

        # 1. Nút 1: Chủ đề bài toán (Topic Node)
        node_topic = MindmapNode(
            id="node_topic",
            title=topic or "Khoa học Tự nhiên 7",
            node_type=MindmapNodeType.TOPIC,
            subtitle=strand_name or "Mạch kiến thức KHTN",
            icon_name="category"
        )
        nodes.append(node_topic)

        # 2. Nút 2: Dữ kiện đã cho (Given Facts Node)
        facts = given_facts or ["s = 12 km", "t = 30 phút"]
        facts_summary = " • ".join(facts[:3])
        node_facts = MindmapNode(
            id="node_facts",
            title="Dữ kiện đề bài cho",
            node_type=MindmapNodeType.FACT,
            subtitle=facts_summary,
            icon_name="push_pin"
        )
        nodes.append(node_facts)
        connections.append(("node_topic", "node_facts"))

        # 3. Nút 3: Mục tiêu cần tìm (Target Node)
        target_label = target_variable or "Tốc độ v"
        node_target = MindmapNode(
            id="node_target",
            title="Mục tiêu cần tính",
            node_type=MindmapNodeType.FACT,
            subtitle=target_label,
            icon_name="flag"
        )
        nodes.append(node_target)
        connections.append(("node_facts", "node_target"))

        # 4. Nút 4: Khái niệm & Công thức cốt lõi (Concept Node)
        concept_names = core_concepts or ["Tốc độ chuyển động"]
        first_concept = concept_names[0] if concept_names else "Tốc độ chuyển động"
        matched_c = next((c for c in CONCEPT_MAP.values() if c.name == first_concept), None)
        formula = matched_c.formula if matched_c and matched_c.formula else "v = s / t"
        concept_desc = matched_c.description if matched_c else "Công thức tính tốc độ chuyển động."

        node_concept = MindmapNode(
            id="node_concept",
            title=first_concept,
            node_type=MindmapNodeType.CONCEPT,
            subtitle=concept_desc[:70] + "..." if len(concept_desc) > 70 else concept_desc,
            formula=formula,
            icon_name="functions"
        )
        nodes.append(node_concept)
        connections.append(("node_target", "node_concept"))

        # 5. Nút 5: Phương pháp tự kiểm tra & Tránh bẫy (Check Node)
        check_desc = "Đổi đơn vị đo lường tương thích trước khi tính toán (ví dụ: phút sang giờ)."
        if matched_c and matched_c.common_pitfalls:
            check_desc = matched_c.common_pitfalls[0]

        node_check = MindmapNode(
            id="node_check",
            title="Tự kiểm tra kết quả",
            node_type=MindmapNodeType.CHECK,
            subtitle=check_desc,
            icon_name="check_circle"
        )
        nodes.append(node_check)
        connections.append(("node_concept", "node_check"))

        # Đảm bảo tổng số nút từ 3 đến 6 nút
        graph = MindmapGraph(nodes=nodes[:5], connections=connections[:4])
        
        # Kiểm duyệt an toàn: Tuyệt đối không rò rỉ đáp số
        MindmapBuilder.sanitize_no_answer_leak(graph)

        return graph

    @staticmethod
    def sanitize_no_answer_leak(graph: MindmapGraph):
        """
        Kiểm tra và loại bỏ mọi mẫu đáp số cuối cùng xuất hiện trong sơ đồ tư duy.
        """
        leak_pattern = re.compile(r"=\s*\d+(?:[\.,]\d+)?\s*(?:km/h|m/s|N|g|kg|°C|mol)", re.IGNORECASE)
        for node in graph.nodes:
            if node.subtitle and leak_pattern.search(node.subtitle):
                node.subtitle = leak_pattern.sub("= ?", node.subtitle)
            if node.title and leak_pattern.search(node.title):
                node.title = leak_pattern.sub("= ?", node.title)


def save_anonymous_session_log(summary: SessionSummary, log_dir: Optional[str] = None) -> str:
    """
    Ghi nhật ký phiên học ẩn danh ra thư mục cục bộ theo chuẩn FR-08.
    """
    if not log_dir:
        base_dir = Path(__file__).resolve().parent.parent
        log_dir = str(base_dir / "logs_an_danh")

    os.makedirs(log_dir, exist_ok=True)
    file_path = os.path.join(log_dir, f"session_{summary.session_id}.json")

    data = summary.to_anonymous_log()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return file_path


def clean_temp_files(file_path: Optional[str]) -> bool:
    """
    Xóa an toàn tệp ảnh đề bài tạm thời sau khi kết thúc phiên theo mục 17.
    """
    if not file_path or not os.path.exists(file_path):
        return False
    try:
        # Chỉ xóa nếu là tệp tạm (không xóa ảnh mẫu chính thức)
        if "sample_images" not in file_path and "tailieu" not in file_path:
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False
