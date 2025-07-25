import os
import re

BUILD_TOP = os.environ.get("BUILD_TOP_PATH")
if not BUILD_TOP:
    raise RuntimeError("BUILD_TOP_PATH environment variable not set")

debug_echo = 'echo "DEBUG-INJECT: ({file}) CWD: $(pwd)" >&2\n'

files_to_patch = [
    os.path.join(BUILD_TOP, "build/envsetup.sh"),
    os.path.join(BUILD_TOP, "vendor/twrp/build/envsetup.sh"),
]

for filepath in files_to_patch:
    if not os.path.exists(filepath):
        continue

    with open(filepath, "r") as f:
        lines = f.readlines()

    modified = []
    injected_debug = False

    for line in lines:
        # Inject debug print at the top
        if not injected_debug:
            modified.append(debug_echo.format(file=os.path.relpath(filepath, BUILD_TOP)))
            injected_debug = True

        # Match `[ -s "some/path/Android.mk" ]`
        mk_check = re.search(r'\[ -s\s+"?([^"\]]*Android\.mk)"?\s*\]', line)
        if mk_check:
            mk_path = mk_check.group(1)
            modified.append(f'if [ ! -s "{mk_path}" ]; then\n')
            modified.append(f'  echo "WARNING: Missing or empty {mk_path} ignored" >&2\n')
            modified.append('else\n')
            modified.append(f'  {line.strip()}\n')
            modified.append('fi\n')
        else:
            modified.append(line)

    with open(filepath, "w") as f:
        f.writelines(modified)

    print(f"✅ Patched: {filepath}")
