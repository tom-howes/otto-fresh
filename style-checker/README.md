# Style Checker

PEP 8 style checker and auto-fixer for Python projects.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Check for issues

```bash
# Check a directory
python style-checker.py ../backend

# Check with line-by-line detail
python style-checker.py ../backend --verbose
```

### Auto-fix issues

```bash
# Fix a directory
python pep8_styler.py ../backend

# Fix with aggressive mode (handles line length, etc.)
python pep8_styler.py ../backend --aggressive
```

Both scripts automatically skip `venv`, `node_modules`, `__pycache__`, `site-packages`, and other non-source directories.