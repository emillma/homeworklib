import re
from pathlib import Path
import xml.etree.ElementTree as ET
import re
from functools import cache
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


def get_results_array(test_results: dict[str, dict[str, str]],
                      name_dict: dict[str, str]) -> str:
    stud_ids = set()
    test_results = sorted([i for i in test_results.items()],
                          key=lambda n: n[0])
    for stud_id, results in test_results:
        stud_ids.update(results.keys())
    stud_ids = sorted(stud_ids)

    shape = len(test_results)+4, len(stud_ids)+4
    res_arr = np.full(shape, '', dtype=object)

    res_arr[:3, 4:] = np.array([split_name(n) for n in stud_ids],
                               dtype=object).T
    res_arr[3, :4] = ['last name', 'name', 'stud id', 'total']

    grade_part = res_arr[4:, 4:]
    namepart = res_arr[4:, :3]

    total_per_hin = res_arr[4:, 3]
    total_per_task = res_arr[3, 4:]

    idxdict = dict((name, i) for (i, name) in enumerate(stud_ids))
    for i, (stud_id, results) in enumerate(test_results):
        name = name_dict[stud_id].split(' ')
        namepart[i] = name[-1], ' '.join(name[:-1]), stud_id
        if results is not None:
            idxs = [idxdict[name] for name in results.keys()]
            grade_part[i][idxs] = np.array(tuple(results.values()))
        else:
            grade_part[i][0] = 'wrong handin'
    passed = grade_part == 'PP'
    total_per_hin[:] = [f'{p}/{len(stud_ids)}' for p in np.sum(passed, axis=1)]
    total_per_task[:] = [f'{p}/{len(test_results)}'
                         for p in np.sum(passed, axis=0)]

    return res_arr
