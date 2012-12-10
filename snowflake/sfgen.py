#!/usr/bin/env python
import os
import time

CMD = "./snowflake.py -s 600 -M 5000 -r %s"
cnt = 1
while 1:
    fn = "snowflake_%d" % cnt
    cmd = CMD % fn
    os.system(cmd)
    cnt += 1
    time.sleep(1)
