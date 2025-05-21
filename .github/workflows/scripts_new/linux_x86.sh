#!/bin/bash

set -ex

echo hello from linux_x86.sh
pwd
uname -a
free -m
cat /etc/lsb-release
ls -la
python -V
sudo apt update
sudo apt install -y \
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
    libxrandr-dev

sudo apt install -y clang-15 clang++-15 cmake ninja-build python3-dev python3-pip
pip3 install scikit-build

./build.py --shell
python setup.py develop
