# pylint: skip-file

import os
import pytest
import pickle
import pytest
from pathlib import Path

if os.getenv('_PYTEST_RAISE', "0") != "0":
    """Hack to let the debugger in vscode catch the assert statements"""
    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call):
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo):
        raise excinfo.value


@pytest.fixture
def test_data():
    pdata = Path(__file__).parent.joinpath("data/testdata.pickle")
    with open(pdata, 'rb') as file:
        test_data = pickle.load(file)
    return test_data
