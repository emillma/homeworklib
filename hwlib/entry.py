from pathlib import Path
import argparse
from hwlib.generation import HWGenerator
from hwlib.grading import HWGrader
import hwlib
from shutil import rmtree
from hwlib.logger import logger


def generate_homework():
    parser = argparse.ArgumentParser(description='Generate test data')
    parser.add_argument('module_dir')
    parser.add_argument('runfile')
    parser.add_argument('output_dir')
    parser.add_argument('--rm', action='store_const',
                        default=False, const=True)
    args = parser.parse_args()

    module_dir = Path(args.module_dir).resolve()
    print(module_dir)
    runfile = Path(args.runfile).resolve()
    output_dir = Path(args.output_dir).resolve().joinpath(module_dir.name)

    if output_dir.is_dir() and args.rm:
        rmtree(output_dir)
    else:
        if output_dir.is_dir() and output_dir.iterdir():
            logger.error('Output directory exists and --rm is not set\n'
                         )
            return 1

    template_dir = Path(hwlib.__file__).parents[1].joinpath('templates')

    assert module_dir.is_dir()
    assert runfile.is_file()
    if not output_dir.is_dir():
        output_dir.mkdir()

    HWGenerator(module_dir, runfile, output_dir, template_dir).call()


def grade_homework():
    parser = argparse.ArgumentParser(description='Grade homework')
    parser.add_argument('handins_dir')
    parser.add_argument('grader_dir')
    args = parser.parse_args()

    handins_dir = Path(args.handins_dir).resolve()
    grader_dir = Path(args.grader_dir).resolve()

    assert handins_dir.is_dir()
    assert grader_dir.is_dir()

    HWGrader(handins_dir, grader_dir).call()
