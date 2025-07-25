import os
import re
import subprocess
import shlex

def normalize_line_endings(file_path):
    """Convert CRLF to LF using dos2unix (if available)."""
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
    norm_path = os.path.normpath(file_path)
    return any(norm_path.startswith(os.path.normpath(p)) for p in ignore_paths)

def inject_debug_lines(file_path):
    try:
        normalize_line_endings(file_path)

        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[ERROR] Failed to read {file_path}: {e}")
        return

    updated_lines = []
    brace_depth = 0
    inside_function = False

    for idx, line in enumerate(lines):
        stripped = line.strip()

        # Skip comments or empty lines
        if not stripped or stripped.startswith("#"):
            updated_lines.append(line)
            continue

        # Detect function start (e.g. "function foo()" or "foo() {")
        if re.match(r'^\s*(function\s+\w+|\w+\s*\(\))\s*\{?', stripped):
            inside_function = True
            brace_depth = stripped.count('{') - stripped.count('}')
            updated_lines.append(line)
            continue

        if inside_function:
            brace_depth += stripped.count('{') - stripped.count('}')
            if brace_depth <= 0:
                inside_function = False
                updated_lines.append(line)
                continue

            match_assign = re.match(r'^\s*(\w+)=.*', line)
            if match_assign:
                var_name = match_assign.group(1)
                # Inject debug line
                debug_line = f'echo "[DEBUG] {file_path}:{idx+1} → {var_name}=${{{var_name}}}"\n'
                updated_lines.append(line)
                updated_lines.append(debug_line)
                continue

        updated_lines.append(line)

    try:
        with open(file_path, 'w') as f:
            f.writelines(updated_lines)
        normalize_line_endings(file_path)
    except Exception as e:
        print(f"[ERROR] Failed to write {file_path}: {e}")

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
