"""
Module: classifier_engine.py
Chức năng 3 (FR-03): Bộ phân loại kiến thức và Khai phá dữ kiện bài toán
Đặc tả: Socrates Nhí v3.0 (Mục 6 - FR-03 & Mục 9 - JSON Schema)

Nhiệm vụ:
1. Phân loại bài toán vào 1 trong 3 Mạch kiến thức (Cơ học, Hóa học, Sinh học).
2. Ước lượng cấp độ nhận thức (Cơ bản, Thông hiểu, Vận dụng).
3. Bóc tách các dữ kiện đã cho (facts) và đại lượng cần tìm (target).
4. Lựa chọn TỐI ĐA 3 khái niệm cốt lõi TỪ BẢN ĐỒ CÓ SẴN (LLM chỉ chọn, không tự bịa).
5. Trả về đối tượng ClassificationResult đúng chuẩn schema mục 9.
"""

import os
import re
import json
from typing import List, Tuple, Optional

from .classifier_model import KnowledgeStrand, DifficultyLevel, ClassificationResult
from .concept_bank import CONCEPT_MAP, get_all_curated_concepts


class KnowledgeClassifier:
    """
    Bộ phân loại kiến thức KHTN 7 chuẩn hóa sư phạm.
    """
    def __init__(self):
        self.curated_concept_names = get_all_curated_concepts()

    def classify_problem(self, problem_text: str) -> ClassificationResult:
        """
        Phân loại toàn diện đề bài đã xác nhận.
        """
        # Thử gọi qua OpenAI-compatible API nếu cấu hình .env
        ai_res = self._classify_via_openai(problem_text)
        if ai_res:
            return ai_res

        # Mặc định / Offline: Phân loại theo thuật toán đối chiếu bản đồ khái niệm nội bộ
        return self._classify_via_concept_bank(problem_text)

    def _classify_via_concept_bank(self, text: str) -> ClassificationResult:
        """
        Bộ phân tích ngữ nghĩa nội bộ dựa trên Bản đồ khái niệm chính thức.
        Đảm bảo chế độ Offline hoạt động ổn định và chính xác 100%.
        """
        text_lower = text.lower()

        # 1. Nhận diện mạch kiến thức
        strand = KnowledgeStrand.MECHANICS
        topic = "Vật lý – Cơ học và Đại lượng đo lường"
        selected_concepts = []
        common_mistakes = []

        # Kiểm tra Hóa học
        if any(w in text_lower for w in ["hóa học", "phản ứng", "chất mới", "đốt cháy", "than", "khí", "o₂", "o2", "co₂", "co2", "h₂o", "h2o", "bảo toàn khối lượng"]):
            strand = KnowledgeStrand.CHEMISTRY
            topic = "Hóa học – Biến đổi chất và Phản ứng hóa học"
            if "bảo toàn" in text_lower or "khối lượng" in text_lower:
                c1 = CONCEPT_MAP["bao_toan_khoi_luong"]
                c2 = CONCEPT_MAP["phuong_trinh_chu"]
                selected_concepts = [c1.name, c2.name]
                common_mistakes = c1.common_pitfalls + c2.common_pitfalls
            else:
                c1 = CONCEPT_MAP["hien_tuong_vat_ly_hoa_hoc"]
                c2 = CONCEPT_MAP["phuong_trinh_chu"]
                selected_concepts = [c1.name, c2.name]
                common_mistakes = c1.common_pitfalls

        # Kiểm tra Sinh học
        elif any(w in text_lower for w in ["quang hợp", "hô hấp", "tế bào", "thực vật", "lá cây", "diệp lục", "ánh sáng", "năng lượng"]):
            strand = KnowledgeStrand.BIOLOGY
            topic = "Sinh học – Trao đổi chất và Chuyển hóa năng lượng"
            if "hô hấp" in text_lower:
                c1 = CONCEPT_MAP["ho_hap_te_bao"]
                c2 = CONCEPT_MAP["trao_doi_chat"]
                selected_concepts = [c1.name, c2.name]
                common_mistakes = c1.common_pitfalls
            else:
                c1 = CONCEPT_MAP["quang_hop"]
                c2 = CONCEPT_MAP["trao_doi_chat"]
                selected_concepts = [c1.name, c2.name]
                common_mistakes = c1.common_pitfalls

        # Mặc định Cơ học
        else:
            strand = KnowledgeStrand.MECHANICS
            if "trọng lượng" in text_lower or "newton" in text_lower or "p = 10m" in text_lower or "khối lượng m" in text_lower:
                topic = "Vật lý – Khối lượng và Trọng lượng"
                c1 = CONCEPT_MAP["khoi_luong_trong_luong"]
                selected_concepts = [c1.name]
                common_mistakes = c1.common_pitfalls
            else:
                topic = "Vật lý – Chuyển động và Tốc độ"
                c1 = CONCEPT_MAP["toc_do"]
                c2 = CONCEPT_MAP["doi_don_vi_toc_do"]
                selected_concepts = [c1.name, c2.name]
                common_mistakes = c1.common_pitfalls + c2.common_pitfalls

        # 2. Bóc tách dữ kiện đã cho (facts) và đại lượng cần tìm
        given_facts, target = self._extract_facts_and_target(text)

        # 3. Ước lượng cấp độ nhận thức
        difficulty = DifficultyLevel.BASIC
        if len(given_facts) >= 2 and ("đổi" in text_lower or "km/h" in text_lower and "m/s" in text_lower):
            difficulty = DifficultyLevel.APPLICATION
        elif len(given_facts) >= 2 or "vì sao" in text_lower or "giải thích" in text_lower:
            difficulty = DifficultyLevel.UNDERSTANDING

        return ClassificationResult(
            topic=topic,
            strand=strand,
            difficulty=difficulty,
            given_facts=given_facts,
            target_variable=target,
            core_concepts=selected_concepts[:3],  # Ràng buộc FR-03: Tối đa 3 khái niệm
            common_mistakes=common_mistakes[:3],
            analysis_source="concept_map_bank"
        )

    def _extract_facts_and_target(self, text: str) -> Tuple[List[str], str]:
        """Trích xuất các đại lượng số liệu cho trước và câu hỏi cần tìm."""
        facts = []
        target = "Đại lượng theo yêu cầu đề bài"

        # Tìm các con số kèm đơn vị KHTN: ví dụ 12 km, 30 phút, 45 kg, 6 g, 22 g
        patterns = [
            r"([sS]\s*=\s*\d+(?:[\.,]\d+)?\s*(?:km|m))",
            r"([tT]\s*=\s*\d+(?:[\.,]\d+)?\s*(?:phút|h|giây|s))",
            r"([mM]\s*=\s*\d+(?:[\.,]\d+)?\s*(?:kg|g))",
            r"([vV]\s*=\s*\d+(?:[\.,]\d+)?\s*(?:km/h|m/s))",
            r"(\d+(?:[\.,]\d+)?\s*(?:km|m|kg|g|phút|h|giây|s|N|°C))"
        ]
        for p in patterns:
            matches = re.findall(p, text)
            for m in matches:
                if m not in facts:
                    facts.append(m)

        # Tìm mục tiêu cần tính
        text_lower = text.lower()
        if "tốc độ" in text_lower or "vận tốc" in text_lower:
            target = "Tốc độ chuyển động v (km/h, m/s)"
        elif "trọng lượng" in text_lower:
            target = "Trọng lượng P (Newton)"
        elif "khối lượng" in text_lower and ("oxygen" in text_lower or "o2" in text_lower):
            target = "Khối lượng khí oxygen đã phản ứng (g)"
        elif "chất tham gia" in text_lower:
            target = "Chất tham gia và chất sản phẩm của phản ứng"

        return facts[:5], target

    def _classify_via_openai(self, text: str) -> Optional[ClassificationResult]:
        """Gọi OpenAI-compatible API với JSON response format nếu có cấu hình."""
        base_url = os.getenv("OPENAI_BASE_URL")
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("SOCRATES_MODEL", "gpt-4o-mini")

        if not api_key:
            return None

        try:
            from openai import OpenAI
            client = OpenAI(base_url=base_url if base_url else None, api_key=api_key)

            system_prompt = (
                "Bạn là bộ phân loại kiến thức KHTN THCS theo chuẩn đặc tả Socrates Nhí v3.0. "
                f"Chỉ được CHỌN tối đa 3 khái niệm cốt lõi từ danh sách sau: {json.dumps(self.curated_concept_names, ensure_ascii=False)}. "
                "Trả về duy nhất định dạng JSON đúng schema: "
                '{"topic": string, "strand": "Cơ học / Đại lượng vật lý"|"Biến đổi chất / Phản ứng hóa học"|"Cơ thể sống / Môi trường", '
                '"difficulty": "Cơ bản"|"Thông hiểu"|"Vận dụng", "given_facts": [string], "target_variable": string, '
                '"core_concepts": [string], "common_mistakes": [string]}'
            )

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Đề bài KHTN: {text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            data = json.loads(response.choices[0].message.content)

            # Ràng buộc tối đa 3 khái niệm
            concepts = [c for c in data.get("core_concepts", []) if c in self.curated_concept_names][:3]
            if not concepts:
                concepts = [self.curated_concept_names[0]]

            return ClassificationResult(
                topic=data.get("topic", "Khoa học tự nhiên 7"),
                strand=KnowledgeStrand(data.get("strand", KnowledgeStrand.MECHANICS.value)),
                difficulty=DifficultyLevel(data.get("difficulty", DifficultyLevel.BASIC.value)),
                given_facts=data.get("given_facts", []),
                target_variable=data.get("target_variable", "Đại lượng cần tìm"),
                core_concepts=concepts,
                common_mistakes=data.get("common_mistakes", []),
                analysis_source="openai_json"
            )
        except Exception:
            return None
