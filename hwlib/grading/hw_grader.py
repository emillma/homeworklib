from pathlib import Path
from shutil import rmtree, copy, copytree, unpack_archive
from .utils import parse_junit_xml, get_results_array
from multiprocessing import Pool, current_process, cpu_count
import subprocess
import os
from itertools import repeat
from typing import Tuple
from hwlib.config import DEBUG
import filecmp
import re
import logging


class HWGrader:
    def __init__(self, handins_dir: Path, grader_dir: Path):
        self.handins_dir = handins_dir
        self.grader_dir = grader_dir

        self.work_dir = self.handins_dir.joinpath('_tmp_work')
        self.report_dir = self.work_dir.joinpath('reports')
        self.handins_unziped = self.handins_dir.joinpath('_unziped')

        pat = r'Name: (.*) \((.*)\)'
        self.name_dict = {m[2]: m[1]
                          for m in (re.match(pat, p.read_text())
                                    for p in self.handins_dir.glob('*.txt'))}

    def call(self):
        self.cleanup()
        self.makedirs()
        self.unzip()

        handins = sorted(list(self.handins_unziped.iterdir()))
        args = zip(handins,
                   repeat(self.work_dir),
                   repeat(self.grader_dir))

        p = Pool(cpu_count())
        chunksize = (len(handins)-1)//cpu_count() + 1
        resiter = p.imap(self.grade, args, chunksize)
        # resiter = map(self.grade, args)
        results = dict(resiter)

        res_arr = get_results_array(results, self.name_dict)
        csvtext = '\n'.join(','.join(ln) for ln in res_arr)
        resname = re.sub('^GR', 'results', f'{self.grader_dir.name}.csv')
        self.handins_dir.joinpath(resname).write_text(csvtext)
        self.cleanup()
        return res_arr

    def get_names(self):
        pat = r'Name: (.*) \((.*)\)'
        return {m[1]: m[2]
                for m in (re.match(pat, p.read_text())
                          for p in self.handins_dir.glob('*.txt'))}

    def makedirs(self):
        for dir in (self.work_dir, self.report_dir, self.handins_unziped):
            dir.mkdir(parents=True, exist_ok=True)

    def unzip(self):
        for handin in self.handins_dir.glob('*.zip'):
            key = re.search(r'_(.*?)_attempt_', handin.name)[1]
            outdir = self.handins_unziped / key
            if not outdir.is_dir():
                unpack_archive(handin, outdir)

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

        try:
            HWGrader.insert_handin_files(handin_dir, process_dir)

            subprocess.run(['pytest',
                            str(process_dir),
                            '--capture=no',
                            '--tb=no',
                            # '--continue-on-collection-errors',
                            f'--junitxml={junit_file}'],
                           stdout=open(os.devnull, 'w'),
                           stderr=open(os.devnull, 'w'))
            results = parse_junit_xml(junit_file)

        except NotImplementedError:
            logging.error(
                f"Could not insert handin files for {handin_dir.name}")
            results = dict()

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
