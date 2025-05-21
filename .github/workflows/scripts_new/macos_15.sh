#!/bin/bash

set -ex

echo hello from macos_15.sh
pwd
brew list
# brew uninstall python@3.13
brew install python@3.10
brew link --force python@3.10
which python
which python3
sudo rm /opt/homebrew/bin/python3
sudo ln -s /opt/homebrew/bin/python3.10 /opt/homebrew/bin/python3
# export PATH="/opt/homebrew/:$PATH"
# export PATH="/opt/homebrew/opt/python@3.10/bin:$PATH"
# brew unlink --force python@3.13
python --version
sw_vers
clang++ --version
uname -a
clang --version
# free -m
ls -la
python -V
# brew install molten-vk
# brew install llvm@15
# ./build.py --shell
# python setup.py develop
