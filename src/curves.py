#!/usr/bin/env python

import re
import os
from splines import *
from bisect import bisect_left
import random
import math
import sys

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

class Interpolate(object):
    def __init__(self, x_list, y_list, squelch=0):
        self.squelch = squelch
        new_x = [x_list[0]]
        new_y = [y_list[0]]
        last_x = x_list[0]
        for (x, y) in zip(x_list[1:], y_list[1:]):
            if x - last_x < 0:
                continue
            last_x = x
            new_x.append(x)
            new_y.append(y)
        x_list = new_x
        y_list = new_y
        if any(y - x <= 0 for x, y in zip(x_list, x_list[1:])):
            raise ValueError("x_list must be in strictly ascending order!")
        x_list = self.x_list = map(float, x_list)
        y_list = self.y_list = map(float, y_list)
        intervals = zip(x_list, x_list[1:], y_list, y_list[1:])
        self.slopes = [(y2 - y1)/(x2 - x1) for x1, x2, y1, y2 in intervals]

    def __getitem__(self, x):
        i = bisect_left(self.x_list, x) - 1
        return self.y_list[i] + self.slopes[i] * (x - self.x_list[i])

class Curve(object):
    def __init__(self, steps, minval, maxval):
        def sumup(lst):
            if len(lst) <= 1:
                return lst
            return [lst[0]] + sumup([lst[0] + lst[1]] + lst[2:])
        self.minval = minval
        self.maxval = maxval
        self.steps = steps
        self.intervals = random.randint(5, 50)
        weights = [random.random() for x in range(self.intervals)]
        wsum = sum(weights)
        self.xlist = [0] + [int(x / wsum * self.steps) for x in sumup(weights)]
        self.ylist = [(random.random() * (maxval - minval) + minval) for x in self.xlist]
        self.process()

    def build_spline(self, knots):
        ncs = NaturalCubicSpline(tuples2points(knots))
        points = []
        u = 0.0
        du = 0.1
        lim = len(ncs) + du
        while (u < lim):
            p = ncs(u)
            points.append(tuple(p))
            u = u + du
        return points

    def process(self):
        knots = []
        for xy in zip(self.xlist, self.ylist):
            knots.append(xy)
        self.curve = Interpolate(*zip(*self.build_spline(knots)))

    def __getitem__(self, x):
        x %= (self.steps - 1)
        x += 1
        return self.curve[x]

class CurveSet(dict):
    def __init__(self, name, steps, curves):
        self.name = name
        random.seed(name)
        self.steps = steps
        self.curves = curves
        self.process()

    def process(self):
        for cname in self.curves:
            args = self.curves[cname]
            curve = Curve(self.steps, *args)
            self[cname] = curve

    def run_graph(self):
        mod = os.path.splitext(__file__)[0] + '.py'
        cmd = "python %s %s \"%s\" %s" % (mod, self.steps, self.curves, self.name)
        os.system(cmd)

    def plot(self):
        assert PLOTS_ENABLED, "you do not currently have plots enabled."
        fig, axs = plt.subplots(nrows=len(self), ncols=1, sharex=True)
        fig.set_size_inches(10, 25)
        for (idx, key) in enumerate(self):
            ax = axs[idx]
            data = [self[key][x] for x in range(self.steps)]
            ax.plot(data)
            ax.set_xlabel("time (simulation steps)")
            ax.set_ylabel(key)
            ax.set_ylim(self[key].minval, self[key].maxval)
        fn = "%s_runtime.png" % self.name
        plt.savefig(fn)

if __name__ == "__main__":
    name = str.join('', sys.argv[3:])
    curves = eval(sys.argv[2])
    steps = int(sys.argv[1])
    nc = CurveSet(name, steps, curves)
    nc.plot()
