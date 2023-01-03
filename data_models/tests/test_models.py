# to run this test file, use 'pytest -k data_models'

import pytest
from data_models.models import remove_empties


class TestStandAloneFunctions:
    def test_remove_empties(self):
        with_empties = ["str1", "str2", "", None, False, [], "str3"]
        no_empties = ["str1", "str2", "str3"]

        assert remove_empties(no_empties) == no_empties  # should output an identical list
        assert (
            remove_empties(with_empties) == no_empties
        )  # should output the predefined no_empties list
