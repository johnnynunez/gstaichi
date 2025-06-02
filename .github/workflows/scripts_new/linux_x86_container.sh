#!/bin/bash

set -ex

echo hello from linux_x86_container.sh
pwd
uname -a
whoami
ls
apt update
apt-get install -y git wget python3 python3-pip
ln -s /usr/bin/python3 /usr/bin/python
python -V
pip --version
git status
git submodule
git submodule update --init --recursive
free -m
cat /etc/lsb-release
ls -la
python -V
apt install -y \
    freeglut3-dev \
    libglfw3-dev \
    libglm-dev \
    libglu1-mesa-dev \
    libwayland-dev \
    libx11-xcb-dev \
    libxcb-dri3-dev \
    libxcb-ewmh-dev \
    libxcb-keysyms1-dev \
    libxcb-randr0-dev \
    libxcursor-dev \
    libxi-dev \
    libxinerama-dev \
    libxrandr-dev \
    pybind11-dev \
    libc++-15-dev \
    libc++abi-15-dev \
    clang-15 \
    libclang-common-15-dev \
    libclang-cpp15 \
    libclang1-15 \
    cmake \
    ninja-build \
    python3-dev \
    python3-pip

pip3 install scikit-build

apt install libjpeg-dev liblz4-dev libpng-dev libssl-dev libzstd-dev -y

mkdir -p ~/bin
cat >~/bin/sudo <<EOF
#!/bin/sh
exec "\$@"
exit 0
EOF
chmod +x ~/bin/sudo
export PATH=~/bin:$PATH

./build.py wheel

pip3 install dist/*.whl
python -c "import taichi as ti; ti.init(arch=ti.cpu)"

pip3 install -r requirements_test.txt
python3.10 tests/run_tests.py
