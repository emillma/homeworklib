from pathlib import Path
import argparse
from hwlib.generation import HWGenerator
from hwlib.grading import HWGrader
import hwlib


def generate_homework():
    parser = argparse.ArgumentParser(description='Generate test data')
    parser.add_argument('module_dir')
    parser.add_argument('runfile')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    module_dir = Path(args.module_dir).resolve()
    runfile = Path(args.runfile).resolve()
    output_dir = Path(args.output_dir).resolve()
    template_dir = Path(hwlib.__file__).parents[1].joinpath('templates')

    assert module_dir.is_dir()
    assert runfile.is_file()
    assert output_dir.is_dir()

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
