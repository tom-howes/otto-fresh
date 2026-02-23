import sys
import subprocess
from pathlib import Path

EXCLUDE_DIRS = {"venv", ".venv", "env", ".env", "node_modules",
                "__pycache__", ".git", ".tox", "site-packages",
                ".eggs", "dist", "build", ".mypy_cache"}


def fix_directory(directory, aggressive=False):
    dir_path = Path(directory).resolve()

    if not dir_path.is_dir():
        print(f"Error: '{directory}' is not a valid directory.")
        sys.exit(1)

    py_files = sorted(
        f for f in dir_path.rglob("*.py")
        if not any(excluded in f.parts for excluded in EXCLUDE_DIRS)
    )

    if not py_files:
        print(f"No Python files found in '{dir_path}'.")
        return

    print(f"Fixing {len(py_files)} Python file(s) in '{dir_path}'...")
    if aggressive:
        print("(aggressive mode enabled)\n")
    else:
        print()

    fixed = 0
    for f in py_files:
        rel = f.relative_to(dir_path)
        cmd = ["autopep8", "--in-place",
               "--max-line-length=99"]
        if aggressive:
            cmd.append("--aggressive")
        cmd.append(str(f))

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            fixed += 1
            print(f"  ✓ {rel}")
        else:
            print(f"  ✗ {rel}  ({result.stderr.strip()})")

    print(f"\nDone. Fixed {fixed}/{len(py_files)} files.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pep8_fixer.py <directory> [--aggressive]")
        sys.exit(1)

    target = sys.argv[1]
    aggressive = "--aggressive" in sys.argv
    fix_directory(target, aggressive)
