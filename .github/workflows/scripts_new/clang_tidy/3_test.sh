#!/bin/bash

set -ex

python ./scripts/run_clang_tidy.py $PWD/gstaichi -clang-tidy-binary clang-tidy-14 -header-filter=$PWD/gstaichi -j2
