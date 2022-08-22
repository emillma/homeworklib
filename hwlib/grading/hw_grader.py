from pathlib import Path
from shutil import rmtree, copy, copytree
from typing import Optional
from subprocess import Popen, PIPE
import re
from pytest import main as runpytest
from .utils import parse_junit_xml, get_csv
from multiprocessing import Pool, current_process, cpu_count
import sys
import os
from itertools import repeat
from typing import Tuple, Set
from hwlib.config import DEBUG
import filecmp


class HWGrader:
    def __init__(self, handins_dir: Path, grader_dir: Path):
        self.handins_dir = handins_dir
        self.grader_dir = grader_dir

        self.work_dir = self.handins_dir.joinpath('_tmp_work')
        self.report_dir = self.work_dir.joinpath('reports')
        self.handins = sorted(list(p for p in self.handins_dir.iterdir()
                                   if p.name != '_tmp_work'))

    def call(self):
        self.cleanup()
        self.makedirs()
        os.environ['PYTHONOPTIMIZE'] = '1'

        def mute():
            sys.stdout = open(os.devnull, 'w')
        args = zip(self.handins[:10],
                   repeat(self.work_dir),
                   repeat(self.grader_dir))

        p = Pool(cpu_count(), initializer=mute)
        chunksize = (len(self.handins)-1)//cpu_count() + 1
        # resiter = p.imap_unordered(self.grade, args, chunksize)
        resiter = map(self.grade, args)

        res = get_csv(resiter)
        self.work_dir.joinpath(f'{self.grader_dir.name}.csv').write_text(res)

    def makedirs(self):
        for dir in (self.work_dir, self.handins_dir, self.report_dir):
            dir.mkdir(parents=True, exist_ok=True)

    def cleanup(self):
        if self.work_dir.is_dir():
            rmtree(self.work_dir)

    @ staticmethod
    def grade(args: Tuple[Path, Path, Path]):
        handin_dir, work_dir, gr_dir = args
        process_dir = work_dir.joinpath(current_process().name)
        junit_file = Path(process_dir.joinpath('_junit.xml'))
        if not process_dir.is_dir():
            copytree(gr_dir, process_dir)

        HWGrader.insert_handin_files(handin_dir, process_dir)
        runpytest([str(process_dir),
                   '--capture=no',
                   '--tb=no',
                   '--continue-on-collection-errors',
                   f'--junitxml={junit_file}'])
        results = parse_junit_xml(junit_file)

        HWGrader.restore_files(process_dir, gr_dir)

        if DEBUG >= 2:
            HWGrader.verify_integrity(process_dir, gr_dir)
        return handin_dir.name, results

    @ staticmethod
    def insert_handin_files(handin_dir: Path, process_dir: Path):
        for hi_path in handin_dir.rglob('*'):
            relpath = hi_path.relative_to(handin_dir)
            pr_path = process_dir.joinpath(relpath)

            if relpath.match('tests/*') or relpath.match('*solution/*'):
                raise NotImplementedError
            elif hi_path.is_dir():
                pr_path.mkdir(exist_ok=True)
            elif hi_path.is_file():
                copy(hi_path, pr_path)
            else:
                raise NotImplementedError

    @ staticmethod
    def restore_files(process_dir: Path, gr_dir: Path):
        reversed
        for pr_path in reversed(list(process_dir.rglob('*'))):
            relpath = pr_path.relative_to(process_dir)
            gr_path = gr_dir.joinpath(relpath)

            if gr_path.is_dir():
                continue
            elif gr_path.is_file():
                if filecmp.cmp(pr_path, gr_path):
                    continue
                else:
                    copy(gr_path, pr_path)
            elif pr_path.is_dir():
                pr_path.rmdir()
            elif pr_path.is_file():
                pr_path.unlink()
            else:
                raise NotImplementedError

    @ staticmethod
    def verify_integrity(dira: Path, dirb: Path):
        def verify(cmp: filecmp.dircmp):
            if cmp.left_only or cmp.right_only or cmp.diff_files:
                raise Exception(f'{dira.name} != {dirb.name}')
            for child_cmp in cmp.subdirs.values():
                verify(child_cmp)
        verify(filecmp.dircmp(dira, dirb))
