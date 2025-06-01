#!/bin/bash

echo hello from win.sh
systeminfo
systeminfo
Get-Location
Get-ChildItem
python -V
python --version

git submodule update --init --recursive

try {
    python myscript.py
    if ($LASTEXITCODE -ne 0) { throw "Python script failed with exit code $LASTEXITCODE" }
} catch {
    Write-Host "Python script failed, but we're continuing anyway: $_"
}
python build.py
