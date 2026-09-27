"""
Unit Tests: test_chuc_nang_3.py
Kiểm thử toàn diện Chức năng 3 (FR-03: Phân loại kiến thức bài toán & Bản đồ khái niệm)
Đặc tả dự án: Socrates Nhí v3.0

Kiểm tra các tiêu chí chấp nhận:
1. Phân loại chính xác 3 Mạch kiến thức: Cơ học, Hóa học, Sinh học.
2. Tiêu chí FR-03: TỐI ĐA 3 khái niệm cốt lõi (len(core_concepts) <= 3).
3. Tiêu chí FR-03: Khái niệm cốt lõi bắt buộc lấy từ Bản đồ đội soạn (không tự bịa).
4. Khai phá và bóc tách các dữ kiện đã cho (facts: s, t, m, kg, km/h).
5. Ước lượng cấp độ nhận thức (Cơ bản, Thông hiểu, Vận dụng).
6. Tuân thủ định dạng JSON Schema mục 9.
"""

import unittest
from chuc_nang_3_phan_loai_kien_thuc.classifier_model import (
    KnowledgeStrand,
    DifficultyLevel,
    ClassificationResult
)
from chuc_nang_3_phan_loai_kien_thuc.classifier_engine import KnowledgeClassifier
from chuc_nang_3_phan_loai_kien_thuc.concept_bank import get_all_curated_concepts


class TestChucNang3(unittest.TestCase):

    def setUp(self):
        self.classifier = KnowledgeClassifier()
        self.valid_concept_names = get_all_curated_concepts()

    # --- 1. KIỂM THỬ PHÂN LOẠI 3 MẠCH KIẾN THỨC ---
    def test_classify_mechanics(self):
        """Phân loại bài toán chuyển động vào mạch Cơ học."""
        text = "Một xe đạp đi quãng đường s = 15 km trong thời gian t = 45 phút. Tính vận tốc."
        result = self.classifier.classify_problem(text)
        self.assertEqual(result.strand, KnowledgeStrand.MECHANICS)
        self.assertIn("Vật lý", result.topic)

    def test_classify_chemistry(self):
        """Phân loại bài toán phản ứng vào mạch Hóa học."""
        text = "Đốt than C trong bình kín chứa khí oxygen O₂ thu được khí CO₂. Viết phương trình chữ."
        result = self.classifier.classify_problem(text)
        self.assertEqual(result.strand, KnowledgeStrand.CHEMISTRY)
        self.assertIn("Hóa học", result.topic)

    def test_classify_biology(self):
        """Phân loại bài toán quang hợp vào mạch Sinh học."""
        text = "Giải thích quá trình quang hợp ở lá cây khi có ánh sáng mặt trời và diệp lục."
        result = self.classifier.classify_problem(text)
        self.assertEqual(result.strand, KnowledgeStrand.BIOLOGY)
        self.assertIn("Sinh học", result.topic)

    # --- 2. KIỂM THỬ RÀNG BUỘC SƯ PHẠM FR-03 ---
    def test_max_three_core_concepts(self):
        """Tiêu chí FR-03: AI chỉ được trả TỐI ĐA 3 khái niệm cốt lõi."""
        text = "Một người đi bộ với tốc độ v = 5 km/h trong thời gian 2 giờ. Tính quãng đường s."
        result = self.classifier.classify_problem(text)
        self.assertLessEqual(len(result.core_concepts), 3, "Ràng buộc FR-03: Không quá 3 khái niệm cốt lõi")
        self.assertGreaterEqual(len(result.core_concepts), 1)

    def test_concepts_chosen_from_curated_map_only(self):
        """Tiêu chí FR-03: Khái niệm phải lấy từ bản đồ đội soạn, không tự bịa."""
        text = "Thùng hàng có khối lượng m = 45 kg. Tính trọng lượng P = 10m."
        result = self.classifier.classify_problem(text)
        for concept in result.core_concepts:
            self.assertIn(concept, self.valid_concept_names, f"Khái niệm '{concept}' phải thuộc bản đồ chuẩn")

    # --- 3. KIỂM THỬ BÓC TÁCH DỮ KIỆN ĐỀ BÀI (FACTS) ---
    def test_facts_extraction(self):
        """Bóc tách chính xác các con số kèm đơn vị đo lường trong đề bài."""
        text = "Xe chuyển động trên quãng đường s = 12 km trong t = 30 phút."
        result = self.classifier.classify_problem(text)
        self.assertTrue(any("12" in f and "km" in f for f in result.given_facts))
        self.assertTrue(any("30" in f and "phút" in f for f in result.given_facts))

    # --- 4. KIỂM THỬ CẤP ĐỘ NHẬN THỨC VÀ JSON SCHEMA ---
    def test_difficulty_estimation(self):
        """Ước lượng cấp độ bài toán phù hợp."""
        text = "Tính tốc độ khi s = 12 km, t = 30 phút và đổi ra đơn vị m/s."
        result = self.classifier.classify_problem(text)
        self.assertIn(result.difficulty, [DifficultyLevel.UNDERSTANDING, DifficultyLevel.APPLICATION])

    def test_json_schema_compliance(self):
        """Kiểm tra tuân thủ cấu trúc dữ liệu JSON Schema mục 9."""
        text = "Cho m = 45 kg. Tìm P."
        result = self.classifier.classify_problem(text)
        self.assertTrue(result.is_valid_schema)
        data = result.to_dict()
        self.assertIn("topic", data)
        self.assertIn("strand", data)
        self.assertIn("difficulty", data)
        self.assertIn("given_facts", data)
        self.assertIn("core_concepts", data)
        self.assertIn("common_mistakes", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
