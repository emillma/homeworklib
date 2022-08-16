from pathlib import Path
import argparse
from hwlib.generation.hw_generator import HWGenerator
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


if __name__ == '__main__':
    generate_homework()
