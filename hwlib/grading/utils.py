import re
from pathlib import Path


def should_include(relative_path: Path):
    relative_str = str(relative_path.as_posix())
    if not re.fullmatch(r'.*\.py', relative_str):
        return False
    if not re.fullmatch(f'{code_dir_str}/.*', relative_str):
        return False
    if re.fullmatch(f'{code_dir_str}/solution/.*', relative_str):
        return False
    return True
