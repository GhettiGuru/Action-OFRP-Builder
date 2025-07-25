import os
import re

BUILD_TOP = os.environ.get("BUILD_TOP_PATH")
if not BUILD_TOP:
    raise RuntimeError("BUILD_TOP_PATH environment variable not set")

debug_echo = 'echo "DEBUG-INJECT: ({file}) CWD: $(pwd)" >> /dev/stderr\n'

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
    injected = False
    for line in lines:
        # Inject debug echo once at the start
        if not injected:
            modified.append(debug_echo.format(file=os.path.relpath(filepath, BUILD_TOP)))
            injected = True

        # Check for Android.mk presence checks
        mk_match = re.search(r"\[ -s ([^\]]*Android\.mk) \]", line)
        if mk_match:
            mk_path = mk_match.group(1)
            modified.append(f'if [ ! -s {mk_path} ]; then echo "WARNING: Missing or empty {mk_path} ignored"; fi\n')

        modified.append(line)

    with open(filepath, "w") as f:
        f.writelines(modified)

    print(f"Injected debug and ignore lines into {filepath}")
