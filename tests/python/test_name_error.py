import pytest

import gstaichi as ti
from tests import test_utils


@test_utils.test()
def test_name_error():
    with pytest.raises(ti.GsTaichiNameError, match='Name "a" is not defined'):

        @ti.kernel
        def foo():
            a + 1

        foo()
