import shutil
from pathlib import Path


def copy_generate_handout_file(assignment_dir: Path, handout_dir: Path):
    shutil.copy(assignment_dir.joinpath('generate_handin.py'),
                handout_dir.joinpath('generate_handin.py'))
