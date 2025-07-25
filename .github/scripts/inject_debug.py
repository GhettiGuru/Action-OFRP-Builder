import os
import re
from pathlib import Path

top_path = os.environ.get("BUILD_TOP_PATH")
if not top_path:
    raise ValueError("BUILD_TOP_PATH environment variable not set")

TARGET_FILE = Path(top_path) / "build/envsetup.sh"

print(f"[inject] Patching {TARGET_FILE}")
if not TARGET_FILE.exists():
    raise FileNotFoundError(f"{TARGET_FILE} does not exist")

with open(TARGET_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines):
    new_lines.append(line)

    # Inject debug echo only after 'if' lines, not 'fi' or empty ones
    if re.match(r'^\s*if\s.*;\s*then\s*$', line):
        new_lines.append('    echo "[DEBUG] Entered condition at line {}"\n'.format(idx + 1))

    # Optionally log export or cd lines
    elif re.match(r'^\s*export\s', line):
        new_lines.append(f'    echo "[DEBUG] Exporting: {line.strip()}"\n')

    elif re.match(r'^\s*cd\s', line) or re.match(r'^\s*cd\s', line.replace("\\", "")):
        new_lines.append(f'    echo "[DEBUG] Changing directory: {line.strip()}"\n')

# Avoid duplicate injections
if lines != new_lines:
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        print("[inject] Debug lines successfully injected.")
else:
    print("[inject] No changes made; already patched.")
