#!/bin/bash

# determine if we are on XF OS or not
if test -d "/opt/App/.venv3.12"; then
    py_ex="/opt/App/.venv3.12/bin/python3.12"
elif test -d "/opt/App/.venv3.8"; then
    py_ex="/opt/App/.venv3.8/bin/python3.8"
else
    py_ex="/usr/bin/python3.6"
fi


cd /usr/local/share/nmkivy

$py_ex main-nm.py
