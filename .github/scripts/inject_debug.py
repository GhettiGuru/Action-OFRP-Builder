import os
import re

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
    with open(file_path, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    for idx, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines or comments
        if not stripped or stripped.startswith("#"):
            updated_lines.append(line)
            continue

        # Avoid injecting after control structure closures
        if stripped in {"fi", "done", "esac"}:
            updated_lines.append(line)
            continue

        # Avoid injecting after assignments or lines with subshells
        if re.match(r'^\s*\w+\s*=\s*\$\(.+\)', stripped):
            updated_lines.append(line)
            updated_lines.append(f'echo "[DEBUG] {file_path}:{idx+1} - Assignment: {stripped}"\n')
            continue

        # Inject echo after function declarations
        if re.match(r'^\s*(function\s+\w+|\w+\s*\(\))\s*\{?', stripped):
            updated_lines.append(line)
            func_name = re.findall(r'\w+', stripped)[0]
            updated_lines.append(f'echo "[DEBUG] {file_path}:{idx+1} - Entered function: {func_name}"\n')
            continue

        updated_lines.append(line)

    with open(file_path, 'w') as f:
        f.writelines(updated_lines)

def walk_and_inject(root_dir):
    for root, _, files in os.walk(root_dir):
        for name in files:
            if name.endswith('.sh'):
                full_path = os.path.join(root, name)
                rel_path = os.path.relpath(full_path, root_dir)
                if not should_ignore_file(rel_path):
                    inject_debug_lines(full_path)

if __name__ == "__main__":
    build_top = os.environ.get("BUILD_TOP_PATH", os.getcwd())
    walk_and_inject(build_top)
