import pytest

from src.utils.puller import DataPuller


@pytest.fixture(scope="function")
def create_data_puller_obj():
    data_puller = DataPuller()
    yield data_puller


class TestSuiteDataPuller:

    def foo(self, create_data_puller_obj):
        pass

    def bar(self, create_data_puller_obj):
        pass
