#!/usr/bin/env python3

import os
import sys

# Define the debug lines to inject
debug_lines = [
    'echo "DEBUG-INJECT: ({file}) Checking Android.mk:" >> /dev/stderr',
    'echo "DEBUG-INJECT: ({file}) CWD: $(pwd)" >> /dev/stderr',
    'echo "DEBUG-INJECT: ({file}) Path being checked: {path}" >> /dev/stderr',
    'ls -l "{path}" >> /dev/stderr || echo "DEBUG-INJECT: ({file}) Android.mk not found or empty here!" >> /dev/stderr',
    'echo "DEBUG-INJECT: ({file}) Result of -s check: $( [ -s \\"{path}\\" ] && echo TRUE || echo FALSE )" >> /dev/stderr',
]

# File paths to patch
targets = [
    {
        "path": "build/envsetup.sh",
        "search": '[ -s "$T/frameworks/base/services/core/xsd/vts/Android.mk" ]',
        "debug_path": "$T/frameworks/base/services/core/xsd/vts/Android.mk",
        "file_label": "build/envsetup.sh",
    },
    {
        "path": "vendor/twrp/build/envsetup.sh",
        "search": '[ -s "$TOP/frameworks/base/services/core/xsd/vts/Android.mk" ]',
        "debug_path": "$TOP/frameworks/base/services/core/xsd/vts/Android.mk",
        "file_label": "vendor/twrp/build/envsetup.sh",
    },
]

def inject_debug(file_path, match_line, debug_text):
    if not os.path.isfile(file_path):
        print(f"Skipping missing file: {file_path}")
        return

    with open(file_path, 'r') as f:
        lines = f.readlines()

    with open(file_path, 'w') as f:
        for line in lines:
            if match_line in line:
                for debug_line in debug_text:
                    f.write(debug_line + '\n')
            f.write(line)

def main():
    root_dir = os.environ.get("BUILD_TOP_PATH", ".")
    for target in targets:
        file_path = os.path.join(root_dir, target["path"])
        debug_text = [line.format(file=target["file_label"], path=target["debug_path"]) for line in debug_lines]
        inject_debug(file_path, target["search"], debug_text)
        print(f"Injected debug lines into {file_path}")

if __name__ == "__main__":
    main()
