#!/bin/bash

# determine if we are on XF OS or not
if test -d "/opt/App/.venv3.12"; then
    py_ex="/opt/App/.venv3.12/bin/python3.12"
elif test -d "/opt/App/.venv3.8"; then
    py_ex="/opt/App/.venv3.8/bin/python3.8"
else
    py_ex="/usr/bin/python3.6"
fi


#we must kill btp as Kivy is a bit borg-ish about multiple windows
# we kill everything that's running the btp stuff
pkill -f $py_ex

cd /usr/local/share/nmkivy

$py_ex main.py
