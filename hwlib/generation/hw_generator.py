from pathlib import Path
from shutil import rmtree, copy, copytree, make_archive
from typing import Optional
from subprocess import Popen, PIPE
import re
from collections import Counter

from .transformers import (get_ho_sup, get_ho_task, get_ho_solu,
                           get_ho_test, get_ho_usage_checker,
                           get_lf_sup_task,
                           get_grader_solu, get_grader_test,
                           get_grader_usage_checker)
from .checkers import pre_check_mmodule, final_control
from .utils import MetaModule, NameReplacer
from hwlib.logger import logger
from .obfuscate import obfuscate_solution


class HWGenerator:
    def __init__(self, proj_dir: Path, runfile: Path,
                 output_dir: Path, template_dir: Path):
        self.output_dir = output_dir

        self.proj_dir = proj_dir
        self.runfile = runfile
        self.template_dir = template_dir
        proj2run = self.runfile.relative_to(self.proj_dir)
        self.code_dir = self.proj_dir.joinpath(proj2run.parts[0])

        self.tmp_test_data = output_dir.joinpath('tmptestdata.pickle')
        self.latex_dir = output_dir.joinpath(f'latex_{self.proj_dir.name}')

        self.ho_proj_dir = output_dir.joinpath('HO_'+self.proj_dir.name)
        self.ho_code_dir = self.ho_proj_dir.joinpath(self.code_dir.name)
        self.ho_solu_dir = self.ho_code_dir.joinpath('solution')
        self.ho_test_dir = self.ho_proj_dir.joinpath('tests')

        self.lf_proj_dir = output_dir.joinpath('LF_'+self.proj_dir.name)
        self.lf_code_dir = self.lf_proj_dir.joinpath(self.code_dir.name)
        self.lf_solu_dir = self.lf_code_dir.joinpath('solution')
        self.lf_test_dir = self.lf_proj_dir.joinpath('tests')

        self.gr_proj_dir = output_dir.joinpath('GR_'+self.proj_dir.name)
        self.gr_code_dir = self.gr_proj_dir.joinpath(self.code_dir.name)
        self.gr_solu_dir = self.gr_code_dir.joinpath('solution')
        self.gr_test_dir = self.gr_proj_dir.joinpath('tests')

        self.modules = [MetaModule(fp, self.proj_dir)
                        for fp in self.code_dir.rglob('*.py')]
        self.task_modules = [m for m in self.modules if m.istask]

        self.testtemplate = MetaModule(
            self.template_dir.joinpath('testfile.py'))
        self.solu_checker = MetaModule(
            self.template_dir.joinpath('solu_usage_checker.py'))

        self.data_process: Optional[PIPE] = None

    def call(self):
        self.start_data_collection(self.tmp_test_data)
        self.clean_output_folders()
        self.create_handout()
        self.create_lf_and_latex()

        self.create_grader()
        self.obfuscate_solutions()
        self.wait_for_data_collection()
        self.add_test_data()
        self.zip()
        self.perform_final_control()

    def create_handout(self):
        logger.info('Creating handout folder')
        self.create_ho_folder_structure()
        self.copy_template_files()
        self.modify_template_files()
        checker = get_ho_usage_checker(self.solu_checker)
        self.ho_solu_dir.joinpath('solu_usage_checker.py').write_text(checker)
        for module in self.modules:
            pre_check_mmodule(module)

            task = (get_ho_task if module.istask else get_ho_sup)(module)
            solu = get_ho_solu(module)

            self.ho_code_dir.joinpath(module.path_rel2code).write_text(task)
            self.ho_solu_dir.joinpath(module.path_rel2code).write_text(solu)

            if module.istask:
                test = get_ho_test(module, self.testtemplate)
                tname = f"test_{module.path.name}"
                self.ho_test_dir.joinpath(tname).write_text(test)

    def create_lf_and_latex(self):
        logger.info('Creating LF folder')
        self.latex_dir.mkdir()
        copytree(self.ho_proj_dir, self.lf_proj_dir)
        for module in self.modules:
            lf = get_lf_sup_task(module)
            self.lf_code_dir.joinpath(module.path_rel2code).write_text(lf)

            for relpath, value in module.latex_file_contents.items():
                fpath = self.latex_dir.joinpath(relpath)
                fpath.parent.mkdir(parents=True, exist_ok=True)
                fpath.write_text(value)

    def zip(self):
        for dir in [self.ho_proj_dir, self.lf_proj_dir, self.gr_proj_dir]:
            make_archive(dir, 'zip', dir)

    def create_grader(self):
        copytree(self.ho_proj_dir, self.gr_proj_dir)
        checker = get_grader_usage_checker(self.solu_checker)
        self.gr_solu_dir.joinpath('solu_usage_checker.py').write_text(checker)
        for module in self.modules:
            solu = get_grader_solu(module)
            self.gr_solu_dir.joinpath(module.path_rel2code).write_text(solu)
            if module.istask:
                test = get_grader_test(module, self.testtemplate)
                tname = f"test_{module.path.name}"
                self.gr_test_dir.joinpath(tname).write_text(test)

    def clean_output_folders(self):
        if self.output_dir.is_dir():
            rmtree(self.output_dir)
        self.output_dir.mkdir()

    def create_ho_folder_structure(self):
        self.ho_proj_dir.mkdir()
        for m in self.modules:
            for d in self.ho_code_dir, self.ho_solu_dir:
                d.joinpath(m.path_rel2code.parent
                           ).mkdir(exist_ok=True, parents=True)
        self.ho_test_dir.mkdir()
        self.ho_test_dir.joinpath('data').mkdir()
        self.ho_solu_dir.joinpath('__init__.py').touch()
        self.ho_code_dir.joinpath('__init__.py').touch()

    def obfuscate_solutions(self):
        for solupath in (self.ho_solu_dir, self.lf_solu_dir):
            obfuscate_solution(solupath)

    def copy_proj_files(self):
        def from_proj(path: Path):
            newpath = self.proj_dir.joinpath(path.relative_to(self.proj_dir))
            copy(path, newpath)

    def copy_template_files(self):

        def from_tpl(name: Path, target: Path):
            path = self.template_dir.joinpath(name)
            if target.exists() and target.is_dir():
                target = target.joinpath(path.name)
            if path.is_file():
                copy(path, target)
            elif path.is_dir():
                copytree(path, target)
            else:
                raise Exception

        from_tpl('vscode', self.ho_proj_dir.joinpath('.vscode'))
        # from_tpl('devcontainer', self.ho_proj_dir.joinpath('.devcontainer'))
        from_tpl('compare.py', self.ho_test_dir)
        from_tpl('conftest.py', self.ho_test_dir)
        from_tpl('create_handin.py', self.ho_proj_dir)

    def modify_template_files(self):
        replacements = {'CODEDIR': self.code_dir.name}
        for file in [f for f in self.ho_proj_dir.rglob('*') if f.is_file()]:
            text = file.read_text()
            for pattern, repl in replacements.items():
                text = re.sub(pattern, repl, text)
            file.write_text(text)

    def start_data_collection(self, outfile):
        logger.info('Starting data collection')
        cmd = f"HWLIB_CATCH_FILE={outfile} python3 {self.runfile}"
        self.data_process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)

    def wait_for_data_collection(self):
        logger.info('Waiting for data collection')
        self.data_process.wait()
        stderr = self.data_process.stderr.read()
        stdout = self.data_process.stdout.read()
        assert not self.data_process.returncode, stderr.decode("utf-8")

    def add_test_data(self):
        logger.info('Adding test data')
        for dir in (self.ho_test_dir, self.lf_test_dir, self.gr_test_dir):
            copy(self.tmp_test_data, dir / 'data/testdata.pickle')
        self.tmp_test_data.unlink()

    def perform_final_control(self):
        logger.info('Performing Final Control')
        res_arr = final_control(self.output_dir, self.gr_proj_dir)
        for i in range(4, 7):
            logger.info(f'{res_arr[i, 2]}: {Counter(res_arr[i, 4:])}')
