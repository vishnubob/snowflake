#!/bin/sh

git pull
$HOME/local/pypy/bin/pypy setup.py install
$HOME/local/python/bin/python setup.py install
