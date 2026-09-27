"""
Module: formula_normalizer.py
Chức năng 2 (FR-02): Chuẩn hóa công thức Khoa học tự nhiên (KHTN)
Đặc tả: Socrates Nhí v3.0 (Mục 12 - OCR công thức KHTN và quy ước hiển thị)

Quy ước hiển thị thống nhất theo đặc tả:
- Công thức bằng Unicode (v², H₂O, 500 g, 12 N, km/h).
- Đơn vị luôn đi kèm số, cách nhau 1 khoảng trắng (500 g, 12 N).
- Phương trình hóa học giữ chỉ số dưới (H₂, O₂, H₂O, CO₂).
- Dấu mũi tên phản ứng hóa học chuẩn '→'.
"""

import re
from typing import Tuple, List, Set

# Bảng tra cứu ký tự chỉ số dưới (Subscript)
SUBSCRIPT_MAP = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    '+': '₊', '-': '₋'
}

# Bảng tra cứu ký tự chỉ số trên (Superscript)
SUPERSCRIPT_MAP = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    '+': '⁺', '-': '⁻'
}

# Danh sách đơn vị đo KHTN chuẩn
KHTN_UNITS = [
    "km/h", "m/s", "cm/s", "km", "m", "dm", "cm", "mm",
    "kg", "g", "mg", "tạ", "tấn",
    "N", "kN", "J", "kJ", "W", "kW",
    "s", "phút", "h", "giờ",
    "°C", "K", "mol", "l", "ml", "L", "mL",
    "cm³", "m³", "dm³", "cm²", "m²", "km²",
    "g/cm³", "kg/m³", "N/m²", "Pa"
]


def to_subscript(number_str: str) -> str:
    """Chuyển chuỗi số thành ký tự chỉ số dưới (Subscript)."""
    return "".join(SUBSCRIPT_MAP.get(ch, ch) for ch in number_str)


def to_superscript(number_str: str) -> str:
    """Chuyển chuỗi số thành ký tự chỉ số trên (Superscript)."""
    return "".join(SUPERSCRIPT_MAP.get(ch, ch) for ch in number_str)


def normalize_chemical_formulas(text: str) -> str:
    """
    Chuẩn hóa các công thức hóa học: chuyển số thành chỉ số dưới.
    Ví dụ: H2O -> H₂O, CO2 -> CO₂, Fe2O3 -> Fe₂O₃, C6H12O6 -> C₆H₁₂O₆
    """
    def replace_element_sub(match):
        elem = match.group(1)
        sub = match.group(2)
        return f"{elem}{to_subscript(sub)}"

    # Khớp ký hiệu nguyên tố hóa học [A-Z][a-z]? theo sau bởi chữ số
    elem_pattern = r"([A-Z][a-z]?)([0-9]+)"
    text = re.sub(elem_pattern, replace_element_sub, text)

    # Xử lý các nhóm nguyên tử trong ngoặc, ví dụ: (OH)2, (SO4)3
    def replace_bracket_sub(match):
        group = match.group(1)
        sub = match.group(2)
        return f"({group}){to_subscript(sub)}"

    bracket_pattern = r"\(([A-Za-z0-9]+)\)([0-9]+)"
    text = re.sub(bracket_pattern, replace_bracket_sub, text)

    # Chuẩn hóa mũi tên phản ứng hóa học
    text = re.sub(r"\s*(?:-->|->|=>|⟶)\s*", " → ", text)

    return text


