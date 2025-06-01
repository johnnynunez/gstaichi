#!/bin/bash

echo hello from win.sh
systeminfo
systeminfo
Get-Location
Get-ChildItem
python -V
python --version

git submodule update --init --recursive

python build.py
