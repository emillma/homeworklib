from pathlib import Path
from shutil import rmtree, copy
import re

project_dir = Path(__file__).parent
handin_dir = project_dir.joinpath('handin')
code_dir_str = 'CODEDIR'


def rel2project(path: Path) -> Path:
    return path.relative_to(project_dir)


def rel2handin(path: Path) -> Path:
    return handin_dir.joinpath(rel2project(path))


def should_include(path: Path):
    relative_str = str(rel2project(path).as_posix())
    if not path.is_file():
        return False
    if not re.fullmatch(r'.*\.py', relative_str):
        return False
    if not re.fullmatch(f'{code_dir_str}/.*', relative_str):
        return False
    if re.fullmatch(f'{code_dir_str}/solution/.*', relative_str):
        return False
    return True


def main():
    rmtree(str(handin_dir), ignore_errors=True)
    handin_dir.mkdir()

    for path in project_dir.rglob('*'):
        if should_include(path):
            newpath = rel2handin(path)
            newpath.parent.mkdir(parents=True, exist_ok=True)
            copy(str(path), str(newpath))


if __name__ == '__main__':
    main()
