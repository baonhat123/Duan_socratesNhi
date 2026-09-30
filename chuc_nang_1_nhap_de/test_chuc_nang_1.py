"""
Unit Tests: test_chuc_nang_1.py
Kiểm thử toàn diện Chức năng 1 (FR-01: Nhập đề bài)
Đặc tả dự án: Socrates Nhí v3.0

Kiểm tra các tiêu chí chấp nhận:
1. Tiếp nhận văn bản đề bài hợp lệ.
2. Từ chối văn bản rỗng hoặc quá ngắn.
3. Cảnh báo bảo mật thông tin cá nhân (PII).
4. Tiếp nhận ảnh JPG/PNG hợp lệ <= 5MB.
5. Từ chối tệp quá lớn (> 5MB).
6. Từ chối tệp sai định dạng (PDF, TXT, DOCX).
7. Từ chối tệp ảnh bị lỗi cấu trúc.
8. Nguyên tắc không gửi sang AI khi chưa nhấn Xác nhận (is_confirmed = False).
"""

import os
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from chuc_nang_1_nhap_de.input_model import ProblemInput, InputType
from chuc_nang_1_nhap_de.validator import (
    process_text_input,
    process_image_input,
    validate_file_size,
    validate_file_format,
    check_pii_and_safety,
    MAX_FILE_SIZE_BYTES
)
from chuc_nang_1_nhap_de.sample_bank import get_all_samples, get_sample_by_id


