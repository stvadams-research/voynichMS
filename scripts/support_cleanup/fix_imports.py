#!/usr/bin/env python3
import os
from pathlib import Path


def fix_file(path):
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    lines = content.splitlines()
    new_lines = []
    found_sys_path = False

    for line in lines:
        if "sys.path.insert" in line or "sys.path.append" in line:
            found_sys_path = True
            new_lines.append(line)
            continue

        if found_sys_path and (line.startswith("from ") or line.startswith("import ")):
            if "# noqa" not in line and line.strip():
                line = f"{line}  # noqa: E402"

        new_lines.append(line)

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

def main():
    for root, _, files in os.walk("."):
        if ".git" in root or ".venv" in root or "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                fix_file(Path(root) / f)

if __name__ == "__main__":
    main()
