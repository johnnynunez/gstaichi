import gstaichi as ti
from tests import test_utils


@ti.pure
@ti.kernel
def k1(a: ti.types.NDArray[ti.i32, 1]) -> None:
    a[0] += 1


@test_utils.test()
def test_pure_smoke() -> None:

    ti.init(arch=ti.cpu)
    a = ti.ndarray(ti.i32, (10,))
    a[0] = 5
    for i in range(3):
        k1(a)
        print('a[0]', a[0])
        assert a[0] == i + 1

    ti.init(arch=ti.cpu)
    a = ti.ndarray(ti.i32, (10,))
    for i in range(3):
        k1(a)
        print('a[0]', a[0])
        assert a[0] == i + 1
