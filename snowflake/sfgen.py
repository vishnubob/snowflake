#!/usr/bin/env python
import os
import time
import uuid

CMD = "./snowflake.py -s 600 -M 5000 -r %s"
while 1:
    _id = str(uuid.uuid1()).split('-')[0]
    fn = "snowflake_%s" % _id
    cmd = CMD % fn
    os.system(cmd)
    cnt += 1
    time.sleep(1)
