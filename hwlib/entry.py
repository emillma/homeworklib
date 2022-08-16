from pathlib import Path
import argparse
from .generation.hw_generator import HWGenerator

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate test data')
    parser.add_argument('module')
    parser.add_argument('--runfile', default='run.py')
    parser.add_argument('--handouts_folder', default='handouts')
    args = parser.parse_args()
    assert Path(args.module).is_dir()
    assert Path(args.runfile).is_file()
    assert Path(args.handouts_folder).is_dir()
    HWGenerator(args.module, args.runfile, args.handouts_folder).call()
