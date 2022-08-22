from pathlib import Path
from shutil import rmtree, copy
import re

project_dir = Path(__file__).parent
handin_dir = project_dir.joinpath('handin')
code_dir_str = 'CODEDIR'


def should_include(relative_path: Path):
    relative_str = str(relative_path.as_posix())
    if not re.fullmatch(r'.*\.py', relative_str):
        return False
    if not re.fullmatch(f'{code_dir_str}/.*', relative_str):
        return False
    if re.fullmatch(f'{code_dir_str}/solution/.*', relative_str):
        return False
    return True


def create_handin():
    rmtree(str(handin_dir), ignore_errors=True)
    handin_dir.mkdir()

    for file in (f for f in project_dir.rglob('*') if f.is_file()):
        rel2project = file.relative_to(project_dir)
        if should_include(rel2project):
            newpath = handin_dir.joinpath(rel2project)
            newpath.parent.mkdir(parents=True, exist_ok=True)
            copy(str(file), str(newpath))


if __name__ == '__main__':
    create_handin()
