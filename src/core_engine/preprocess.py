import re
from pathlib import Path

def normalise_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9+#./\s-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def read_text_from_file(path: str | Path, *, max_chars: int = 250_000) -> str:
    p = Path(path)

    # 1) Missing
    if not p.exists():
        raise FileNotFoundError(
            f"CV file not found: {p}\n"
            f"Fix: check the path, filename, and that it’s inside your project folder."
        )

    # 2) Wrong type
    if not p.is_file():
        raise IsADirectoryError(
            f"Expected a file but got a folder: {p}\n"
            f"Fix: point to a .txt file, not a directory."
        )

    # 3) Empty (0 bytes)
    if p.stat().st_size == 0:
        raise ValueError(
            f"File is empty (0 bytes): {p}\n"
            f"Fix: open it and paste your CV text, then save."
        )

    # 4) Read
    text = p.read_text(encoding="utf-8", errors="ignore")

    # 5) Too large (optional safety)
    if len(text) > max_chars:
        raise ValueError(
            f"File is too large ({len(text):,} chars): {p}\n"
            f"Fix: use a shorter file or extract the relevant sections."
        )

    # 6) “Looks empty” after stripping
    if not text.strip():
        raise ValueError(
            f"File contains only whitespace: {p}\n"
            f"Fix: ensure it contains real text (not blank lines/spaces)."
        )

    return text