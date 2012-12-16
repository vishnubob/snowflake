#!/usr/bin/python

import boto
from boto.sqs.message import Message
import boto.ec2

import logging
import socket

logging.getLogger('boto').setLevel(logging.CRITICAL)
logging.basicConfig(format="%(asctime)s (%(process)d): %(message)s", level=logging.DEBUG, datefmt='%d/%m/%y %H:%M:%S')
logger = logging.getLogger()

def enable_file_logging():
    logfn = "server_%s.log" % socket.gethostname()
    foh = logging.FileHandler(logfn)
    foh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s (%(process)d): %(message)s', datefmt='%d/%m/%y %H:%M:%S')
    foh.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(foh)

class SnowflakeServer(object):
    SleepCycle = 60

    def __init__(self):
        self.services = SnowflakeServices()
        self.running = True
        self.current_job = None
        self.services.update_state("booting")

    def execute(self, cmd):
        return subprocess.Popen(self.cmd)

    def do_work(self, work):
        self.current_job = self.execute(work)

    def kill_job(self):
        retry = 10
        self.current_job.send_signal(signal.SIGINT)
        # wait a few minues
        while self.current_job.poll() and retry:
            time.sleep(self.SleepCycle)
            retry -= 1
        if not retry:
            self.current_job.kill()

    def check_work(self):
        if not self.current_job:
            return
        if not self.current_job.poll():
            # XXX: log?
            # XXX: clean up?
            self.current_job = None

    def loop(self):
        while self.running:
            self.check_work()
            if self.idle:
                work = self.services.get_work()
                if work:
                    self.do_work(work)
            time.sleep(self.SleepCycle)

class SnowflakeServices(object):
    SimpleDB_Domain = "snowflake_db"
    SimpleQS_Name = "snowflake_queue"

    def __init__(self):
        self.setup_simple_db()
        self.setup_work_queue()

    def ensure(self, func, *args, **kw):
        trycnt = 1
        while not func(*args, **kw):
            msg = "Try #%d to %s failed, retrying in %s seconds.." % (trycnt, func, self.RetryPause)
            logger.debug(msg)
            time.sleep(self.RetryPause)
            trycnt += 1

    def get_this_instance(self):
        conn = boto.ec2.connect_to_region("us-east-1")
        print dir(conn)
        print conn
        reservations = conn.get_all_instances(filters={'instance-id' : 'i-xxxxxxxx'})
        my_instance = reservations[0].instances[0]

    def get_tags(self):
        return self.get_this_instance().tags
        
    def send_work(self, msg):
        m = Message()
        m.set_body(msg)
        self.ensure(self.queue.write, *(m,))
    
    def get_work(self):
        rs = self.queue.get_messages()
        if len(rs) == 0:
            return
        m = rs[0]
        # XXX: no ensure?
        self.queue.delete_message(m)
        return m.get_body()
    
    def setup_work_queue(self):
        conn = boto.connect_sqs()
        queues = conn.get_all_queues()
        for queue in queues:
            if queue.name == self.SimpleQS_Name:
                self.queue = queue
                return
        msg = "Creating SimpleQS queue: %s" % self.SimpleQS_Name
        logger.info(msg)
        self.queue = conn.create_queue(self.SimpleQS_Name)

    def setup_simple_db(self):
        conn = boto.connect_sdb()
        domains = conn.get_all_domains()
        for domain in domains:
            if domain.name == self.SimpleDB_Domain:
                self.domain = domain
                return
        msg = "Creating SimpleDB domain: %s" % self.SimpleDB_Domain
        logger.info(msg)
        self.domain =  conn.create_domain(self.SimpleDB_Domain)

ss = SnowflakeServices()
print ss.get_tags()
