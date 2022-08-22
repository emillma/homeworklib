import re
from pathlib import Path
import xml.etree.ElementTree as ET
import re
from functools import cache
from typing import Iterable, Tuple
import numpy as np


def extraxt_junitxml_results(junitxml_file: Path) -> dict[str, bool]:
    root = ET.parse(junitxml_file).getroot()
    results = {}
    for testcase in root.iter("testcase"):
        if classname := testcase.attrib['classname']:
            shortened = re.sub(r'^.*?tests\.', r'', classname)
            passed = next(iter(testcase), None) is None
            results.setdefault(shortened, {})[testcase.attrib['name']] = passed
    return results


def format_junit_results(results):
    formated = {}
    for key, val in results.items():
        outres = val.get('test_output', False)
        solres = val.get('test_solution_usage', False)
        res = ''.join('P' if test else 'F' for test in [outres, solres])
        name = re.sub('[tT]est_', '', key)
        formated[name] = res
    return formated


def parse_junit_xml(junitxml_file: Path):
    results = extraxt_junitxml_results(junitxml_file)
    formated = format_junit_results(results)
    return formated


def split_name(name: str):
    def acronym(part: str):
        if len(part) <= 8:
            return part
        else:
            return part[:3] + re.sub('[aeiouy]', '', part[3:])

    module, func_or_method = name.split('.')
    if len(parts := func_or_method.split('__')) >= 2:
        clsname = acronym(parts[0])
        fname = '__'.join(acronym(n) for n in parts[1:])
    else:
        clsname = ''
        fname = acronym(parts[0])
    return [module, clsname, fname]


def get_csv(test_results: Iterable[Tuple[str, dict[str, dict]]]) -> str:
    names = set()
    test_results = sorted([i for i in test_results], key=lambda n: n[0])
    for name, results in test_results:
        names.update(results.keys())

    heading = np.array([split_name(n) for n in names]).T
    heading = np.concatenate((np.tile('', (3, 2)), heading), axis=1)
    heading[2, :2] = ['name', 'total']

    @cache
    def index(name):
        return list(names).index(name)+2
    lines = []
    for name, results in test_results:

        score = sum((r == 'FF' for r in results))
        line = [name, f'{score}/{len(names)}', *(['FF']*len(names))]
        for test, res in results.items():
            line[index(test)] = res
        lines.append(line)
    return '\n'.join((','.join(ln) for ln in (*heading, *lines)))
