
import sys
import subprocess
from pathlib import Path
from collections import defaultdict

VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv


def check_directory(directory):
    dir_path = Path(directory).resolve()

    if not dir_path.is_dir():
        print(f"Error: '{directory}' is not a valid directory.")
        sys.exit(1)

    EXCLUDE_DIRS = {"venv", ".venv", "env", ".env", "node_modules",
                    "__pycache__", ".git", ".tox", "site-packages",
                    ".eggs", "dist", "build", ".mypy_cache"}

    py_files = sorted(
        f for f in dir_path.rglob("*.py")
        if not any(excluded in f.parts for excluded in EXCLUDE_DIRS)
    )

    if not py_files:
        print(f"No Python files found in '{dir_path}'.")
        return

    # Run pycodestyle in batches to avoid OS argument length limits
    BATCH_SIZE = 100
    file_issues = defaultdict(list)

    for i in range(0, len(py_files), BATCH_SIZE):
        batch = py_files[i:i + BATCH_SIZE]
        result = subprocess.run(
            ["pycodestyle", "--max-line-length=99",
             "--max-doc-length=72",
             *[str(f) for f in batch]],
            capture_output=True, text=True
        )
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            # Default format: /path/to/file.py:10:1:
            # E302 expected 2 blank lines
            parts = line.split(":", 3)
            if len(parts) >= 4:
                filepath = parts[0].strip()
                line_num = parts[1].strip()
                msg = parts[3].strip()
                code = msg.split()[0]
                file_issues[filepath].append((code, line_num, msg))

    # Build report
    dir_counts = defaultdict(lambda: {"files": set(), "issues": 0})
    code_counts = defaultdict(int)
    total_issues = 0
    files_with_issues = 0

    print()
    print("=" * 70)
    print("PEP 8 STYLE REPORT")
    print("=" * 70)

    for f in py_files:
        key = str(f)
        issues = file_issues.get(key, [])
        rel = f.relative_to(dir_path)
        parent = str(rel.parent) if str(rel.parent) != "." else "(root)"
        dir_counts[parent]["files"].add(str(rel))

        if not issues:
            continue

        files_with_issues += 1
        dir_counts[parent]["issues"] += len(issues)
        total_issues += len(issues)

        codes = defaultdict(int)
        for code, line_num, msg in issues:
            codes[code] += 1
            code_counts[code] += 1

        print(f"\n  {rel}  ({len(issues)} issues)")
        if VERBOSE:
            for code, line_num, msg in issues:
                print(f"    line {line_num:<6} {msg}")
        else:
            for code, count in sorted(codes.items(), key=lambda x: -x[1]):
                print(f"    {code:<12} x{count}")

    # Directory summary
    print("\n" + "=" * 70)
    print("ISSUES BY DIRECTORY")
    print("=" * 70)
    for d in sorted(dir_counts.keys()):
        info = dir_counts[d]
        n_files = len(info["files"])
        n_issues = info["issues"]
        bar = "█" * min(n_issues // 5, 30) if n_issues > 0 else ""
        print(f"  {d:<40} {n_files:>3} files  {n_issues:>5} issues  {bar}")

    # Top error codes with descriptions
    CODE_DESCRIPTIONS = {
        "E101": "indentation contains mixed spaces and tabs",
        "E111": "indentation is not a multiple of expected",
        "E112": "expected an indented block",
        "E113": "unexpectedly indented",
        "E114": "indentation is not a multiple of expected (comment)",
        "E115": "expected an indented block (comment)",
        "E116": "unexpected indentation (comment)",
        "E117": "over-indented",
        "E121": "continuation line under-indented",
        "E122": "missing indentation or outdented",
        "E123": "closing bracket does not match indentation",
        "E124": "closing bracket does not match visual indentation",
        "E125": "continuation line not indented enough",
        "E126": "continuation line over-indented for hanging indent",
        "E127": "continuation line over-indented for visual indent",
        "E128": "continuation line under-indented for visual indent",
        "E129": "visually indented line with same indent as next",
        "E131": "continuation line unaligned for block comment",
        "E133": "closing bracket does not match for visual indent",
        "E201": "whitespace after '('",
        "E202": "whitespace before ')'",
        "E203": "whitespace before ':', ';', or ','",
        "E211": "whitespace before '(' or '['",
        "E221": "multiple spaces before operator",
        "E222": "multiple spaces after operator",
        "E223": "tab before operator",
        "E224": "tab after operator",
        "E225": "missing whitespace around operator",
        "E226": "missing whitespace around arithmetic operator",
        "E227": "missing whitespace around bitwise or shift operator",
        "E228": "missing whitespace around modulo operator",
        "E231": "missing whitespace after ',', ';', or ':'",
        "E241": "multiple spaces after ','",
        "E242": "tab after ','",
        "E251": "unexpected spaces around keyword / parameter default",
        "E252": "missing whitespace around parameter default",
        "E261": "at least two spaces before inline comment",
        "E262": "inline comment should start with '# '",
        "E265": "block comment should start with '# '",
        "E266": "too many leading '#' for block comment",
        "E271": "multiple spaces after keyword",
        "E272": "multiple spaces before keyword",
        "E275": "missing whitespace after keyword",
        "E301": "expected 1 blank line before a nested definition",
        "E302": "expected 2 blank lines before function/class definition",
        "E303": "too many blank lines",
        "E304": "defs that immediately follow docstrings should not be decorated",
        "E401": "multiple imports on one line",
        "E402": "module level import not at top of file",
        "E501": "line too long (> 79 characters)",
        "E502": "backslash is redundant between brackets",
        "E701": "multiple statements on one line (colon)",
        "E702": "multiple statements on one line (semicolon)",
        "E711": "comparison to None",
        "E712": "comparison to True/False",
        "E721": "do not compare types, use isinstance()",
        "E722": "do not use bare 'except'",
        "E731": "do not assign a lambda expression",
        "E741": "ambiguous variable name",
        "E742": "ambiguous class name",
        "E743": "ambiguous function name",
        "W191": "indentation contains tabs",
        "W291": "trailing whitespace",
        "W292": "no newline at end of file",
        "W293": "whitespace before a comment",
        "W391": "blank line at end of file",
        "W503": "line break before binary operator",
        "W504": "line break after binary operator",
        "W505": "doc line too long",
    }

    if code_counts:
        print("\n" + "=" * 70)
        print("TOP ERROR CODES")
        print("=" * 70)
        for code, count in sorted(code_counts.items(), key=lambda x: -x[1])[:15]:
            desc = CODE_DESCRIPTIONS.get(code, "unknown")
            print(f"  {code:<8} {count:>5}   {desc}")

    # Summary
    print("\n" + "=" * 70)
    print(f"TOTAL: {total_issues} issues in {files_with_issues}/{len(py_files)} files")
    print("=" * 70)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "."
    check_directory(target)
