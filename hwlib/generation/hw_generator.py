from pathlib import Path
from shutil import rmtree, copy, copytree
from typing import Optional
from subprocess import Popen, PIPE
import re

from .transformers import (get_ho_sup, get_ho_task, get_ho_solu,
                           get_ho_test, get_ho_usage_checker,
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
        self.create_lf()
        self.create_grader()
        self.wait_for_data_collection()
        for dir in (self.ho_test_dir, self.lf_test_dir, self.gr_test_dir):
            copy(self.tmp_test_data, dir.joinpath('data/testdata.pickle'))
        self.tmp_test_data.unlink()

    def create_handout(self):
        self.create_ho_folder_structure()
        self.copy_files()
        self.modify_files()
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

    def create_lf(self):
        copytree(self.ho_proj_dir, self.lf_proj_dir)
        for module in self.modules:
            lf = get_lf_sup_task(module)
            self.lf_code_dir.joinpath(module.path_rel2code).write_text(lf)

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
        for dir in [self.ho_proj_dir, self.lf_proj_dir, self.gr_proj_dir]:
            if dir.is_dir():
                rmtree(dir)

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

    def copy_files(self):
        def from_proj(path: Path):
            newpath = self.proj_dir.joinpath(path.relative_to(self.proj_dir))
            copy(path, newpath)

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
        from_tpl('devcontainer', self.ho_proj_dir.joinpath('.devcontainer'))
        from_tpl('compare.py', self.ho_test_dir)
        from_tpl('conftest.py', self.ho_test_dir)
        from_tpl('create_handin.py', self.ho_proj_dir)

    def modify_files(self):
        replacements = {'CODEDIR': self.code_dir.name}
        for file in [f for f in self.ho_proj_dir.rglob('*') if f.is_file()]:
            text = file.read_text()
            for pattern, repl in replacements.items():
                text = re.sub(pattern, repl, text)
            file.write_text(text)

    def start_data_collection(self, outfile):
        cmd = f"HWLIB_CATCH_FILE={outfile} python3 {self.runfile}"
        self.data_process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)

    def wait_for_data_collection(self):
        self.data_process.wait()
        stderr = self.data_process.stderr.read()
        stdout = self.data_process.stdout.read()
        assert not self.data_process.returncode, stderr.decode("utf-8")
