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


def get_results_array(test_results: dict[str, dict[str, str]]) -> str:
    names = set()
    test_results = sorted([i for i in test_results.items()],
                          key=lambda n: n[0])
    for name, results in test_results:
        names.update(results.keys())

    shape = len(test_results)+4, len(names)+2
    res_arr = np.full(shape, '', dtype=object)

    res_arr[:3, 2:] = np.array([split_name(n) for n in names], dtype=object).T
    res_arr[3, :2] = ['name', 'total']

    grade_part = res_arr[4:, 2:]
    namepart = res_arr[4:, 0]

    total_per_hin = res_arr[4:, 1]
    total_per_task = res_arr[3, 2:]

    for i, (name, results) in enumerate(test_results):
        namepart[i] = name
        sortidx = np.argsort(tuple(results.keys()))
        grade_part[i] = np.array(tuple(results.values()))[sortidx]

    passed = grade_part == 'PP'
    total_per_hin[:] = [f'{p}/{len(names)}' for p in np.sum(passed, axis=1)]
    total_per_task[:] = [f'{p}/{len(test_results)}'
                         for p in np.sum(passed, axis=0)]

    return res_arr
