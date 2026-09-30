"""
Module: ai_service.py
Dịch vụ Kết nối & Điều phối Trí tuệ Nhân tạo Toàn cục (AI Integration Layer)
Đặc tả: Socrates Nhí v3.0 (Bảng A - Cuộc thi Sáng tạo trẻ Quốc gia AI 2026)

Tính năng:
1. Nạp và quản lý cấu hình .env chuẩn OpenAI-compatible.
2. Tương thích đa mô hình (GPT-4o, GPT-4o-mini, GPT-5-mini, o1/o3-mini, Gemini OpenAI proxy, DeepSeek...).
3. Xử lý an toàn các tham số đặc biệt (max_completion_tokens vs max_tokens, temperature filter).
4. Kiểm thử kết nối trực tiếp (Latency & Model Check).
5. Lưu và cập nhật cấu hình .env trực tiếp từ giao diện App.
"""

import os
import re
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

# Nạp file .env từ thư mục gốc dự án
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = WORKSPACE_ROOT / ".env"


def load_project_env() -> None:
    """Tự động tìm và nạp cấu hình từ file .env vào os.environ."""
    try:
        from dotenv import load_dotenv
        if ENV_FILE_PATH.exists():
            load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)
        else:
            load_dotenv()
    except Exception:
        # Fallback tự đọc file thủ công nếu chưa cài dotenv
        if ENV_FILE_PATH.exists():
            try:
                with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k:
                                os.environ[k] = v
            except Exception:
                pass


# Gọi nạp ngay khi module được import
load_project_env()


def get_ai_config() -> Dict[str, str]:
    """Lấy thông tin cấu hình AI hiện tại."""
    load_project_env()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1"
    model = os.getenv("SOCRATES_MODEL", "").strip() or "gpt-5-mini-2025-08-07"

    # Che mờ API Key để bảo mật hiển thị
    if len(api_key) > 12:
        masked_key = f"{api_key[:7]}...{api_key[-4:]}"
    elif api_key:
        masked_key = "********"
    else:
        masked_key = "Chưa cấu hình"

    return {
        "api_key": api_key,
        "masked_key": masked_key,
        "base_url": base_url,
        "model": model,
        "has_key": bool(api_key)
    }


def save_ai_config(api_key: str, model: str, base_url: str) -> bool:
    """Cập nhật cấu hình vào file .env và nạp lại vào môi trường."""
    api_key = api_key.strip()
    model = model.strip() or "gpt-5-mini-2025-08-07"
    base_url = base_url.strip() or "https://api.openai.com/v1"

    content = (
        "# ==============================================================================\n"
        "# SOCRATES NHÍ v3.0 - CẤU HÌNH KẾT NỐI AI CHUẨN OPENAI-COMPATIBLE\n"
        "# Dự án tham dự Hội thi Sáng tạo trẻ Quốc gia trong lĩnh vực Trí tuệ nhân tạo 2026 - Bảng A\n"
        "# ==============================================================================\n\n"
        f"OPENAI_BASE_URL={base_url}\n"
        f"OPENAI_API_KEY={api_key}\n"
        f"SOCRATES_MODEL={model}\n"
    )

    try:
        with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(content)

        os.environ["OPENAI_BASE_URL"] = base_url
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["SOCRATES_MODEL"] = model
        return True
    except Exception as e:
        print(f"[AI Service] Lỗi lưu .env: {e}")
        return False


def get_openai_client():
    """Khởi tạo OpenAI client từ cấu hình hiện tại."""
    load_project_env()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    try:
        from openai import OpenAI
        return OpenAI(base_url=base_url, api_key=api_key)
    except Exception as e:
        print(f"[AI Service] Không thể tạo OpenAI client: {e}")
        return None


