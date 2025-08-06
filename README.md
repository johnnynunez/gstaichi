<div align="center">
  <img width="500px" src="https://github.com/taichi-dev/gstaichi/raw/master/misc/logo.png"/>
</div>

---
[![Latest Release](https://img.shields.io/github/v/release/gstaichi-dev/gstaichi?color=blue&label=Latest%20Release)](https://github.com/taichi-dev/gstaichi/releases/latest)
[![downloads](https://pepy.tech/badge/gstaichi)](https://pepy.tech/project/gstaichi)
[![CI](https://github.com/taichi-dev/gstaichi/actions/workflows/testing.yml/badge.svg)](https://github.com/taichi-dev/gstaichi/actions/workflows/testing.yml)
[![Nightly Release](https://github.com/taichi-dev/gstaichi/actions/workflows/release.yml/badge.svg)](https://github.com/taichi-dev/gstaichi/actions/workflows/release.yml)
<a href="https://discord.gg/f25GRdXRfg"><img alt="discord invitation link" src="https://dcbadge.vercel.app/api/server/f25GRdXRfg?style=flat"></a>

```shell
pip install gstaichi  # Install GsTaichi Lang
ti gallery          # Launch demo gallery
```

## What is GsTaichi Lang?

GsTaichi Lang is an open-source, imperative, parallel programming language for high-performance numerical computation. It is embedded in Python and uses just-in-time (JIT) compiler frameworks, for example LLVM, to offload the compute-intensive Python code to the native GPU or CPU instructions.

<a href="https://github.com/taichi-dev/gstaichi/blob/master/python/gstaichi/examples/simulation/fractal.py#L1-L31"> <img src="https://github.com/taichi-dev/public_files/raw/master/gstaichi/fractal_code.png" height="270px"></a>  <img src="https://raw.githubusercontent.com/gstaichi-dev/public_files/master/gstaichi/fractal_small.gif" height="270px">

The language has broad applications spanning real-time physical simulation, numerical computation, augmented reality, artificial intelligence, vision and robotics, visual effects in films and games, general-purpose computing, and much more.

<a href="https://github.com/taichi-dev/gstaichi/blob/master/python/gstaichi/examples/simulation/mpm128.py"><img src="https://github.com/taichi-dev/public_files/raw/master/gstaichi/mpm128.gif" height="192px"></a>
<a href="https://github.com/taichi-dev/quangstaichi"> <img src="https://raw.githubusercontent.com/gstaichi-dev/public_files/master/gstaichi/smoke_3d.gif" height="192px"></a>
<a href="https://github.com/taichi-dev/gstaichi/blob/master/python/gstaichi/examples/rendering/sdf_renderer.py"><img src="https://github.com/taichi-dev/public_files/raw/master/gstaichi/sdf_renderer.jpg" height="192px"></a>
<a href="https://github.com/taichi-dev/gstaichi/blob/master/python/gstaichi/examples/simulation/euler.py"><img src="https://github.com/taichi-dev/public_files/raw/master/gstaichi/euler.gif" height="192px"></a>

<a href="https://github.com/taichi-dev/quangstaichi"><img src="https://raw.githubusercontent.com/gstaichi-dev/public_files/master/gstaichi/elastic_letters.gif" height="213px"></a>
<a href="https://github.com/taichi-dev/quangstaichi"><img src="https://raw.githubusercontent.com/gstaichi-dev/public_files/master/gstaichi/fluid_with_bunnies.gif" height="213px"></a>

[...More](#demos)

## Why GsTaichi Lang?

- Built around Python: GsTaichi Lang shares almost the same syntax with Python, allowing you to write algorithms with minimal language barrier. It is also well integrated into the Python ecosystem, including NumPy and PyTorch.
- Flexibility: GsTaichi Lang provides a set of generic data containers known as *SNode* (/ˈsnoʊd/), an effective mechanism for composing hierarchical, multi-dimensional fields. This can cover many use patterns in numerical simulation (e.g. [spatially sparse computing](https://docs.taichi-lang.org/docs/sparse)).
- Performance: With the `@ti.kernel` decorator, GsTaichi Lang's JIT compiler automatically compiles your Python functions into efficient GPU or CPU machine code for parallel execution.
- Portability: Write your code once and run it everywhere. Currently, GsTaichi Lang supports most mainstream GPU APIs, such as CUDA and Vulkan.
- ... and many more features! A cross-platform, Vulkan-based 3D visualizer, [differentiable programming](https://docs.taichi-lang.org/docs/differentiable_programming),  [quantized computation](https://github.com/taichi-dev/quangstaichi) (experimental), etc.

## Getting Started

### Installation

<details>
  <summary>Prerequisites</summary>

<!--TODO: Precise OS versions-->

- Operating systems
  - Windows
  - Linux
  - macOS
- Python: 3.6 ~ 3.10 (64-bit only)
- Compute backends
  - x64/ARM CPUs
  - CUDA
  - Vulkan
  - OpenGL (4.3+)
  - Apple Metal
  - WebAssembly (experiemental)
- Other packages:
  - cmake >= 3.11.0
 </details>

Use Python's package installer **pip** to install GsTaichi Lang:

```bash
pip install --upgrade gstaichi
```

*We also provide a nightly package. Note that nightly packages may crash because they are not fully tested.  We cannot guarantee their validity, and you are at your own risk trying out our latest, untested features. The nightly packages can be installed from our self-hosted PyPI (Using self-hosted PyPI allows us to provide more frequent releases over a longer period of time)*

```bash
pip install -i https://pypi.gstaichi.graphics/simple/ gstaichi-nightly
```

### Run your "Hello, world!"

Here is how you can program a 2D fractal in GsTaichi:

```py
# python/gstaichi/examples/simulation/fractal.py

import gstaichi as ti

ti.init(arch=ti.gpu)

n = 320
pixels = ti.field(dtype=float, shape=(n * 2, n))


@ti.func
def complex_sqr(z):
    return ti.Vector([z[0]**2 - z[1]**2, z[1] * z[0] * 2])


@ti.kernel
def paint(t: float):
    for i, j in pixels:  # Parallelized over all pixels
        c = ti.Vector([-0.8, ti.cos(t) * 0.2])
        z = ti.Vector([i / n - 1, j / n - 0.5]) * 2
        iterations = 0
        while z.norm() < 20 and iterations < 50:
            z = complex_sqr(z) + c
            iterations += 1
        pixels[i, j] = 1 - iterations * 0.02


gui = ti.GUI("Julia Set", res=(n * 2, n))

for i in range(1000000):
    paint(i * 0.03)
    gui.set_image(pixels)
    gui.show()
```

*If GsTaichi Lang is properly installed, you should get the animation below 🎉:*

<a href="https://github.com/taichi-dev/gstaichi/blob/master/python/gstaichi/examples/simulation/fractal.py#L1-L31"> </a><img src="https://raw.githubusercontent.com/gstaichi-dev/public_files/master/gstaichi/fractal_small.gif" height="270px">

See [Get started](https://docs.taichi-lang.org) for more information.

### Build from source

If you wish to try our experimental features or build GsTaichi Lang for your own environments, see [Developer installation](https://docs.taichi-lang.org/docs/dev_install).

## Documentation

- [Technical documents](https://docs.taichi-lang.org/)
- [API Reference](https://docs.taichi-lang.org/api/)
- [Blog](https://docs.taichi-lang.org/blog)

## Community activity [![Time period](https://images.repography.com/32602247/gstaichi-dev/gstaichi/recent-activity/RlhQybvihwEjfE7ngXyQR9tudBDYAvl27v-NVNMxUrg_badge.svg)](https://repography.com)
[![Timeline graph](https://images.repography.com/32602247/gstaichi-dev/gstaichi/recent-activity/RlhQybvihwEjfE7ngXyQR9tudBDYAvl27v-NVNMxUrg_timeline.svg)](https://github.com/taichi-dev/gstaichi/commits)
[![Issue status graph](https://images.repography.com/32602247/gstaichi-dev/gstaichi/recent-activity/RlhQybvihwEjfE7ngXyQR9tudBDYAvl27v-NVNMxUrg_issues.svg)](https://github.com/taichi-dev/gstaichi/issues)
[![Pull request status graph](https://images.repography.com/32602247/gstaichi-dev/gstaichi/recent-activity/RlhQybvihwEjfE7ngXyQR9tudBDYAvl27v-NVNMxUrg_prs.svg)](https://github.com/taichi-dev/gstaichi/pulls)
[![Trending topics](https://images.repography.com/32602247/gstaichi-dev/gstaichi/recent-activity/RlhQybvihwEjfE7ngXyQR9tudBDYAvl27v-NVNMxUrg_words.svg)](https://github.com/taichi-dev/gstaichi/commits)

## Contributing

Kudos to all of our amazing contributors! GsTaichi Lang thrives through open-source. In that spirit, we welcome all kinds of contributions from the community. If you would like to participate, check out the [Contribution Guidelines](CONTRIBUTING.md) first.

<a href="https://github.com/taichi-dev/gstaichi/graphs/contributors"><img src="https://raw.githubusercontent.com/gstaichi-dev/public_files/master/gstaichi/contributors_gstaichi-dev_gstaichi_18.png" width="800px"></a>

*Contributor avatars are randomly shuffled.*

## License

GsTaichi Lang is distributed under the terms of Apache License (Version 2.0).

See [Apache License](https://github.com/taichi-dev/gstaichi/blob/master/LICENSE) for details.

## Community

For more information about the events or community, please refer to [this page](https://github.com/taichi-dev/community)


### Join our discussions

- [Discord](https://discord.gg/f25GRdXRfg)
- [GitHub Discussions](https://github.com/taichi-dev/gstaichi/discussions)
- [太极编程语言中文论坛](https://forum.gstaichi.graphics/)

### Report an issue

- If you spot an technical or documentation issue, file an issue at [GitHub Issues](https://github.com/taichi-dev/gstaichi/issues)
- If you spot any security issue, mail directly to <a href = "mailto:security@gstaichi.graphics?subject = GsTaichi Security Problem">security@gstaichi.graphics</a>.

### Contact us

- [Discord](https://discord.gg/f25GRdXRfg)
- [WeChat](https://forum.gstaichi-lang.cn/t/topic/2884)

## Reference

### Demos

- [Nerf with GsTaichi](https://github.com/taichi-dev/gstaichi-nerfs)
- [GsTaichi Lang examples](https://github.com/taichi-dev/gstaichi/tree/master/python/gstaichi/examples)
- [Advanced GsTaichi Lang examples](https://github.com/taichi-dev/advanced_examples)
- [Awesome GsTaichi](https://github.com/taichi-dev/awesome-gstaichi)
- [DiffGsTaichi](https://github.com/taichi-dev/diffgstaichi)
- [GsTaichi elements](https://github.com/taichi-dev/gstaichi_elements)
- [GsTaichi Houdini](https://github.com/taichi-dev/gstaichi_houdini)
- [More...](misc/links.md)


### AOT deployment

- [GsTaichi AOT demos & tutorial](https://github.com/taichi-dev/gstaichi-aot-demo/)


### Lectures & talks

- SIGGRAPH 2020 course on GsTaichi basics: [YouTube](https://youtu.be/Y0-76n3aZFA), [Bilibili](https://www.bilibili.com/video/BV1kA411n7jk/), [slides (pdf)](https://yuanming.gstaichi.graphics/publication/2020-gstaichi-tutorial/gstaichi-tutorial.pdf).
- Chinagraph 2020 用太极编写物理引擎: [哔哩哔哩](https://www.bilibili.com/video/BV1gA411j7H5)
- GAMES 201 高级物理引擎实战指南 2020: [课件](https://github.com/taichi-dev/games201)
- 太极图形课第一季：[课件](https://github.com/gstaichiCourse01)
- [GsTaichiCon](https://github.com/taichi-dev/gstaichicon): GsTaichi Developer Conferences
- More to come...

### Citations

If you use GsTaichi Lang in your research, please cite the corresponding papers:

- [**(SIGGRAPH Asia 2019) GsTaichi: High-Performance Computation on Sparse Data Structures**](https://yuanming.gstaichi.graphics/publication/2019-gstaichi/gstaichi-lang.pdf) [[Video]](https://youtu.be/wKw8LMF3Djo) [[BibTex]](https://raw.githubusercontent.com/gstaichi-dev/gstaichi/master/misc/gstaichi_bibtex.txt) [[Code]](https://github.com/taichi-dev/gstaichi)
- [**(ICLR 2020) DiffGsTaichi: Differentiable Programming for Physical Simulation**](https://arxiv.org/abs/1910.00935) [[Video]](https://www.youtube.com/watch?v=Z1xvAZve9aE) [[BibTex]](https://raw.githubusercontent.com/gstaichi-dev/gstaichi/master/misc/diffgstaichi_bibtex.txt) [[Code]](https://github.com/yuanming-hu/diffgstaichi)
- [**(SIGGRAPH 2021) QuanGsTaichi: A Compiler for Quantized Simulations**](https://yuanming.gstaichi.graphics/publication/2021-quangstaichi/quangstaichi.pdf) [[Video]](https://www.youtube.com/watch?v=0jdrAQOxJlY) [[BibTex]](https://raw.githubusercontent.com/gstaichi-dev/gstaichi/master/misc/quangstaichi_bibtex.txt) [[Code]](https://github.com/taichi-dev/quangstaichi)
