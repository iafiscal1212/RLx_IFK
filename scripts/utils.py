def read_file_content(path: str) -> str:
    """Safely reads the content of a file."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except IOError:
        return ""
