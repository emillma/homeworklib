from pathlib import Path
from tqdm import tqdm
from hwlib.grading.grading_utils import (get_student_name_dict, prepare_folder,
                                         cleanup_tmp_stuff, get_junitxml, parse_junit_xml,
                                         create_csv)
assignment_name = 'Assignment3_ekf'
code_folder_name = 'ekf'

grading_dir = Path(__file__).parents[1].absolute()
handins_dir = grading_dir.joinpath('handins')
tmp_dir = grading_dir.joinpath('tmp')

tmp_test_dir = tmp_dir.joinpath(f'{assignment_name}')
test_template_dir = grading_dir.joinpath(f'handouts_like/{assignment_name}')
assignment_handins_dir = handins_dir.joinpath(f"{assignment_name}_handins")

studlist_file = grading_dir.joinpath('grader/stud_list_2021.csv')
student_name_dict = get_student_name_dict(studlist_file)

homework_file_names = [p.name[5:] for p in
                       test_template_dir.joinpath("tests").glob("test_*.py")]

student_results = {}
test_class_names_all = set()
stud_ids = list(student_name_dict.keys())
for studid in tqdm(stud_ids):

    files = list(assignment_handins_dir.glob(f"*{studid}*.zip"))
    assert len(files) <= 1
    if len(files) == 1:
        zip_file = files[0]
        tmp_zip_dir = tmp_dir.joinpath(f"{studid}_unzipped")
        prepare_folder(homework_file_names, code_folder_name,
                       test_template_dir, zip_file,
                       tmp_test_dir, tmp_zip_dir)
        tmp_junitxml = tmp_dir.joinpath(f"{studid}_junitxml.xml")
        get_junitxml(tmp_test_dir, tmp_junitxml)
        test_results, test_class_names = parse_junit_xml(tmp_junitxml)
        test_class_names_all.update(test_class_names)
        student_results[studid] = test_results

        cleanup_tmp_stuff(tmp_test_dir, tmp_zip_dir, tmp_junitxml)

result_file = grading_dir.joinpath(f"results/{assignment_name}.csv")

create_csv(student_name_dict, student_results, test_class_names_all,
           result_file)
