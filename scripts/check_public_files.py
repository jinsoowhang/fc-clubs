"""Check publishable files for private runtime data and personal machine paths."""

import os
import re
import subprocess
from pathlib import Path

PRIVATE_DIRS = {
    ".git",
    ".venv",
    ".secrets",
    "data",
    "target",
    "logs",
    "dbt_packages",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
PRIVATE_SUFFIXES = {".duckdb", ".wal", ".db", ".sqlite", ".sqlite3", ".xlsx", ".pyc"}
TEXT_SUFFIXES = {".py", ".sql", ".yml", ".yaml", ".toml", ".md", ".sh", ".lock"}


def check(root: Path) -> list[str]:
    problems = []
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            capture_output=True,
            check=True,
        )
        paths = [Path(value.decode()) for value in result.stdout.split(b"\0") if value]
    else:
        # Only public source/config/docs; never open ignored data or dependency artifacts.
        paths = []
        for directory, folders, filenames in os.walk(root):
            folders[:] = [folder for folder in folders if folder not in PRIVATE_DIRS]
            paths.extend((Path(directory) / filename).relative_to(root) for filename in filenames)
    for relative in paths:
        if (
            any(part in PRIVATE_DIRS for part in relative.parts)
            or relative.suffix in PRIVATE_SUFFIXES
            or relative.name.startswith(".env")
            or relative.name == ".user.yml"
        ):
            problems.append("private_file_in_public_inventory")
            continue
        path = root / relative
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        content = path.read_text(encoding="utf-8")
        # Concatenation prevents this scanner's own patterns from matching themselves.
        personal_path = (
            "/mnt/" + r"(?:host/)?[a-z]/Users/[A-Za-z0-9_. -]+/" + "|/" + r"home/[A-Za-z0-9_. -]+/"
        )
        if re.search(personal_path, content):
            problems.append("personal_filesystem_path")
    return sorted(set(problems))


def main():
    problems = check(Path.cwd())
    if problems:
        for problem in problems:
            print(problem)
        return 1
    print("Public-file checks passed; runtime data excluded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
