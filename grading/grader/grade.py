import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
import re
from shutil import copy
from tqdm import tqdm
grading_dir = Path(__file__).parents[1].absolute()
grader_dir = grading_dir.joinpath('grader')
handins_dir = grading_dir.joinpath('handins')

assignments_dir = grading_dir.joinpath('assignments')
result_dir = grading_dir.joinpath("results")

studlist_file = grader_dir.joinpath('studentliste_2021.csv')
studlist = [line.split(',')
            for line in studlist_file.read_text('utf-8').split('\n')]
studlist = sorted(studlist, key=lambda s: s[2])
student_names = dict([(stud[0], stud[1:]) for stud in studlist])


def get_junitxml(test_dir, junit_xml_path):
    subprocess.run(['pytest', '-rA', '--tb=auto',
                    f'--junitxml={junit_xml_path}', f'{test_dir}'],
                   capture_output=True)


test_dir = assignments_dir.joinpath("assignment2/tests")
code_dir = assignments_dir.joinpath("assignment2/assignment2")
handin_dir = handins_dir.joinpath("assignment2")
junitxml_file = result_dir.joinpath('junitxml_tmp.xml')
result_file = result_dir.joinpath('result.csv')

test_names = set()
student_results = {}
for student in student_names.keys():
    pattern = re.compile(rf".*?_{student}_.*?.py")
    pyfile_opt = [path for path in handin_dir.iterdir()
                  if pattern.fullmatch(path.name)]

    testsresults = {}

    if pyfile_opt:
        pyfile = pyfile_opt[0]
        assert len(pyfile_opt) == 1
        copy(pyfile, code_dir.joinpath("task2.py"))
        get_junitxml(test_dir, junitxml_file)
        root = ET.parse(junitxml_file).getroot()

        if list(root.iter("error")):
            testsresults['error'] = True

        else:
            for testcase in root.iter("testcase"):
                classname = testcase.attrib['classname']
                classname = re.sub(r'^.*?tests\.', r'', classname)
                name = testcase.attrib['name']
                passed = testcase.find("failure") is None

                test_names.add(classname)
                testclass_result = testsresults.get(classname, {})
                testclass_result[name] = passed
                testsresults[classname] = testclass_result

            for testclass, testclass_result in testsresults.items():
                bothpassed = all(testclass_result.values())
                testclass_result['both'] = bothpassed

        student_results[student] = testsresults

test_names = sorted(list(test_names))


fname_double = [n for test_name in test_names for n in [test_name, '']]
typename_double = [n for n in
                   ['output', 'solution usage']*len(test_names)]

output = [["ID", "First Name", "Last Name", "Total passed"] + fname_double,
          ['']*4 + typename_double]

for stud, name in student_names.items():
    f_name = name[0]
    l_name = name[1]
    testsresults = student_results.get(stud)
    if testsresults:
        if 'error' in testsresults:
            count = 'Error in code'
            results = []
        else:
            count = str(sum([int(test['both'])
                             for test in testsresults.values()]))

            results = [str(r) for values in testsresults.values()
                       for r in [values.get('test_output', None),
                                 values.get('test_solution_usage', None)]]
    else:
        count = 'missing'
        results = []
    output.append([stud, f_name, l_name, count, *results])
text = '\n'.join([','.join(line) for line in output])
result_file.write_text(text)
