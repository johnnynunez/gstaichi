#!/bin/bash

set -ex

python -V
pwd
ls
uname -a

# python + C++
# =============

pip install pre-commit
pre-commit run -a

# python
# ======

pip install mypy
# FIXME: Need to deal with all the ti.template() and similar, which
# violate typing/myp rules. And then we can run:
# mypy python

pip install isort
isort --check-only --diff python

# C++
# ===

# TODO: figure out how to run clang-tidy
