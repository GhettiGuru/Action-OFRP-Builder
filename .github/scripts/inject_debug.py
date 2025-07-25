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

# cproj() function definition with safe backslashes for Python regex replacement
replacement_cproj = r'''
function cproj()
{
    local TOPFILE=build/make/core/envsetup.mk
    local HERE=$PWD
    local T=
    while [ \( ! \( -f "$TOPFILE" \) \) -a \( "$PWD" != "/" \) ]; do
        T=$PWD
        if [ -f "$T/Android.mk" ]; then
            \\cd "$T"
            return
        fi
        \\cd ..
    done
    \\cd "$HERE"
    echo "DEBUG-INJECT: cproj() could not find Android.mk, returning to $HERE" >&2
}
'''.strip() + "\n"

for filepath in files_to_patch:
    if not os.path.exists(filepath):
        continue

    print(f"[inject] Patching {filepath}")

    with open(filepath, "r") as f:
        lines = f.readlines()

    modified = []
    injected_debug = False
    file_relpath = os.path.relpath(filepath, BUILD_TOP)

    for line in lines:
        if not injected_debug:
            modified.append(debug_echo.format(file=file_relpath))
            injected_debug = True

        modified.append(line)

    content = "".join(modified)

    # Replace original cproj() safely with version that logs debug if Android.mk is missing
    updated, count = re.subn(
        r"function cproj\(\)\s*\{.*?\n\}",
        replacement_cproj,
        content,
        flags=re.DOTALL,
    )

    if count > 0:
        print(f"[inject] Replaced cproj() in {file_relpath}")

    # Write updated file
    with open(filepath, "w") as f:
        f.write(updated)

    print(f"[inject] Injection complete: {file_relpath}")
