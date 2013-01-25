import logging
import math
import os

SNOWFLAKE_INI = os.path.join(os.path.split(__file__)[0], "etc", "snowflake.ini")
logging.basicConfig(format="%(asctime)s (%(process)d): %(message)s", level=logging.DEBUG, datefmt='%d/%m/%y %H:%M:%S')
log = logging.info

X_SCALE_FACTOR = (1.0 / math.sqrt(3))

def log_output(name):
    logfn = "%s.log" % name
    foh = logging.FileHandler(logfn)
    foh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s (%(process)d): %(message)s', datefmt='%d/%m/%y %H:%M:%S')
    foh.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(foh)

from curves import *
from graphics import *
from engine import *
