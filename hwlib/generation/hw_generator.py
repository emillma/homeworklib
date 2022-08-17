from pathlib import Path
from shutil import rmtree, copy, copytree
from typing import Optional
from subprocess import Popen, PIPE
import re

from .transformers import (get_out_sup, get_out_task, get_out_solu,
                           get_out_test, get_out_usage_checker,
                           get_lf_sup_task,
                           get_grader_solu, get_grader_test,
                           get_grader_usage_checker)
from .checkers import pre_check_mmodule
from .utils import MetaModule, NameReplacer


class HWGenerator:
    def __init__(self, proj_dir: Path, runfile: Path,
                 output_dir: Path, template_dir: Path):
        self.proj_dir = proj_dir
        self.runfile = runfile
        self.template_dir = template_dir
        proj2run = self.runfile.relative_to(self.proj_dir)
        self.code_dir = self.proj_dir.joinpath(proj2run.parts[0])

        self.tmp_test_data = output_dir.joinpath('tmptestdata.pickle')

        self.out_proj_dir = output_dir.joinpath(self.proj_dir.name)
        self.out_code_dir = self.out_proj_dir.joinpath(self.code_dir.name)
        self.out_solu_dir = self.out_code_dir.joinpath('solution')
        self.out_test_dir = self.out_proj_dir.joinpath('tests')

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
        self.create_lf()
        self.create_grader()
        self.wait_for_data_collection()
        for dir in (self.out_test_dir, self.lf_test_dir, self.gr_test_dir):
            copy(self.tmp_test_data, dir.joinpath('data/testdata.pickle'))
        self.tmp_test_data.unlink()

    def create_handout(self):
        self.create_out_folder_structure()
        self.copy_files()
        self.modify_files()
        checker = get_out_usage_checker(self.solu_checker)
        self.out_solu_dir.joinpath('solu_usage_checker.py').write_text(checker)
        for module in self.modules:
            pre_check_mmodule(module)

            task = (get_out_task if module.istask else get_out_sup)(module)
            solu = get_out_solu(module)

            self.out_code_dir.joinpath(module.path_rel2code).write_text(task)
            self.out_solu_dir.joinpath(module.path_rel2code).write_text(solu)

            if module.istask:
                test = get_out_test(module, self.testtemplate)
                tname = f"test_{module.path.name}"
                self.out_test_dir.joinpath(tname).write_text(test)

    def create_lf(self):
        copytree(self.out_proj_dir, self.lf_proj_dir)
        for module in self.modules:
            lf = get_lf_sup_task(module)
            self.lf_code_dir.joinpath(module.path_rel2code).write_text(lf)

    def create_grader(self):
        copytree(self.out_proj_dir, self.gr_proj_dir)
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
        for dir in [self.out_proj_dir, self.lf_proj_dir, self.gr_proj_dir]:
            if dir.is_dir():
                rmtree(dir)

    def create_out_folder_structure(self):
        self.out_proj_dir.mkdir()
        for m in self.modules:
            for d in self.out_code_dir, self.out_solu_dir:
                d.joinpath(m.path_rel2code.parent
                           ).mkdir(exist_ok=True, parents=True)
        self.out_test_dir.mkdir()
        self.out_test_dir.joinpath('data').mkdir()
        self.out_solu_dir.joinpath('__init__.py').touch()
        self.out_code_dir.joinpath('__init__.py').touch()

    def modify_files(self):
        replacements = {'CODEDIR': self.code_dir.name}

        for file in self.out_proj_dir.rglob('*'):
            if file.is_file() and re.fullmatch(r'.*[^(.py)]', str(file)):
                text = file.read_text()
                for pattern, repl in replacements.items():
                    text = re.sub(pattern, repl, text)
                file.write_text(text)

    def copy_files(self):
        def from_proj(path: Path):
            newpath = self.proj_dir.joinpath(path.relative_to(self.proj_dir))
            copy(path, newpath)

        def from_template(name: Path, target: Path):
            path = self.template_dir.joinpath(name)
            if target.exists() and target.is_dir():
                target = target.joinpath(path.name)
            if path.is_file():
                copy(path, target)
            elif path.is_dir():
                copytree(path, target)
            else:
                raise Exception

        from_template('compare.py', self.out_test_dir)
        from_template('conftest.py', self.out_test_dir)
        from_template('vscode', self.out_proj_dir.joinpath('.vscode'))
        from_template('devcontainer',
                      self.out_proj_dir.joinpath('.devcontainer'))

    def start_data_collection(self, outfile):
        cmd = f"HWG_DATA_OUT_FILE={outfile} python3 {self.runfile}"
        self.data_process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)

    def wait_for_data_collection(self):
        self.data_process.wait()
        stderr = self.data_process.stderr.read()
        stdout = self.data_process.stdout.read()
        assert not self.data_process.returncode, stderr.decode("utf-8")
