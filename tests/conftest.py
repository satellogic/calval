from tempfile import TemporaryDirectory
import pytest


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as tempdir:
        yield tempdir


@pytest.fixture(scope='module')
def module_temp_dir():
    with TemporaryDirectory() as tempdir:
        yield tempdir
