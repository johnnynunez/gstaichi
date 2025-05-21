#!/bin/bash

set -ex

echo hello from macos_15.sh
pwd
brew list
brew uninstall python@3.13
brew install python@3.10
sw_vers
clang++ --version
uname -a
clang --version
# free -m
ls -la
python -V
brew install molten-vk
brew install llvm@15
./build.py --shell
python setup.py develop
