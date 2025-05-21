#!/bin/bash

set -ex

echo hello from macos_15.sh
pwd
git submodule 
git submodule update --init --recursive
brew list
brew install python@3.10
brew link --force python@3.10
which python
which python3
sudo rm /opt/homebrew/bin/python3
sudo rm /Library/Frameworks/Python.framework/Versions/Current/bin/python
sudo ln -s /opt/homebrew/bin/python3.10 /opt/homebrew/bin/python3
sudo ln -s /opt/homebrew/bin/python3.10 /Library/Frameworks/Python.framework/Versions/Current/bin/python
python --version
sw_vers
clang++ --version
uname -a
clang --version
ls -la
python -V
brew install molten-vk
brew install llvm@15
./build.py --shell
python setup.py develop
