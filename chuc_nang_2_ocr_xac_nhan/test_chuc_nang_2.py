"""
Unit Tests: test_chuc_nang_2.py
Kiểm thử toàn diện Chức năng 2 (FR-02: Trích xuất OCR & Xác nhận đề bài)
Đặc tả dự án: Socrates Nhí v3.0

Kiểm tra các tiêu chí chấp nhận:
1. Chuẩn hóa công thức Hóa học (chỉ số dưới: H₂O, CO₂, C₆H₁₂O₆, Fe₂O₃).
2. Chuẩn hóa lũy thừa Vật lý (v², cm³, m², °C).
3. Chuẩn hóa quy cách khoảng trắng đơn vị đo (15 km/h, 500 g, 12 N).
4. Nhận diện và trích xuất đúng danh mục công thức và đơn vị.
5. Đánh giá độ nét ảnh: phân biệt chính xác ảnh rõ nét vs ảnh mờ.
6. Tiêu chí FR-02: Từ chối ảnh mờ, yêu cầu chụp lại, không đoán mò.
7. Đóng gói ConfirmedProblem sau khi học sinh kiểm tra / sửa lỗi.
"""

import unittest
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw

from chuc_nang_2_ocr_xac_nhan.formula_normalizer import (
    normalize_chemical_formulas,
    normalize_physics_powers,
    normalize_units_spacing,
    normalize_khtn_text,
    extract_formulas_and_units
)
from chuc_nang_2_ocr_xac_nhan.ocr_engine import (
    calculate_image_sharpness,
    calculate_sharpness_percentage,
    is_image_too_blurry,
    process_image_ocr
)
from chuc_nang_2_ocr_xac_nhan.ocr_model import OcrResult, ConfirmedProblem
from chuc_nang_2_ocr_xac_nhan.sample_images import SAMPLE_PATHS


class TestChucNang2(unittest.TestCase):

    # --- 1. KIỂM THỬ CHUẨN HÓA CÔNG THỨC HÓA HỌC ---
    def test_normalize_chemistry(self):
        """Kiểm tra chỉ số dưới cho các chất hóa học KHTN 7."""
        raw = "Quang hop: 6CO2 + 6H2O -> C6H12O6 + 6O2"
        normalized = normalize_chemical_formulas(raw)
        self.assertIn("CO₂", normalized)
        self.assertIn("H₂O", normalized)
        self.assertIn("C₆H₁₂O₆", normalized)
        self.assertIn("O₂", normalized)
        self.assertIn("→", normalized)

    def test_normalize_chemistry_complex(self):
        """Kiểm tra các muối và oxit phức tạp."""
        raw = "Nhiet phan: Fe2O3 va CaCO3 -> CaO + CO2"
        normalized = normalize_chemical_formulas(raw)
        self.assertIn("Fe₂O₃", normalized)
        self.assertIn("CaCO₃", normalized)

    # --- 2. KIỂM THỬ CHUẨN HÓA LŨY THỪA VẬT LÝ ---
    def test_normalize_physics_powers(self):
        """Kiểm tra lũy thừa v^2, cm^3, m^2."""
        raw = "Vat ly: van toc v^2 = 25 (m/s)^2, the tich V = 100cm3, dien tich S = 2m2"
        normalized = normalize_physics_powers(raw)
        self.assertIn("v²", normalized)
        self.assertIn("cm³", normalized)
        self.assertIn("m²", normalized)

    def test_normalize_celsius(self):
        """Kiểm tra đơn vị nhiệt độ °C."""
        raw = "Nhiet do moi truong la 37 oC hoac 25 do C"
        normalized = normalize_physics_powers(raw)
        self.assertIn("37 °C", normalized)

    # --- 3. KIỂM THỬ KHOẢNG TRẮNG ĐƠN VỊ ĐO ---
    def test_normalize_units_spacing(self):
        """Đơn vị luôn đi kèm số, cách 1 khoảng trắng (500 g, 12 N)."""
        raw = "m = 500g, F = 12N, v = 15km/h, t = 30s"
        normalized = normalize_units_spacing(raw)
        self.assertIn("500 g", normalized)
        self.assertIn("12 N", normalized)
        self.assertIn("15 km/h", normalized)
        self.assertIn("30 s", normalized)

    # --- 4. KIỂM THỬ TRÍCH XUẤT CÔNG THỨC & ĐƠN VỊ ---
    def test_extract_formulas_and_units(self):
        """Trích xuất tự động danh sách công thức và đơn vị."""
        text = "Vận tốc v = s/t với s = 12 km và t = 30 phút. Nước H₂O và CO₂."
        formulas, units = extract_formulas_and_units(text)
        self.assertTrue(any("v = s/t" in f or "v" in f for f in formulas))
        self.assertIn("km", units)
        self.assertIn("phút", units)

    # --- 5. KIỂM THỬ ĐÁNH GIÁ ĐỘ NÉT ẢNH ---
    def test_sharp_image_detection(self):
        """Ảnh rõ nét phải có phương sai cao và không bị đánh dấu là mờ."""
        sharp_path = SAMPLE_PATHS["co_hoc"]
        self.assertTrue(Path(sharp_path).exists())
        self.assertFalse(is_image_too_blurry(sharp_path))
        score = calculate_sharpness_percentage(calculate_image_sharpness(sharp_path))
        self.assertGreaterEqual(score, 70)

    def test_blurry_image_detection(self):
        """Ảnh mờ phải bị phát hiện (is_blurry = True)."""
        blurry_path = SAMPLE_PATHS["blurry"]
        self.assertTrue(Path(blurry_path).exists())
        self.assertTrue(is_image_too_blurry(blurry_path))

    # --- 6. KIỂM THỬ NGUYÊN TẮC FR-02: TỪ CHỐI ẢNH MỜ, KHÔNG ĐOÁN MÒ ---
    def test_blurry_image_rejection(self):
        """Tiêu chí chấp nhận FR-02: Đề quá mờ -> yêu cầu ảnh rõ hơn, không đoán mò."""
        blurry_path = SAMPLE_PATHS["blurry"]
        result = process_image_ocr(blurry_path)
        self.assertTrue(result.is_blurry)
        self.assertFalse(result.is_usable)
        self.assertIsNotNone(result.error_message)
        self.assertIn("quá mờ", result.error_message)
        self.assertIn("không thể đoán mò", result.error_message)

    def test_clear_image_acceptance(self):
        """Ảnh rõ nét được trích xuất thành công và chuẩn hóa công thức."""
        sharp_path = SAMPLE_PATHS["co_hoc"]
        result = process_image_ocr(sharp_path)
        self.assertFalse(result.is_blurry)
        self.assertTrue(result.is_usable)
        self.assertIsNone(result.error_message)
        self.assertIn("km/h", result.formatted_text)

    # --- 7. KIỂM THỬ ĐÓNG GÓI CONFIRMED PROBLEM ---
    def test_confirmed_problem_packaging(self):
        """Kiểm tra đối tượng ConfirmedProblem sau khi xác nhận."""
        original = "v = 15km/h, t = 2h"
        edited = "v = 15 km/h, t = 2 h. Tinh quang duong s."
        confirmed = ConfirmedProblem(
            original_text=original,
            confirmed_text=edited,
            was_edited=True,
            formulas=["v = s/t"],
            units=["km/h", "h"],
            source_type="image"
        )
        self.assertTrue(confirmed.was_edited)
        self.assertEqual(confirmed.confirmed_text, edited)
        data = confirmed.to_dict()
        self.assertEqual(data["was_edited"], True)
        self.assertIn("confirmed_at", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
