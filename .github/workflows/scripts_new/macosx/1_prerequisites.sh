#!/bin/bash

set -ex

pwd

python --version
sw_vers
clang++ --version
uname -a
clang --version
ls -la
python -V
pip install scikit-build setuptools_scm
pip install numpy
brew install llvm@15

git submodule
git submodule update --init --recursive
brew list
# brew install python@3.10
brew install pybind11
# brew link --force python@3.10
which python
which python3
which pip
# sudo rm /opt/homebrew/bin/python3
# sudo rm /Library/Frameworks/Python.framework/Versions/Current/bin/python
# sudo ln -s /opt/homebrew/bin/python3.10 /opt/homebrew/bin/python3
# sudo ln -s /opt/homebrew/bin/python3.10 /Library/Frameworks/Python.framework/Versions/Current/bin/python
