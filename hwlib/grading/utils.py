import re
from pathlib import Path
import xml.etree.ElementTree as ET
import re
from functools import cache
from typing import Iterable, Tuple


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


def get_csv(test_results: Iterable[Tuple[str, dict[str, dict]]]) -> str:
    names = set()
    test_results = sorted(list(test_results), key=lambda n: n[0])
    for name, results in test_results:
        names.update(results.keys())

    # tmp = [n.split('.') for n in names]
    # while True:
    #     done = set()
    #     for i, t in enumerate(tmp):
    #         part = t.pop(0)
    heading = ['name', 'total', *names]

    @cache
    def index(name):
        return heading.index(name)
    lines = []
    for name, results in test_results:

        score = sum((r == 'FF' for r in results))
        line = [name, f'{score}/{len(names)}', *(['FF']*len(names))]
        for test, res in results.items():
            line[index(test)] = res
        lines.append(line)
    return '\n'.join((','.join(ln) for ln in (heading, *lines)))