def call_ai_chat_completion(
    messages: List[Dict[str, Any]],
    json_mode: bool = False,
    timeout: float = 18.0,
    max_tokens: Optional[int] = None
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    """
    Gọi Chat Completion đa tương thích với mọi dòng mô hình (GPT-4o, GPT-5-mini, Reasoning...).
    
    Trả về:
    (thành_công: bool, nội_dung_văn_bản: str, dữ_liệu_json: dict, thông_báo_lỗi: str)
    """
    client = get_openai_client()
    if not client:
        return False, None, None, "Chưa thiết lập OPENAI_API_KEY trong cấu hình."

    model = os.getenv("SOCRATES_MODEL", "gpt-5-mini-2025-08-07").strip()

    # Nhận diện mô hình reasoning / gpt-5 / o1 / o3 để điều chỉnh tham số
    is_reasoning_or_gpt5 = any(prefix in model.lower() for prefix in ["gpt-5", "o1", "o3", "o4"])

    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "timeout": timeout,
    }

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    # Thử gọi lượt 1 với tham số phù hợp
    try:
        call_kwargs = dict(kwargs)
        if not is_reasoning_or_gpt5:
            call_kwargs["temperature"] = 0.3
            call_kwargs["max_tokens"] = max_tokens or 1000
        else:
            call_kwargs["reasoning_effort"] = "low"
            call_kwargs["max_completion_tokens"] = max_tokens or 1200

        res = client.chat.completions.create(**call_kwargs)
        content = (res.choices[0].message.content or "").strip()
        
        # Nếu content rỗng (do một số mô hình preview không tương thích json_object), tự động thử lại không ép response_format
        if json_mode and not content:
            retry_raw_kwargs = dict(call_kwargs)
            retry_raw_kwargs.pop("response_format", None)
            res = client.chat.completions.create(**retry_raw_kwargs)
            content = (res.choices[0].message.content or "").strip()

        json_data = None
        if json_mode:
            try:
                json_data = json.loads(content)
            except Exception:
                # Trích xuất JSON từ markdown block ```json ... ``` hoặc khối { ... }
                match = re.search(r"\{[\s\S]*\}", content)
                if match:
                    try:
                        json_data = json.loads(match.group(0))
                    except Exception:
                        pass
                if not json_data:
                    return False, content, None, "Mô hình trả về không đúng định dạng JSON."

        return True, content, json_data, None

    except Exception as e:
        err_str = str(e)
        # Nếu lỗi do temperature, reasoning_effort hoặc max_tokens không hỗ trợ, tự động retry an toàn
        if any(term in err_str.lower() for term in ["temperature", "max_tokens", "reasoning_effort", "unsupported_parameter", "unsupported_value"]):
            try:
                retry_kwargs = dict(kwargs)
                retry_kwargs["max_completion_tokens"] = max_tokens or 1200
                res = client.chat.completions.create(**retry_kwargs)
                content = (res.choices[0].message.content or "").strip()
                json_data = None
                if json_mode:
                    try:
                        json_data = json.loads(content)
                    except Exception:
                        match = re.search(r"\{[\s\S]*\}", content)
                        if match:
                            try:
                                json_data = json.loads(match.group(0))
                            except Exception:
                                pass
                return True, content, json_data, None
            except Exception as e2:
                return False, None, None, f"Lỗi gọi AI: {e2}"

        return False, None, None, f"Lỗi gọi AI: {err_str}"


def test_ai_connection() -> Dict[str, Any]:
    """Kiểm tra kết nối trực tiếp đến mô hình AI và đo độ trễ (Latency)."""
    cfg = get_ai_config()
    if not cfg["has_key"]:
        return {
            "success": False,
            "latency": 0.0,
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "message": "Chưa nhập OPENAI_API_KEY trong file .env hoặc bảng cài đặt."
        }

    start_time = time.time()
    test_messages = [
        {"role": "system", "content": "Bạn là trợ lý AI. Hãy chào ngắn gọn đúng 5 từ."},
        {"role": "user", "content": "Xin chào!"}
    ]

    success, text, _, error = call_ai_chat_completion(test_messages, json_mode=False, timeout=12.0)
    latency = round(time.time() - start_time, 2)

    if success:
        return {
            "success": True,
            "latency": latency,
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "message": f"Kết nối AI thành công! Độ trễ: {latency}s. Phản hồi: {text[:60]}"
        }
    else:
        return {
            "success": False,
            "latency": latency,
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "message": f"Không thể kết nối đến AI ({error})."
        }
