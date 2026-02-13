import re
from typing import List

def norm_text(x: str) -> str:
    return re.sub(r"\s+", " ", x.strip().lower())

def tokenize(x: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", norm_text(x))

def format_range(start_s: str, end_s: str) -> str:
    return f"{start_s}–{end_s}"
