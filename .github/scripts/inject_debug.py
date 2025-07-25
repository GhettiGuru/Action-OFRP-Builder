import os
import re

BUILD_TOP = os.environ.get("BUILD_TOP_PATH")
if not BUILD_TOP:
    raise RuntimeError("BUILD_TOP_PATH environment variable not set")

debug_echo = 'echo "DEBUG-INJECT: ({file}) CWD: $(pwd)" >> /dev/stderr\n'

replacement_cproj = r'''
function cproj()
{
    local TOPFILE=build/make/core/envsetup.mk
    local HERE=$PWD
    local T=
    while [ \( ! \( -f "$TOPFILE" \) \) -a \( "$PWD" != "/" \) ]; do
        T=$PWD
        if [ -f "$T/Android.mk" ]; then
            \cd "$T"
            return
        fi
        \cd ..
    done
    \cd "$HERE"
    echo "DEBUG-INJECT: cproj() could not find Android.mk, returning to $HERE" >&2
}
'''.strip() + "\n"

files_to_patch = [
    os.path.join(BUILD_TOP, "build/envsetup.sh"),
    os.path.join(BUILD_TOP, "vendor/twrp/build/envsetup.sh"),
]

for filepath in files_to_patch:
    if not os.path.exists(filepath):
        print(f"[skip] {filepath} not found")
        continue

    print(f"[inject] Patching {filepath}")
    with open(filepath, "r") as f:
        content = f.read()

    relpath = os.path.relpath(filepath, BUILD_TOP)
    echo_line = debug_echo.format(file=relpath)

    # Inject debug echo near the top (only once)
    if echo_line not in content:
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith("#"):
                lines.insert(i, echo_line.strip())
                break
        content = "\n".join(lines)

    # Replace or insert cproj()
    cproj_re = r'function cproj\(\)\s*\{(?:[^{}]*|\{[^{}]*\})*\}'
    updated, count = re.subn(
        cproj_re,
        replacement_cproj.strip(),
        content,
        flags=re.DOTALL,
    )
    if count == 0:
        print(f"[append] No cproj() found in {filepath}, appending at end")
        if not content.endswith('\n'):
            content += '\n'
        content += '\n' + replacement_cproj
    else:
        content = updated

    # Inject missing Android.mk checks with warning
    mk_check_pattern = re.compile(r'(\[ -s\s+"?\$?\{?[^ \n]*Android\.mk"?\}? \])')
    if 'DEBUG-INJECT: Android.mk warning' not in content:
        def wrap_mk_check(match):
            original = match.group(1)
            return (
                f'if ! {original}; then\n'
                f'  echo "DEBUG-INJECT: Android.mk check failed in {relpath}: {original}" >&2\n'
                f'else\n'
                f'  {original}\n'
                f'fi'
            )
        content = mk_check_pattern.sub(wrap_mk_check, content)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"[done] Injected into {filepath}")
