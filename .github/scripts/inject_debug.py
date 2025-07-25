import os
import re

BUILD_TOP = os.environ.get("BUILD_TOP_PATH")
if not BUILD_TOP:
    raise RuntimeError("BUILD_TOP_PATH environment variable not set")

debug_echo = 'echo "DEBUG-INJECT: ({file}) CWD: $(pwd)" >&2\n'

# Matches any line with -s and Android.mk (with or without full path, quotes, or brackets)
android_mk_pattern = re.compile(
    r"""
    (?P<prefix>.*)            # any leading code
    \[\s*-s\s+                # [ -s 
    (?P<path>[^ \]]*Android\.mk)  # path/to/Android.mk
    \s*\]                     # ]
    (?P<suffix>.*)            # anything after
    """,
    re.VERBOSE,
)

files_to_patch = [
    os.path.join(BUILD_TOP, "build/envsetup.sh"),
    os.path.join(BUILD_TOP, "vendor/twrp/build/envsetup.sh"),
]

for filepath in files_to_patch:
    if not os.path.exists(filepath):
        continue

    print(f"[inject] Patching {filepath}")

    with open(filepath, "r") as f:
        lines = f.readlines()

    modified_lines = []
    injected = False
    for line in lines:
        if not injected:
            modified_lines.append(
                debug_echo.format(file=os.path.relpath(filepath, BUILD_TOP))
            )
            injected = True

        mk_check = android_mk_pattern.search(line)
        if mk_check:
            path = mk_check.group("path")
            safe_block = (
                f'# DEBUG-INJECT: Safe Android.mk check wrapper for {path}\n'
                f'if [ ! -s "{path}" ]; then\n'
                f'    echo "WARNING: Missing or empty {path} ignored" >&2\n'
                f'else\n'
                f'    {line.strip()}\n'
                f'fi\n'
            )
            modified_lines.append(safe_block)
        else:
            modified_lines.append(line)

    with open(filepath, "w") as f:
        f.writelines(modified_lines)

    print(f"[inject] ✅ Done patching {filepath}")
