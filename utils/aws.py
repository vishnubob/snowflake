#!/usr/bin/python

import boto
from boto.sqs.message import Message
import boto.ec2
import os
import cPickle as pickle
import subprocess
import shlex

import time
import logging
import socket

HOSTNAME = str.join('_', socket.gethostname().split('.'))
FUSE_MOUNT = "/tmp/snowflake"
SERVER_DIR = "/tmp/snowflake_server"

logging.getLogger('boto').setLevel(logging.CRITICAL)
logging.basicConfig(format="%(asctime)s (%(process)d): %(message)s", level=logging.DEBUG, datefmt='%d/%m/%y %H:%M:%S')
logger = logging.getLogger()

def enable_file_logging():
    logfn = "server_%s.log" % HOSTNAME
    logfn = os.path.join(SERVER_DIR, logfn)
    foh = logging.FileHandler(logfn)
    foh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s (%(process)d): %(message)s', datefmt='%d/%m/%y %H:%M:%S')
    foh.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(foh)

def mount_s3fs(mnt):
    cmd = "s3fs vishnubob_snowflakes %s -ouse_cache=/tmp" % mnt
    os.system(cmd)

def unmount_s3fs(mnt):
    cmd = "fusermount -u %s" % mnt
    os.system(cmd)

def rsync():
    cmd = "rsync -r %s/ %s" % (SERVER_DIR, FUSE_MOUNT)
    os.system(cmd)

class Job(object):
    SleepCycle = 60

    def __init__(self, cmd):
        self.cmd = cmd
        self.proc = None

    def execute(self):
        self.proc = subprocess.Popen(self.cmd)

    def kill_job(self):
        retry = 10
        self.proc.send_signal(signal.SIGINT)
        # wait a few minues
        while (self.proc.poll() == None) and retry:
            time.sleep(self.SleepCycle)
            retry -= 1
        if not retry:
            self.proc.kill()

    def finished(self):
        if self.proc == None:
            return True
        if self.proc.poll() != None:
            # XXX: log?
            # XXX: clean up?
            self.proc = None
            return True
        return False

class UpdateSource(Job):
    def execute(self):
        cwd = os.getcwd()
        try:
            os.chdir("/tmp")
            cmd = "git pull https://github.com/vishnubob/snowflake.git"
            os.system(cmd)
            cmd = "/tmp/snowflake/utils/deploy.sh"
            os.system(cmd)
        finally:
            os.chdir(cwd)

    def post_process(self):
        msg = "Restarting SnowflakeServer"
        logging.warning(msg)
        args = ["python", "python"] + sys.argv
        os.execlp("/usr/bin/env", *args)
        rsync(self.name, FUSE_MOUNT)

class SnowflakeJob(Job):
    Command = "snowflake.py -s %(size)s -c %(name)s -L"

    def __init__(self, name, size=200):
        self.name = name
        self.size = size
        self.proc = None

    def execute(self):
        kw = {"size": self.size, "name": self.name}
        cmd = self.Command % kw
        msg = "Executing %s" % cmd
        logging.debug(msg)
        cmd = shlex.split(cmd)
        self.proc = subprocess.Popen(cmd)

    def post_process(self):
        rsync(self.name, FUSE_MOUNT)

class SnowflakeMaster(object):
    SleepCycle = 60

    def __init__(self):
        self.service = SnowflakeServices()
        self.service.add_queue("snowflake")

    def add_work(self, name):
        job = SnowflakeJob(name)
        self.service.queue_push("snowflake", job)

class SnowflakeServer(object):
    SleepCycle = 10

    def __init__(self):
        self.service = SnowflakeServices()
        self.service.add_queue("snowflake")
        hq = "snowflakehost_%s" % HOSTNAME
        self.service.add_queue(hq)
        self.service.add_queue("snowflake")
        self.running = True
        self.current_job = None
        #self.service.update_state("booting")
        msg = "SnowflakeServer started."
        logger.info(msg)
        self.logger = logger

    def __del__(self):
        hq = "snowflakehost_%s" % HOSTNAME
        try:
            self.service.delete_queue(hq)
        except:
            import traceback
            traceback.print_exc()

    def do_work(self, work):
        msg = "Executing %s" % work
        logger.info(msg)
        self.current_job = work
        self.current_job.execute()

    def check_work(self):
        if not self.current_job:
            return
        if self.current_job.finished():
            msg = "Work finished."
            logger.info(msg)
            self.current_job.post_process()
            self.current_job = None

    def loop(self):
        mount_s3fs(FUSE_MOUNT)
        try:
            while self.running:
                if self.current_job:
                    self.check_work()
                else:
                    msg = "Checking for work."
                    logger.info(msg)
                    work = self.service.queue_pull("snowflake")
                    if work:
                        self.do_work(work)
                time.sleep(self.SleepCycle)
        finally:
            unmount_s3fs(FUSE_MOUNT)

class SnowflakeServices(object):
    SimpleDB_Domain = "snowflake_db"

    def __init__(self):
        self.boto = boto
        self.sqs = boto.connect_sqs()
        self.queues = {}
        self.logger = logger

    def ensure(self, func, *args, **kw):
        trycnt = 1
        while not func(*args, **kw):
            msg = "Try #%d to %s failed, retrying in %s seconds.." % (trycnt, func, self.RetryPause)
            logger.debug(msg)
            time.sleep(self.RetryPause)
            trycnt += 1

    def get_tags(self):
        return self.get_this_instance().tags
        
    def send_message(self, name, obj):
        queue = self.queues[name]
        m = Message()
        m.set_body(pickle.dumps(obj, protocol=-1))
        self.ensure(queue.write, *(m,))
    
    def recv_message_filter(self, name, func):
        queue = self.queues[name]
        rs = queue.get_messages()
        if len(rs) == 0:
            return
        m = rs[0]
        # XXX: no ensure?
        if delete:
            self.delete_message(name, m)
        return pickle.loads(m.get_body())
        
    def recv_message(self, name, delete=True):
        queue = self.queues[name]
        rs = queue.get_messages()
        if len(rs) == 0:
            return
        m = rs[0]
        # XXX: no ensure?
        if delete:
            self.delete_message(name, m)
        return pickle.loads(m.get_body())

    def delete_message(self, name, message):
        queue = self.queues[name]
        self.ensure(queue.delete_message, (message,))
    
    def add_queue(self, name):
        self.update_queue_cache()
        if name not in self.queues:
            self.create_queue(name)
        return self.queues[name]

    def create_queue(self, name):
        self.update_queue_cache()
        if name in self.queues:
            return self.queues[name]
        msg = "Creating SimpleQS queue: %s" % name
        logger.info(msg)
        self.queues[name] = self.sqs.create_queue(name)
        return self.queues[name]

    def delete_queue(self, name):
        if name not in self.queues:
            return 
        queue = self.queues[name]
        queue.clear()
        self.ensure(self.sqs.delete_queue, (queue,))

    def update_queue_cache(self):
        queues = self.sqs.get_all_queues()
        self.queues = {q.name: q for q in queues}

if __name__ == "__main__":
    cwd = os.getcwd()
    if not os.path.exists(SERVER_DIR):
        os.mkdir(SERVER_DIR)
    try:
        enable_file_logging()
        ss = SnowflakeServer()
        ss.loop()
    finally:
        os.chdir(cwd)
