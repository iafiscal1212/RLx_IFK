def read_file_content(filepath: str) -> str:
    """Reads a file and returns its content, ignoring decoding errors."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""
