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

        # Avoid injecting inside multi-line assignments like T=$(pwd)
        assignment_match = re.match(r'^\s*(\w+)\s*=.*', line)
        if assignment_match and 'pwd' in line:
            updated_lines.append(line)
            updated_lines.append(f'echo "[DEBUG] {file_path}:{idx+1} - {assignment_match.group(1)} set to $(pwd)"\n')
            continue

        # Inject echo for common shell functions and commands
        if re.match(r'^\s*(if|for|while|case|function|\w+\(\))\b', stripped):
            updated_lines.append(line)
            updated_lines.append(f'echo "[DEBUG] {file_path}:{idx+1} - Entered: {stripped.split()[0]}"\n')
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
