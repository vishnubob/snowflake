#!/usr/bin/env python

import argparse
import os

# matplotlib
PLOTS_ENABLED = True
try:
    import matplotlib
    matplotlib.use('AGG')
    import numpy as np
    import matplotlib.mlab as mlab
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import pylab
except ImportError:
    PLOTS_ENABLED = False

class DataPlotter(list):
    def __init__(self, args):
        self.name = args.name
        self.load()

    def load(self):
        fn = "datalog.csv"
        f = open(fn)
        hdr = f.readline()
        hdr = hdr.strip()
        self.hdr = hdr.split(',')
        for line in f:
            line = line.strip()
            row = line.split(',')
            self.append(row)

    def plot(self):
        assert PLOTS_ENABLED, "You do not currently have plots enabled."
        fig, axs = plt.subplots(nrows=len(self.hdr), ncols=1, sharex=True)
        fig.set_size_inches(10, 25)
        #plt.title(self.name)
        for (idx, key) in enumerate(self.hdr):
            ax = axs[idx]
            data = [row[idx] for row in self]
            ax.plot(data)
            ax.set_xlabel("Time (simulation steps)")
            ax.set_ylabel(key)
        fn = "%s_rundata.png" % self.name
        plt.savefig(fn)


DEFAULTS = {
    "name": "snowflake",
}

def get_cli():
    parser = argparse.ArgumentParser(description='Snowflake Generator.')
    parser.add_argument(dest="name", nargs='+', help="The name of the snowflake.")

    parser.set_defaults(**DEFAULTS)
    args = parser.parse_args()
    args.name = str.join('', map(str.lower, args.name))
    return args

if __name__ == "__main__":
    args = get_cli()
    os.chdir(args.name)
    try:
        dp = DataPlotter(args)
        dp.plot()
    finally:
        os.chdir('..')
