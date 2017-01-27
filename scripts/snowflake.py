#!/usr/bin/env pypy

import os
import sys
from sfgen import *

def ensure_python():
    # pylab doesn't play well with pypy
    # so this will cause us to re-exec if
    # we are in pypy ... do not use if you want pypy
    if sys.subversion[0] == "PyPy":
        msg = "Restarting within CPython environment to accomdate scipy/numpy"
        logging.warning(msg)
        args = ["/usr/local/bin/python", "python"] + sys.argv
        #os.execlp("/usr/bin/env", *args)
        print args
        os.execlp(*args)


def get_cli():
    parser = argparse.ArgumentParser(description='Snowflake Generator.')
    parser.add_argument(dest="name", nargs='+', help="The name of the snowflake.")
    parser.add_argument('-s', '--size', dest="size", type=int, help="The size of the snowflake.")
    parser.add_argument('-e', '--env', dest='env', help='comma seperated key=val env overrides')
    parser.add_argument('-b', '--bw', dest='bw', action='store_true', help='write out the image in black and white')
    parser.add_argument('-r', '--randomize', dest='randomize', action='store_true', help='randomize environment.')
    parser.add_argument('-x', '--extrude', dest='pipeline_3d', action='store_true', help='Enable 3d pipeline.')
    parser.add_argument('-l', '--laser', dest='pipeline_lasercutter', action='store_true', help='Enable Laser Cutter pipeline.')
    parser.add_argument('-M', '--max-steps', dest='max_steps', type=int, help='Maximum number of iterations.')
    parser.add_argument('-m', '--margin', dest='margin', type=float, help='When to stop snowflake growth (between 0 and 1)')
    parser.add_argument('-c', '--curves', dest='curves', action='store_true', help='run name as curves')
    parser.add_argument('-L', '--datalog', dest='datalog', action='store_true', help='Enable step wise data logging.')
    parser.add_argument('-D', '--debug', dest='debug', action='store_true', help='Show every step.')
    parser.add_argument('-V', '--movie', dest='movie', action='store_true', help='Render a movie.')
    parser.add_argument('-W', '--width', dest='width', type=float, help="Width of target render.")
    parser.add_argument('-H', '--height', dest='height', type=float, help="Height of target render.")

    parser.set_defaults(**SNOWFLAKE_DEFAULTS)
    args = parser.parse_args()
    args.name = str.join('', map(str.lower, args.name))
    args.target_size = None
    if args.width and args.height:
        args.target_size = (args.width, args.height)
    if args.name[-1] == '/':
        # wart from the shell
        args.name = args.name[:-1]
    if not os.path.exists(args.name):
        os.mkdir(args.name)
    if args.pipeline_lasercutter:
        ensure_python()
    if args.pipeline_3d:
        args.bw = True
    if args.pipeline_3d or args.pipeline_lasercutter:
        ensure_python()
    return args

if __name__ == "__main__":
    args = get_cli()
    os.chdir(args.name)
    try:
        run(args)
    finally:
        os.chdir('..')
