# pylint: skip-file
from copy import deepcopy
import sys
from pathlib import Path

project_dir = Path(__file__).parents[1]  # nopep8
sys.path.insert(0, str(project_dir.joinpath(CODEDIRSTR)))  # nopep8

from compare import compare
import MODULEFULL as MODULE
from solution.solu_usage_checker import UsageChecker


class TESTCLASS:
    """Test class"""

    def test_output(self, test_data):
        """Tests if the function is correct by comparing the output
        with the output of the solution

        As python always use pass by reference, not by copy, it also checks if the
        input is changed (or not) in the same way as the in solution
        """
        for kwargs, ret_s in test_data[FUNC_ID]:
            values = tuple(kwargs.values())
            ARGS = values
            ARGS_SOLU = deepcopy(values)
            if RETBLOCK:

                ret = MODULE.FUNCTION(ARGS)
                ret_s = MODULE.FUNCTION(ARGS_SOLU)
            if NORETBLOCK:

                MODULE.FUNCTION(ARGS)

            compare(ARG, ARG_SOLU)
            if RETBLOCK:

                RETS = ret
                RETS_SOLU = ret_s

                compare(RET, RET_SOLU)

    def test_solution_usage(self, test_data):
        """Tests if the solution is used in the function"""
        func_id = FUNC_ID
        for kwargs, ret_s in test_data[func_id]:
            UsageChecker.reset_usage(func_id, PASSWORD)
            MODULE.FUNCTION(**kwargs)
            msg = "The function uses the solution"
            assert not UsageChecker.is_used(func_id), msg


if __name__ == "__main__":
    import os
    import pytest
    os.environ["_PYTEST_RAISE"] = "1"
    pytest.main()
