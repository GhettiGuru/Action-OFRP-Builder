import os
import re

BUILD_TOP = os.environ.get("BUILD_TOP_PATH")
if not BUILD_TOP:
    raise RuntimeError("BUILD_TOP_PATH not set")

files_to_patch = [
    os.path.join(BUILD_TOP, "build/envsetup.sh"),
    os.path.join(BUILD_TOP, "vendor/twrp/build/envsetup.sh"),
]

replacement_cproj = """function cproj()
{
    local TOPFILE=build/make/core/envsetup.mk
    local HERE=$PWD
    local T=
    while [ ! -f "$TOPFILE" ] && [ "$PWD" != "/" ]; do
        T=$PWD
        if [ -f "$T/Android.mk" ]; then
            cd "$T"
            return
        fi
        cd ..
    done
    cd "$HERE"
    echo "DEBUG-INJECT: cproj() could not find Android.mk, returning to $HERE" >&2
}
"""

for filepath in files_to_patch:
    if not os.path.isfile(filepath):
        continue

    with open(filepath, "r") as f:
        content = f.read()

    # Replace existing cproj() function
    updated, count = re.subn(
        r'function cproj\(\)\s*\{.*?\n\}',  # match the whole function (non-greedy)
        replacement_cproj,
        content,
        flags=re.DOTALL,
    )

    if count == 0:
        print(f"No cproj() found in {filepath} — skipping")
        continue

    with open(filepath, "w") as f:
        f.write(updated)

    print(f"✅ Replaced cproj() in {filepath}")
