import shutil
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
import re


def get_student_name_dict(student_list_file: Path):
    studlist = [line.split(',')
                for line in student_list_file.read_text('utf-8').split('\n')]
    studlist = sorted(studlist, key=lambda s: s[2])
    student_names = dict([(stud[0], stud[1:]) for stud in studlist])
    return student_names


def prepare_folder(homework_file_names, code_folder_name,
                   test_template_dir: Path, zip_file: Path,
                   tmp_test_dir: Path, tmp_zip_dir: Path):

    shutil.rmtree(tmp_test_dir, ignore_errors=True)
    shutil.rmtree(tmp_zip_dir, ignore_errors=True)

    shutil.copytree(test_template_dir, tmp_test_dir)
    shutil.unpack_archive(zip_file, tmp_zip_dir, 'zip')

    tmp_code_dir = tmp_test_dir.joinpath(code_folder_name)
    for fname in homework_file_names:
        matches = [p for p in tmp_zip_dir.rglob(fname)
                   if "solution" not in str(p)]
        assert len(matches) == 1
        shutil.copy(matches[0], tmp_code_dir.joinpath(matches[0].name))


def cleanup_tmp_stuff(tmp_test_dir, tmp_zip_dir, tmp_junitxml):
    shutil.rmtree(tmp_test_dir, ignore_errors=True)
    shutil.rmtree(tmp_zip_dir, ignore_errors=True)
    shutil.rmtree(tmp_junitxml, ignore_errors=True)


def get_junitxml(test_dir, junit_xml_path):
    subprocess.run(['pytest', '-rA', '--tb=auto',
                    f'--junitxml={junit_xml_path}', f'{test_dir}'],
                   capture_output=True)


def parse_junit_xml(junitxml_file):
    test_class_names = set()
    test_results = {}

    root = ET.parse(junitxml_file).getroot()

    if list(root.iter("error")):
        test_results['error'] = True
        return test_results, test_class_names

    for testcase in root.iter("testcase"):
        classname = testcase.attrib['classname']
        classname = re.sub(r'^.*?tests\.', r'', classname)
        test_class_names.add(classname)

        name = testcase.attrib['name']
        passed = testcase.find("failure") is None
        testclass_result = test_results.get(classname, {})
        testclass_result[name] = passed
        test_results[classname] = testclass_result

    for testclass, testclass_result in test_results.items():
        bothpassed = all(testclass_result.values())
        testclass_result['both'] = bothpassed

    return test_results, test_class_names


def create_csv(student_name_dict, student_results, test_names,
               result_csv_path: Path):
    test_names = sorted(list(test_names))
    test_names_compact = [re.sub(r'[tT]est_', '', name) for name in test_names]
    max_score = len(test_names)
    fname_double = [n for tname in test_names_compact for n in [tname, '']]
    typename_double = [n for n in
                       ['output', 'solution usage']*len(test_names_compact)]

    output = [["ID", "First Name", "Last Name", "Total passed"] + fname_double,
              ['']*4 + typename_double]

    for stud, name in student_name_dict.items():
        f_name = name[0]
        l_name = name[1]
        testsresults = student_results.get(stud)
        if testsresults:
            if 'error' in testsresults:
                score = 'Error in code'
                results = []
            else:
                count = str(sum([int(test['both'])
                                 for test in testsresults.values()]))
                score = f"{count}/{max_score}"
                results = [str(r) for k in test_names
                           for r in [testsresults[k].get('test_output', None),
                                     testsresults[k].get('test_solution_usage', None)]]
        else:
            score = 'missing'
            results = []
        output.append([stud, f_name, l_name, score, *results])
    text = '\n'.join([','.join(line) for line in output])
    result_csv_path.write_text(text)
