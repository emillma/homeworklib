from pathlib import Path
from shutil import rmtree, copy, copytree
from typing import Optional
from subprocess import Popen, PIPE
import re
from pytest import main as runpytest


class HWGrader:
    def __init__(self, handins_dir: Path, grader_dir: Path):
        self.handins_dir = handins_dir
        self.grader_dir = grader_dir

        self.work_dir = self.handins_dir.joinpath('_tmp_work')
        self.report_dir = self.work_dir.joinpath('reports')
        self.handins = list(handins_dir.iterdir())

    def call(self):
        self.cleanup()
        for dir in (self.work_dir, self.handins_dir):
            dir.mkdir(parents=True, exist_ok=True)
        self.grade(self.handins[0])

    def cleanup(self):
        if self.work_dir.is_dir():
            rmtree(self.work_dir)

    def grade(self, handin_dir: Path):
        tmp_dir = self.work_dir.joinpath(f'grade_{handin_dir.name}')
        junit_file = self.report_dir.joinpath(f'{handin_dir.name}.xml')
        copytree(self.grader_dir, tmp_dir)
        for file in (f for f in handin_dir.rglob('*') if f.is_file()):
            relpath = file.relative_to(handin_dir)
            if relpath.match('test/*') or relpath.match('*solution/'):
                raise NotImplementedError
            else:
                file.parent.mkdir(parents=True, exist_ok=True)
                copy(file, tmp_dir.joinpath(relpath))
        runpytest([str(tmp_dir), '-v', f'--junitxml="{junit_file}"'])
        pass
