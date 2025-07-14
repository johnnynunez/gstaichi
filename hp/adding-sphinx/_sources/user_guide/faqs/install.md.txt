---
sidebar_position: 2
---

# Installation Troubleshooting

## Windows issues

- If Taichi crashes and reports `ImportError` on Windows. Please
  consider installing [Microsoft Visual C++
  Redistributable](https://aka.ms/vs/16/release/vc_redist.x64.exe).

## Python issues

- If `pip` could not find a satisfying package,
  i.e.,

  ```
  ERROR: Could not find a version that satisfies the requirement gs-taichi (from versions: none)
  ERROR: No matching distribution found for gs-taichi
  ```

  - Make sure you're using Python version 3.10/3.11/3.12/3.13:

    ```bash
    python3 -c "import sys;print(sys.version[:sys.version.find('.', 2)])"
    # 3.10, 3.11, 3.12, or 3.13
    ```

  - Make sure your Python executable is 64-bit:

    ```bash
    python3 -c "print(__import__('platform').architecture()[0])"
    # 64bit
    ```

## CUDA issues

- If Taichi crashes with the following errors:

  ```
  [Taichi] mode=release
  [Taichi] version 0.6.0, supported archs: [cpu, cuda, opengl], commit 14094f25, python 3.8.2
  [W 05/14/20 10:46:49.549] [cuda_driver.h:call_with_warning@60] CUDA Error CUDA_ERROR_INVALID_DEVICE: invalid device ordinal while calling mem_advise (cuMemAdvise)
  [E 05/14/20 10:46:49.911] Received signal 7 (Bus error)
  ```

  This might be because that your NVIDIA GPU is pre-Pascal, which we don't support.

- If Taichi exits with message "Out of CUDA pre-allocated memory", e.g.,

  ```python
  import taichi as ti

  ti.init(arch=ti.cuda)

  x = ti.field(dtype=ti.i16)

  ti.root.pointer(ti.i, 1024).dense(ti.i, 1024 * 1024).place(x)
  # A sparse array. Each dense block is 2MB in size.

  # Populate 1024 * 2MB = 2GB memory
  def populate():
    for k in range(1024):
      x[k * 1024 * 1024] = 1

  populate()
  ```

  ... may give you ...

  ```
  [Taichi] Starting on arch=cuda
  Taichi JIT:0: allocate_from_buffer: block: [0,0,0], thread: [0,0,0] Assertion `Out of CUDA pre-allocated memory.
  Consider using ti.init(device_memory_fraction=0.9) or ti.init(device_memory_GB=4) to allocate more GPU memory` failed.
  ```

  This usually happens when you are using sparse data structures that need dynamic GPU memory allocation.
  On platforms without CUDA unified memory support (e.g., Windows),
  Taichi only pre-allocates 1 GB of GPU memory for dynamically allocated data structures.
  To fix this, simply pre-allocate more GPU memory:

    1. Set `ti.init(..., device_memory_fraction=0.9)` to allocate 90% of GPU memory. Replace "90%" with any other fraction depending on your hardware.
    2. Set `ti.init(..., device_memory_GB=4)` to allocate 4 GB GPU memory. Feel free to use any number bigger than 1.
    3. Setting environment variables `TI_DEVICE_MEMORY_FRACTION=0.9` and `TI_DEVICE_MEMORY_GB=4` would also work.

  Note that on Linux, Taichi automatically grows the memory pool using CUDA unified memory mechanisms.

- If you find other CUDA problems:

  - **Possible solution**: add `export TI_ENABLE_CUDA=0` to your
    `~/.bashrc`. This disables the CUDA backend completely and
    Taichi will fall back on other GPU backends such as OpenGL.

## Installation interrupted
During the installation, the downloading process is interrupted because of `HTTPSConnection` error. You can try installing Taichi from a mirror source.

```
pip install gs-taichi -i https://pypi.douban.com/simple
```
