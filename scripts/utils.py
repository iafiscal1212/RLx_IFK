#!/usr/bin/env python3
"""
Shared utility functions for guard scripts.
"""

def read_file_content(filepath: str) -> str:
    """
    Reads a file's content, ignoring read errors and non-UTF8 characters.
    Returns an empty string on failure.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (IOError, OSError):
        return ""
