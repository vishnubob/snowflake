#!/usr/bin/env python
import os

CMD = "./snowflake.py -n %s -s 600 -M 5000 -r"
cnt = 1
while 1:
    fn = "snowflake_%d" % cnt
    cmd = CMD % fn
    os.system(cmd)
    cnt += 1
