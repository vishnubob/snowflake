#!/usr/bin/env python

import aws
import sys

ss = aws.SnowflakeServices()
job = aws.SnowflakeJob(sys.argv[1])
ss.send_work(job)