class TestChucNang1(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    # --- 1. KIỂM THỬ ĐẦU VÀO VĂN BẢN ---
    def test_text_input_valid(self):
        """Kiểm tra nhập văn bản đề bài KHTN hợp lệ."""
        content = "Một vật rơi tự do từ độ cao h = 20m. Tính thời gian rơi chạm đất."
        result = process_text_input(content)
        self.assertEqual(result.input_type, InputType.TEXT)
        self.assertEqual(result.text_content, content)
        self.assertIsNone(result.validation_error)
        self.assertTrue(result.is_valid)
        self.assertFalse(result.is_confirmed, "Quy tắc FR-01: Chưa xác nhận thì is_confirmed phải là False")

    def test_text_input_empty(self):
        """Kiểm tra từ chối khi đề bài rỗng."""
        result = process_text_input("   ")
        self.assertIsNotNone(result.validation_error)
        self.assertIn("không được để trống", result.validation_error)
        self.assertFalse(result.is_valid)

    def test_text_input_too_short(self):
        """Kiểm tra từ chối khi đề bài quá ngắn."""
        result = process_text_input("abc")
        self.assertIsNotNone(result.validation_error)
        self.assertIn("quá ngắn", result.validation_error)
        self.assertFalse(result.is_valid)

    def test_text_input_pii_warning(self):
        """Kiểm tra cảnh báo thông tin cá nhân (PII) theo mục 17.1."""
        text_with_phone = "Đề bài của em: Một vật chuyển động, liên hệ số 0912345678 lớp 7A"
        warnings = check_pii_and_safety(text_with_phone)
        self.assertGreaterEqual(len(warnings), 1)
        self.assertTrue(any("số điện thoại" in w for w in warnings))

    # --- 2. KIỂM THỬ ĐẦU VÀO ẢNH HỢP LỆ ---
    def test_image_input_valid_png(self):
        """Kiểm tra tải ảnh PNG hợp lệ <= 5MB."""
        img_path = self.temp_path / "de_bai.png"
        img = Image.new("RGB", (300, 200), color="white")
        img.save(img_path, format="PNG")

        result = process_image_input(str(img_path))
        self.assertEqual(result.input_type, InputType.IMAGE)
        self.assertIsNone(result.validation_error)
        self.assertTrue(result.is_valid)
        self.assertFalse(result.is_confirmed, "Quy tắc FR-01: Chưa bấm xác nhận thì is_confirmed = False")
        self.assertIsNotNone(result.file_path)
        self.assertTrue(os.path.exists(result.file_path), "File tạm an toàn phải tồn tại trên đĩa")

    def test_image_input_valid_jpg(self):
        """Kiểm tra tải ảnh JPG hợp lệ <= 5MB."""
        img_path = self.temp_path / "de_bai.jpg"
        img = Image.new("RGB", (200, 200), color="blue")
        img.save(img_path, format="JPEG")

        result = process_image_input(str(img_path))
        self.assertEqual(result.input_type, InputType.IMAGE)
        self.assertIsNone(result.validation_error)
        self.assertTrue(result.is_valid)

    def test_image_input_valid_webp(self):
        """Kiểm tra tải ảnh WebP hợp lệ <= 5MB."""
        img_path = self.temp_path / "de_bai.webp"
        img = Image.new("RGB", (200, 200), color="green")
        img.save(img_path, format="WEBP")

        result = process_image_input(str(img_path))
        self.assertEqual(result.input_type, InputType.IMAGE)
        self.assertIsNone(result.validation_error)
        self.assertTrue(result.is_valid)

    def test_clipboard_image_flow(self):
        """Kiểm thử luồng dán ảnh chụp màn hình từ bộ nhớ tạm (Clipboard / Win+Shift+S)."""
        clip_path = self.temp_path / "clip_screenshot.png"
        img = Image.new("RGBA", (400, 300), color=(255, 255, 255, 255))
        img.save(clip_path, format="PNG")

        result = process_image_input(str(clip_path))
        self.assertEqual(result.input_type, InputType.IMAGE)
        self.assertIsNone(result.validation_error)
        self.assertTrue(result.is_valid)
        self.assertTrue(os.path.exists(result.file_path))

    # --- 3. KIỂM THỬ GIỚI HẠN DUNG LƯỢNG TỆP (> 5MB) ---
    def test_image_size_exceeded(self):
        """Tiêu chí chấp nhận FR-01: Báo lỗi rõ khi tệp quá lớn (> 5 MB)."""
        oversized_path = self.temp_path / "huge_photo.jpg"
        # Tạo file vượt quá 5MB: 5.2 MB
        with open(oversized_path, "wb") as f:
            f.seek(int(5.2 * 1024 * 1024))
            f.write(b"\0")

        result = process_image_input(str(oversized_path))
        self.assertIsNotNone(result.validation_error)
        self.assertIn("quá lớn", result.validation_error)
        self.assertIn("5 MB", result.validation_error)
        self.assertFalse(result.is_valid)

    # --- 4. KIỂM THỬ ĐỊNH DẠNG TỆP KHÔNG HỢP LỆ ---
    def test_invalid_file_extension(self):
        """Tiêu chí chấp nhận FR-01: Báo lỗi rõ khi tệp không phải ảnh JPG/PNG (ví dụ .pdf)."""
        pdf_path = self.temp_path / "tai_lieu.pdf"
        pdf_path.write_text("Day la file tai lieu PDF gia dinh", encoding="utf-8")

        result = process_image_input(str(pdf_path))
        self.assertIsNotNone(result.validation_error)
        self.assertIn("không được hỗ trợ", result.validation_error)
        self.assertFalse(result.is_valid)

    def test_corrupted_image_file(self):
        """Kiểm tra tệp có đuôi .png nhưng nội dung hỏng/giả mạo."""
        corrupted_path = self.temp_path / "fake_image.png"
        corrupted_path.write_bytes(b"Day khong phai anh hop le!")

        result = process_image_input(str(corrupted_path))
        self.assertIsNotNone(result.validation_error)
        self.assertIn("bị lỗi hoặc không thể mở", result.validation_error)
        self.assertFalse(result.is_valid)

    # --- 5. KIỂM THỬ BÀI TOÁN MẪU KHTN 7 ---
    def test_sample_bank_loading(self):
        """Kiểm tra danh mục đề mẫu KHTN 7 đủ 3 mạch kiến thức và 12 bài chuẩn SGK."""
        samples = get_all_samples()
        self.assertEqual(len(samples), 12, "Ngân hàng đề mẫu KHTN 7 phải có đúng 12 bài chuẩn SGK theo mục 2.2")
        strands = {s["strand"] for s in samples}
        self.assertIn("Cơ học / Đại lượng vật lý", strands)
        self.assertIn("Biến đổi chất / Phản ứng hóa học", strands)
        self.assertIn("Cơ thể sống / Môi trường", strands)

        first_sample = get_sample_by_id(samples[0]["id"])
        self.assertIsNotNone(first_sample)
        self.assertTrue(len(first_sample["content"]) > 10)

    def test_process_sample_input_valid(self):
        """Kiểm tra tiếp nhận và đóng gói đề bài mẫu KHTN 7 qua process_sample_input."""
        from chuc_nang_1_nhap_de.validator import process_sample_input
        result = process_sample_input("VL01")
        self.assertEqual(result.input_type, InputType.SAMPLE)
        self.assertEqual(result.sample_id, "VL01")
        self.assertIn("xe đạp", result.text_content)
        self.assertFalse(result.is_confirmed, "Quy tắc FR-01: Chưa xác nhận thì is_confirmed = False")
        self.assertTrue(result.is_valid)

        # Kiểm tra alias tương thích ngược
        alias_result = process_sample_input("co_hoc_01")
        self.assertEqual(alias_result.sample_id, "VL01")


    # --- 6. KIỂM THỬ ĐẦU VÀO GIỌNG NÓI & CHUẨN HÓA KHTN ---
    def test_voice_normalization_physics_units(self):
        """Kiểm tra chuẩn hóa thuật ngữ & đơn vị đo Vật lý từ giọng nói."""
        from chuc_nang_1_nhap_de.voice_service import normalize_spoken_khtn
        spoken = "Một người đi xe đạp với vận tốc 15 ki lô mét trên giờ trong thời gian 30 phút."
        normalized = normalize_spoken_khtn(spoken)
        self.assertIn("km/h", normalized)
        self.assertNotIn("ki lô mét trên giờ", normalized)

    def test_voice_normalization_chemistry_bio(self):
        """Kiểm tra chuẩn hóa công thức hóa học và thuật ngữ sinh học từ giọng nói."""
        from chuc_nang_1_nhap_de.voice_service import normalize_spoken_khtn
        spoken = "Hòa tan can xi các bo nát vào axit clohydric thu được khí các bon níc và nước."
        normalized = normalize_spoken_khtn(spoken)
        self.assertIn("CaCO3", normalized)
        self.assertIn("HCl", normalized)
        self.assertIn("CO2", normalized)

    def test_process_voice_input_valid(self):
        """Kiểm tra xử lý đầu vào giọng nói hợp lệ."""
        from chuc_nang_1_nhap_de.voice_service import process_voice_input
        raw = "Một vật chuyển động đều với tốc độ 5 mét trên giây đi được quãng đường 100 mét."
        result = process_voice_input(raw)
        self.assertEqual(result.input_type, InputType.VOICE)
        self.assertTrue(result.is_valid)
        self.assertFalse(result.is_confirmed, "Chưa xác nhận thì is_confirmed = False")
        self.assertIn("5 m/s", result.text_content)
        self.assertIn("100 m", result.text_content)

    def test_process_voice_input_empty_and_short(self):
        """Kiểm tra từ chối giọng nói rỗng hoặc quá ngắn."""
        from chuc_nang_1_nhap_de.voice_service import process_voice_input
        res_empty = process_voice_input("   ")
        self.assertFalse(res_empty.is_valid)
        self.assertIn("Chưa ghi nhận được", res_empty.validation_error)

        res_short = process_voice_input("alo")
        self.assertFalse(res_short.is_valid)
        self.assertIn("quá ngắn", res_short.validation_error)

    def test_voice_presets_available(self):
        """Kiểm tra danh sách mẫu phát âm thử nghiệm chuẩn 3 phân môn."""
        from chuc_nang_1_nhap_de.voice_service import get_demo_voice_presets
        presets = get_demo_voice_presets()
        self.assertGreaterEqual(len(presets), 3)
        strands = [p["strand"] for p in presets]
        self.assertIn("Vật lý", strands)
        self.assertIn("Hóa học", strands)
        self.assertIn("Sinh học", strands)


if __name__ == "__main__":
    unittest.main(verbosity=2)

