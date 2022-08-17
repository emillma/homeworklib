import re
from pathlib import Path
import xml.etree.ElementTree as ET
import re


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
        score = 2*val.get('test_output', 0) + val.get('test_solution_usage', 0)
        name = re.sub('[tT]est_', '', key)
        formated[name] = score
    return formated


def parse_junit_xml(junitxml_file: Path):
    results = extraxt_junitxml_results(junitxml_file)
    formated = format_junit_results(results)
    return formated
