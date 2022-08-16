from pathlib import Path
from shutil import rmtree, copy, copytree
from typing import Optional
from subprocess import Popen, PIPE
import re

from .transformers import get_handout, get_task, get_lf, get_solu, get_test
from .checkers import pre_check_mmodule
from .utils import MetaModule


class HWGenerator:
    def __init__(self, module, runfile, handouts_dir):
        self.proj_dir = Path(module).resolve()
        self.runfile = Path(runfile).resolve()
        self.code_dir = self.proj_dir.joinpath(
            self.runfile.relative_to(self.proj_dir).parts[0])

        self.template_dir = Path(__file__).parents[1].joinpath('templates')
        handouts_dir = Path(handouts_dir).resolve()
        self.out_proj_dir = handouts_dir.joinpath(self.proj_dir.name)
        self.out_test_dir = self.out_proj_dir.joinpath('tests')
        self.out_code_dir = self.out_proj_dir.joinpath(self.code_dir.name)
        self.out_solu_dir = self.out_code_dir.joinpath('solution')
        self.out_test_data = self.out_test_dir.joinpath('data/testdata.pickle')

        self.lf_proj_dir = handouts_dir.joinpath('LF_'+self.proj_dir.name)
        self.lf_code_dir = self.lf_proj_dir.joinpath(self.code_dir.name)
        self.lf_test_dir = self.lf_proj_dir.joinpath('tests')

        self.modules = [MetaModule(fp, self.proj_dir)
                        for fp in self.code_dir.rglob('*.py')]
        self.task_modules = [m for m in self.modules if m.istask]

        template_dir = Path(__file__).parents[1].joinpath('templates')
        self.testtemplate = MetaModule(
            template_dir.joinpath('testfile.py'), None)

        self.data_process: Optional[PIPE] = None

    def call(self):
        self.create_folder_structure()
        self.start_data_collection()
        self.copy_files()
        self.modify_files()
        for module in self.modules:
            pre_check_mmodule(module)

            task = get_task(module)if module.istask else get_handout(module)
            solu = get_solu(module)

            self.out_code_dir.joinpath(module.path_rel2code).write_text(task)
            self.out_solu_dir.joinpath(module.path_rel2code).write_text(solu)

            if module.istask:
                test = get_test(module, self.testtemplate)
                tname = f"test_{module.path.name}"
                self.out_test_dir.joinpath(tname).write_text(test)

        copytree(self.out_proj_dir, self.lf_proj_dir)
        for module in self.modules:
            lf = get_lf(module)
            self.lf_code_dir.joinpath(module.path_rel2code).write_text(lf)

        self.wait_for_data_collection()
        copy(self.out_test_data, self.lf_test_dir.joinpath('data'))

    def create_folder_structure(self):
        if self.out_proj_dir.is_dir():
            rmtree(self.out_proj_dir)
        if self.lf_proj_dir.is_dir():
            rmtree(self.lf_proj_dir)
        self.out_proj_dir.mkdir()
        self.out_code_dir.mkdir()
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
        files = self.out_proj_dir.rglob('*')
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
        from_template('solu_vars.py', self.out_solu_dir)
        from_template('.devcontainer', self.out_proj_dir)
        from_template('.vscode', self.out_proj_dir)

    def start_data_collection(self):
        datafile = self.out_test_dir.joinpath('data/testdata.pickle')
        cmd = f"HWG_DATA_OUT_FILE={datafile} python3 {self.runfile}"
        self.data_process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)

    def wait_for_data_collection(self):
        self.data_process.wait()
        stderr = self.data_process.stderr.read()
        stdout = self.data_process.stdout.read()
        assert not self.data_process.returncode, stderr.decode("utf-8")
