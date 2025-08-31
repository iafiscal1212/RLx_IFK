#!/usr/bin/env python
import os
import json
import hashlib
import pathlib


def main():
    """Generates a manifest of files in specific subdirectories of local_bundle."""
    root = pathlib.Path(__file__).parent.parent
    base = root / "local_bundle"
    items = []

    for top in ("data", "models", "licenses"):
        d = base / top
        if d.is_dir():
            for p in sorted(d.rglob("*")):
                if p.is_file():
                    h = hashlib.sha256()
                    with open(p, "rb") as fh:
                        for b in iter(lambda: fh.read(1 << 20), b""):
                            h.update(b)
                    items.append({"path": str(p.relative_to(root)), "sha256": h.hexdigest(), "bytes": p.stat().st_size})

    path = base / "dist/BUNDLE_MANIFEST.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2))
    print(f"Wrote {path} with {len(items)} entries")

if __name__ == "__main__":
    main()
