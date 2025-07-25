import os
import re
import subprocess

def normalize_line_endings(file_path):
    """Run dos2unix to convert CRLF to LF (if available)."""
    try:
        subprocess.run(["dos2unix", file_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[WARN] dos2unix failed or missing: {e}")

def should_ignore_file(file_path):
    ignore_paths = [
        'external/',
        'prebuilts/',
        'kernel/',
        'hardware/qcom/',
        'vendor/qcom/',
        'device/qcom/',
    ]
    return any(file_path.startswith(p) for p in ignore_paths)

def inject_debug_lines(file_path):
    normalize_line_endings(file_path)

    with open(file_path, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    in_function = False

    for idx, line in enumerate(lines):
        stripped = line.strip()

        # Skip blank or comment lines
        if not stripped or stripped.startswith("#"):
            updated_lines.append(line)
            continue

        # Detect function start (e.g. "function foo()" or "foo() {")
        function_start = re.match(r'^\s*(function\s+\w+|\w+\s*\(\))\s*\{?', stripped)
        if function_start:
            in_function = True
            updated_lines.append(line)
            continue

        # Detect function end (heuristic: closing brace on its own line)
        if in_function and stripped == "}":
            in_function = False
            updated_lines.append(line)
            continue

        # Only inject inside function blocks
        if in_function:
            # Add a debug echo for simple assignments
            match_assign = re.match(r'^\s*(\w+)=.*', line)
            if match_assign:
                var_name = match_assign.group(1)
                debug_line = f'echo "[DEBUG] {file_path}:{idx+1} → {var_name}=${{{var_name}}}"\n'
                updated_lines.append(line)
                updated_lines.append(debug_line)
                continue

        updated_lines.append(line)

    with open(file_path, 'w') as f:
        f.writelines(updated_lines)

    normalize_line_endings(file_path)

def walk_and_inject(root_dir):
    for root, _, files in os.walk(root_dir):
        for name in files:
            if name.endswith('.sh'):
                full_path = os.path.join(root, name)
                rel_path = os.path.relpath(full_path, root_dir)
                if not should_ignore_file(rel_path):
                    print(f"[INFO] Injecting into {rel_path}")
                    inject_debug_lines(full_path)

if __name__ == "__main__":
    build_top = os.environ.get("BUILD_TOP_PATH", os.getcwd())
    walk_and_inject(build_top)