def normalize_physics_powers(text: str) -> str:
    """
    Chuẩn hóa lũy thừa và đơn vị thể tích/diện tích trong Vật lý:
    Ví dụ: v^2 -> v², cm^3 -> cm³, 10^3 -> 10³, m^2 -> m²
    """
    # Xử lý dạng x^y hoặc (m/s)^2
    def replace_power(match):
        base = match.group(1)
        power = match.group(2)
        return f"{base}{to_superscript(power)}"

    power_pattern = r"([A-Za-z0-9\)]+)\^([0-9]+)"
    text = re.sub(power_pattern, replace_power, text)

    # Xử lý các đơn vị m2, m3, cm2, cm3 viết liền hoặc có số trước đó (ví dụ 100cm3, 2m2)
    text = re.sub(r"(?<=[0-9\s])(cm|mm|dm|m|km)2\b", r"\1²", text)
    text = re.sub(r"(?<=[0-9\s])(cm|mm|dm|m|km)3\b", r"\1³", text)
    text = re.sub(r"\b(cm|mm|dm|m|km)2\b", r"\1²", text)
    text = re.sub(r"\b(cm|mm|dm|m|km)3\b", r"\1³", text)

    # Chuẩn hóa độ C: oC, do C -> °C
    text = re.sub(r"\b(?:[oO]C|độ\s*C)\b", "°C", text)

    return text


def normalize_units_spacing(text: str) -> str:
    """
    Quy ước đặc tả mục 12: Đơn vị luôn đi kèm số, cách nhau 1 khoảng trắng (ví dụ: 500 g, 12 N, 15 km/h).
    """
    # Tách số và đơn vị nếu bị viết dính liền, ví dụ: 12km/h -> 12 km/h, 500g -> 500 g
    for unit in ["km/h", "m/s", "cm/s", "kg", "mg", "kJ", "kW", "kN", "mol"]:
        text = re.sub(rf"(\d+)\s*{re.escape(unit)}\b", rf"\1 {unit}", text)

    # Các đơn vị đơn chữ: g, N, m, s, J, W, L
    for single_unit in ["g", "N", "m", "s", "J", "W"]:
        text = re.sub(rf"(\d+)\s*{single_unit}\b", rf"\1 {single_unit}", text)

    return text


def extract_formulas_and_units(text: str) -> Tuple[List[str], List[str]]:
    """
    Trích xuất danh sách các công thức và đơn vị đo phát hiện được trong đề bài.
    """
    detected_formulas: Set[str] = set()
    detected_units: Set[str] = set()

    # 1. Tìm công thức hóa học (chứa chỉ số dưới hoặc nguyên tố)
    chem_matches = re.findall(r"\b[A-Z][a-z]?[₀-₉0-9]+(?:[A-Z][a-z]?[₀-₉0-9]*)*\b", text)
    for m in chem_matches:
        if any(ch in m for ch in "₀₁₂₃₄₅₆₇₈₉"):
            detected_formulas.add(m)

    # 2. Tìm công thức vật lý (dạng v = s/t, P = 10m, ...)
    phys_patterns = [
        r"[vV]\s*=\s*[sS]\s*/\s*[tT]",
        r"[pP]\s*=\s*10\s*[mM]",
        r"[dD]\s*=\s*10\s*[dD]",
        r"[dD]\s*=\s*[mM]\s*/\s*[vV]",
        r"[a-zA-Z]+\s*=\s*[^,\n.;]+"
    ]
    for p in phys_patterns:
        matches = re.findall(p, text)
        for m in matches:
            if len(m.strip()) <= 25:
                detected_formulas.add(m.strip())

    # 3. Tìm các phương trình hóa học có dấu '→'
    if "→" in text:
        for line in text.splitlines():
            if "→" in line:
                detected_formulas.add(line.strip())

    # 4. Tìm các đơn vị đo KHTN
    for unit in KHTN_UNITS:
        if re.search(rf"\b\d+(?:[\.,]\d+)?\s*{re.escape(unit)}\b", text):
            detected_units.add(unit)

    return sorted(list(detected_formulas)), sorted(list(detected_units))


def normalize_khtn_text(raw_text: str) -> str:
    """
    Hàm tổng hợp chuẩn hóa toàn bộ văn bản đề bài KHTN:
    1. Chuẩn hóa công thức hóa học (H₂O, CO₂, C₆H₁₂O₆)
    2. Chuẩn hóa lũy thừa vật lý (v², cm³, °C)
    3. Chuẩn hóa khoảng cách đơn vị đo (12 km/h, 500 g)
    """
    if not raw_text:
        return ""

    text = normalize_chemical_formulas(raw_text)
    text = normalize_physics_powers(text)
    text = normalize_units_spacing(text)
    return text.strip()
