"""
Package: chuc_nang_7_demo_offline_cache
Chức năng 7 (FR-10): Chế Độ Demo Offline & Cache Học Liệu 12 Bài Mẫu KHTN 7 Đủ 5 Pha Socratic
Đặc tả dự án: Socrates Nhí v3.0 (Mục 18 - Vận hành lúc thi)
"""

from .offline_model import (
    NetworkMode,
    KnowledgeStrand,
    SocraticPhaseDialogue,
    OfflineSampleProblem
)
from .offline_bank import (
    OFFLINE_SAMPLE_PROBLEMS,
    get_all_offline_problems,
    get_offline_problem_by_id,
    get_offline_problems_by_strand
)
from .offline_engine import (
    OfflineDemoEngine,
    GLOBAL_OFFLINE_ENGINE
)
from .offline_view import OfflineCacheControlView

__all__ = [
    "NetworkMode",
    "KnowledgeStrand",
    "SocraticPhaseDialogue",
    "OfflineSampleProblem",
    "OFFLINE_SAMPLE_PROBLEMS",
    "get_all_offline_problems",
    "get_offline_problem_by_id",
    "get_offline_problems_by_strand",
    "OfflineDemoEngine",
    "GLOBAL_OFFLINE_ENGINE",
    "OfflineCacheControlView"
]
