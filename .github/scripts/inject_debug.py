import os
import re

BUILD_TOP = os.environ.get("BUILD_TOP_PATH")
if not BUILD_TOP:
    raise RuntimeError("BUILD_TOP_PATH environment variable not set")

# Relative debug echo
debug_echo = 'echo "DEBUG-INJECT: ({file}) CWD: $(pwd)" >&2\n'

# Files to patch
files_to_patch = [
    os.path.join(BUILD_TOP, "build/envsetup.sh"),
    os.path.join(BUILD_TOP, "vendor/twrp/build/envsetup.sh"),
]

# Patch each file
for filepath in files_to_patch:
    if not os.path.exists(filepath):
        continue

    with open(filepath, "r") as f:
        lines = f.readlines()

    modified = []
    injected_debug = False

    for line in lines:
        # Inject debug echo once at the top
        if not injected_debug:
            modified.append(debug_echo.format(file=os.path.relpath(filepath, BUILD_TOP)))
            injected_debug = True

        # Patch Android.mk existence checks like: [ -s path/to/Android.mk ]
        mk_check = re.search(r'\[ -s\s+"?([^"\]]*Android\.mk)"?\s*\]', line)
        if mk_check:
            mk_path = mk_check.group(1)
            patched = (
                f'if [ ! -s "{mk_path}" ]; then\n'
                f'  echo "WARNING: Missing or empty {mk_path} ignored" >&2\n'
                f'else\n'
            )
            modified.append(patched)
            modified.append(f'  {line.strip()}\n')  # Indent original logic
            modified.append('fi\n')
        else:
            modified.append(line)

    # Write patched content back to file
    with open(filepath, "w") as f:
        f.writelines(modified)

    print(f"Injected debug and Android.mk check handling into: {filepath}")
