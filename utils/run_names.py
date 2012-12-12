#!/usr/bin/env python
import os
import sys
from multiprocessing import Pool

CMD = "snowflake.py -c -s 600 -M 5000 %s"
def name_snowflake(name):
    cmd = CMD % name
    print cmd
    os.system(cmd)

workers = Pool(3)
f = open(sys.argv[1])
names = [name.strip() for name in f if name.strip()]
workers.map(name_snowflake, names)
