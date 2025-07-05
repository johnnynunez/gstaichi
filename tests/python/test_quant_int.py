import taichi as ti
from tests import test_utils

# TODO: validation layer support on macos vulkan backend is not working.
vk_on_mac = (ti.vulkan, "Darwin")

# TODO: capfd doesn't function well on CUDA backend on Windows
cuda_on_windows = (ti.cuda, "Windows")


@test_utils.test(require=ti.extension.quant_basic)
def test_quant_int_implicit_cast():
    qi13 = ti.types.quant.int(13, True)
    x = ti.field(dtype=qi13)

    bitpack = ti.BitpackedFields(max_num_bits=32)
    bitpack.place(x)
    ti.root.place(bitpack)

    @ti.kernel
    def foo():
        x[None] = 10.3

    foo()
    assert x[None] == 10


@test_utils.test(
    require=ti.extension.quant_basic,
    arch=[ti.cpu, ti.cuda, ti.vulkan],
    exclude=[vk_on_mac, cuda_on_windows],
    debug=True,
)
def test_quant_store_fusion() -> None:
    x = ti.field(dtype=ti.types.quant.int(16, True))
    y = ti.field(dtype=ti.types.quant.int(16, True))
    v = ti.BitpackedFields(max_num_bits=32)
    v.place(x, y)
    ti.root.dense(ti.i, 10).place(v)

    z = ti.field(dtype=ti.i32, shape=(10, 2))

    # should fuse store
    # note: don't think this actually tests that store is fused?
    @ti.kernel
    def store():
        ti.loop_config(serialize=True)
        for i in range(10):
            x[i] = i
            y[i] = i + 1
            z[i, 0], z[i, 1] = x[i], y[i]

    store()
    ti.sync()

    for i in range(10):
        assert z[i, 0] == i
        assert z[i, 1] == i + 1


@test_utils.test(
    require=ti.extension.quant_basic,
    arch=[ti.cpu, ti.cuda, ti.vulkan],
    exclude=[vk_on_mac, cuda_on_windows],
    debug=True,
)
def test_quant_store_no_fusion() -> None:
    x = ti.field(dtype=ti.types.quant.int(16, True))
    y = ti.field(dtype=ti.types.quant.int(16, True))
    v = ti.BitpackedFields(max_num_bits=32)
    v.place(x, y)
    ti.root.dense(ti.i, 10).place(v)

    z = ti.field(dtype=ti.i32, shape=(10, 2))

    @ti.kernel
    def store():
        ti.loop_config(serialize=True)
        for i in range(10):
            x[i] = i
            z[i, 0] = x[i]
            y[i] = i + 1
            z[i, 1] = y[i]

    store()
    ti.sync()

    for i in range(10):
        assert z[i, 0] == i
        assert z[i, 1] == i + 1
