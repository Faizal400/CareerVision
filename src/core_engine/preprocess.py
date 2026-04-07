import re


def normalise_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9+#./\s-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

