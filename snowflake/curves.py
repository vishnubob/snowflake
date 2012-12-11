#!/usr/bin/env python

import re
import os
from splines import *
from bisect import bisect_left
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
    print "Warning: skipping import of plots (missing a module like matplotlib, pylab)."
    PLOTS_ENABLED = False

class Interpolate(object):
    def __init__(self, x_list, y_list):
        if any(y - x <= 0 for x, y in zip(x_list, x_list[1:])):
            raise ValueError("x_list must be in strictly ascending order!")
        x_list = self.x_list = map(float, x_list)
        y_list = self.y_list = map(float, y_list)
        intervals = zip(x_list, x_list[1:], y_list, y_list[1:])
        self.slopes = [(y2 - y1)/(x2 - x1) for x1, x2, y1, y2 in intervals]

    def __getitem__(self, x):
        i = bisect_left(self.x_list, x) - 1
        return self.y_list[i] + self.slopes[i] * (x - self.x_list[i])

class NameCurve(object):
    MinTemp = -50
    MaxTemp = -30
    MinHum = 0.0
    MaxHum = 0.5
    MaxSteps = 5000

    def __init__(self, name):
        self.name = str.join('', re.split("\s+", name.lower()))
        self.coefs = [ord(ch) - ord('a') for ch in self.name]
        self.hum_phase = sum(self.coefs)
        self.temp_phase = int(round(sum(self.coefs) / len(self.coefs)))
        self.hum_steps = ((self.MaxSteps + self.MaxSteps * (self.hum_phase / 200.0))) / (len(self.name) - 1)
        self.temp_steps = ((self.MaxSteps + self.MaxSteps * (1.0 / self.temp_phase))) / (len(self.name) - 1)
        self.temp_map = Interpolate((0, 25), (self.MinTemp, self.MaxTemp))
        self.hum_map = Interpolate((0, 25), (self.MinHum, self.MaxHum))
        self.process()

    def get_temperature(self, step):
        return self.temp_curve[step]

    def get_humidity(self, step):
        return self.hum_curve[step]

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
        hum_knots = []
        temp_knots = []
        hum_steps = 0
        temp_steps = 0
        for ch_val in self.coefs:
            hum_knots.append((hum_steps, self.hum_map[(ch_val + self.hum_phase) % 26]))
            temp_knots.append((temp_steps, self.temp_map[(ch_val + self.temp_phase) % 26]))
            hum_steps += self.hum_steps
            temp_steps += self.temp_steps
        self.hum_curve = Interpolate(*zip(*self.build_spline(hum_knots)))
        self.temp_curve = Interpolate(*zip(*self.build_spline(temp_knots)))

    def run_graph(self):
        mod = os.path.splitext(__file__)[0] + '.py'
        cmd = "python %s %s" % (mod, self.name)
        print cmd
        os.system(cmd)
            
    def graph(self, fn):
        fig = plt.figure()
        ax1 = fig.add_subplot(1, 1, 1)
        ax1.plot([self.hum_curve[x] for x in range(self.MaxSteps)], 'r')
        ax1.set_ylim(0, 1)
        ax1.set_xlabel("steps")
        ax1.set_ylabel("humidity", color='r')
        for tl in ax1.get_yticklabels():
            tl.set_color('r')
        ax2 = ax1.twinx()
        ax2.plot([self.temp_curve[x] for x in range(self.MaxSteps)], 'b')
        ax2.set_ylabel("temp", color='b')
        ax2.set_ylim(-20, -60)
        for tl in ax2.get_yticklabels():
            tl.set_color('b')
        plt.title(self.name)
        plt.savefig(fn)

if __name__ == "__main__":
    name = str.join('', sys.argv[1:])
    nc = NameCurve(sys.argv[1])
    nc.graph(name + "_plot.png")
