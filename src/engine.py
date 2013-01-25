#!/usr/bin/env pypy

import random
import math
import argparse
import cPickle as pickle
import logging
import os
import sys
import re
import colorsys
import bisect
import operator
from xml.dom.minidom import parse

InkscapePath = "/Applications/Inkscape.app/Contents/Resources/bin/inkscape"

try:
    import Image
    import ImageDraw
except ImportError:
    from PIL import Image
    from PIL import ImageDraw

# local
from sfgen import *
sys.modules["curves"] = curves

def avg_stdev(data):
    avg = sum(data) / float(len(data))
    stdev = math.sqrt(sum((x - avg) ** 2 for x in data) / float(len(data)))
    return (avg, stdev)

class CrystalEnvironment(dict):
    def __init__(self, curves=None, **kw):
        self.curves = curves
        self._init_defaults()
        self.update(**kw)
        self.set_factory_settings()

    def set_factory_settings(self):
        self.factory_settings = self.copy()

    def __getattr__(self, name):
        if name not in self:
            return AttributeError, "no such thing brah: %s" % name
        return self[name]

    def __getnewargs__(self):
        return ()

    def __getstate__(self):
        return (self.curves, self.factory_settings, dict(self))

    def __setstate__(self, state):
        if type(state) == dict:
            self.update(state)
            self.curves = None
            self.set_factory_settings()
        else:
            self.curves = state[0]
            self.factory_settings = state[1]
            self.update(state[2])

    def step(self, x):
        if self.curves == None:
            return
        for key in self.curves:
            self[key] = self.curves[key][x]

    @classmethod
    def build_env(self, name, steps, min_gamma=0.45, max_gamma=0.85):
        curves = {
            "beta": (1.3, 2),
            "theta": (0.01, 0.04),
            "alpha": (0.02, 0.1),
            "kappa": (0.001, 0.01),
            "mu": (0.01, 0.1),
            "upilson": (0.00001, 0.0001),
            "sigma": (0.00001, 0.000001),
        }
        cs = CurveSet(name, steps, curves)
        cs.run_graph()
        env = {key: cs[key][0] for key in curves}
        env["gamma"] = random.random() * (max_gamma - min_gamma) + min_gamma
        return CrystalEnvironment(curves=cs, **env)

    def get_default(self, key):
        return self.factory_settings[key]

    def randomize(self):
        for key in self:
            if key == "sigma":
                continue
            if key == "gamma":
                self[key] += 1.0 / random.randint(100, 1000)
            else:
                self[key] += random.choice([1.0, -1.0]) / random.randint(100, 1000)
        self.set_factory_settings()

    def _init_defaults(self):
        # (3a) 
        # "A boundary site with 1 or 2 attached neighbors needs boundary mass at least beta to join the crystal
        #  This is the case when the local mesoscopic geometry near x corresponds to a tip or flat spot of the crystal. 
        #  (Distinguishing the two cases turns out to be of minor significance.) In our simulations, beta is typically 
        #  between about 1.05 and 3. We assume beta > 1 since 1 is the basic threshold of the case to follow next.
        self["beta"] = 1.3

        # (3b)
        # "A boundary site with 3 attached neighbors joins the crystal if either it has boundary mass >= 1, 
        #  or it has diffusive mass < theta in its neighborhood and it has boundary mass >= alpha"
        self["theta"] = 0.025
        self["alpha"] = 0.08

        # (2) 
        # "Proportion kappa of the diffusive mass at each boundary site crystallizes. 
        #  The remainder (proportion 1 - kappa) becomes boundary mass."
        self["kappa"] = 0.003

        # (4)
        # "Proportion mu of the boundary mass and proportion upsilon of the crystal mass at each boundary site become diffusive mass. 
        #  Melting represents mass flow at the boundary from ice and quasi-liquid back to vapor, reverse
        #  effects from the freezing of step ii. Typically mu is small and upsilon extremely small."
        self["mu"] = 0.07
        self["upsilon"] = 0.00005

        # (5)
        # "The diffusive mass at each site undergoes an independent random perturbation of proportion sigma"
        self["sigma"] = 0.00001

        # initial diffusion
        self["gamma"] = 0.5

	def _init_special(self):
		pass

class RenderMovie(object):
    def __init__(self, name):
        self.name = name
        self.replay = LatticeReplay(name)

    def run(self):
        if not os.path.exists("frames"):
            os.mkdir("frames")
        x = iter(self.replay)
        for (idx, frame) in enumerate(self.replay):
            fn = "frames/%s_%09d.png" % (self.name, idx + 1)
            frame.save_image(fn)

class LatticeReplay(object):
    class ReplayIterator(object):
        def __init__(self, replay):
            self.replay = replay
            self.idx = 0

        def next(self):
            try:
                lattice = self.replay.get_lattice(self.idx)
                self.idx += 1
                return lattice
            except IndexError:
                raise StopIteration

    def __init__(self, name):
        self.name = name
        self.current_frame = None
        self.current_replay = None
        pfn = "%s.pickle" % self.name
        self.lattice = CrystalLattice.load_lattice(pfn)
        self.scan_replays()

    def __iter__(self):
        return self.ReplayIterator(self)

    def get_lattice(self, step):
        (step, dm, cm) = self.get_step(step)
        for (idx, cell) in enumerate(zip(dm, cm)):
            self.lattice.cells[idx].diffusive_mass = cell[0]
            self.lattice.cells[idx].crystal_mass = cell[1]
            self.lattice.cells[idx].attached = bool(cell[1])
        for cell in self.lattice.cells:
            cell.update_boundary()
        return self.lattice

    def get_step(self, step):
        idx = bisect.bisect_left(self.replay_map, step + 1)
        if self.current_frame != idx or not self.current_replay:
            self.current_frame = idx
            fn = self.replays[self.current_frame]
            print "loading", fn
            f = open(fn)
            self.current_replay = pickle.load(f)
        offset = self.current_replay[0][0]
        return self.current_replay[step - offset]

    def scan_replays(self):
        replays = []
        fn_re = re.compile("cell_log_(\d+).pickle")
        for fn in os.listdir('.'):
            m = fn_re.search(fn)
            if m:
                step = int(m.group(1))
                replays.append((fn, step))
        replays.sort(key=operator.itemgetter(1))
        self.replays = [rp[0] for rp in replays]
        self.replay_map = [rp[1] for rp in replays]

class CrystalLattice(object):
    LogHeader = ["dm", "cm", "bm", "acnt", "bcnt", "width", "beta", "theta", "alpha", "kappa", "mu", "upsilon"]

    def __init__(self, size, environment=None, celltype=None, max_steps=0, margin=None, curves=None, datalog=False, debug=False):
        self.size = size
        if environment == None:
            environment = CrystalEnvironment()
        self.environment = environment
        self.datalog = None
        self.celllog = None
        if datalog:
            self.datalog = []
            self.celllog = []
        if celltype == None:
            celltype = SnowflakeCell
        self.debug = debug
        self.celltype = celltype
        self.iteration = 1
        assert margin > 0 and margin <= 1.0
        self.margin = margin
        self.curves = curves
        self.max_steps = max_steps
        self._init_cells()

    def __setstate__(self, state):
        # 0.1->0.2 format changes
        if "radius" in state:
            state["size"] = state["radius"]
            del state["radius"]
        if "angle" in state:
            del state["angle"]
        self.__dict__.update(state)

    def save_lattice(self, fn):
        msg = "Saving %s..." % fn
        log(msg)
        f = open(fn, 'wb')
        pickle.dump(self, f, protocol=-1)

    @classmethod
    def load_lattice(cls, fn):
        msg = "Loading %s..." % fn
        log(msg)
        f = open(fn, 'rb')
        obj = pickle.load(f)
        for cell in obj.cells:
            cell.lattice = obj
            cell.env = obj.environment
            cell.update_boundary()
        return obj

    def get_neighbors(self, xy):
        (x, y) = xy
        nlist = [(x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y), (x - 1, y - 1), (x + 1, y + 1)]
        nlist = map(self._cell_index, filter(self._xy_ok, nlist))
        res = tuple([self.cells[nidx] for nidx in nlist if self.cells[nidx] != None])
        return res

    def reality_check(self):
        for cell in self.cells:
            cell.reality_check()

    def _init_cells(self):
        self.cells = [None] * (self.size * self.size)
        for x in range(self.size):
            for y in range(self.size):
                xy = (x, y)
                cell = self.celltype(xy, self)
                idx = self._cell_index(xy)
                self.cells[idx] = cell
        self.reality_check()
        center_pt = self._cell_index((self.size / 2, self.size / 2))
        self.cells[center_pt].attach(1)
        # fun experiments
        #self.cells[center_pt+4].attach(1)
        #self.cells[center_pt-4].attach(1)

    def _xy_ok(self, xy):
        (x, y) = xy
        return (x >= 0 and x < self.size and y >= 0 and y < self.size)

    def _cell_index(self, xy):
        (x, y) = xy
        return int(round(y * self.size + x))

    def _cell_xy(self, idx):
        y = idx / self.size
        x = idx % self.size
        return (x, y)

    def adjust_humidity(self, val):
        val = abs(val)
        for cell in self.cells:
            if cell.attached or cell.boundary:
                continue
            cell.diffusive_mass += val * self.environment.sigma
            # only mutate the cells outside our margin
            #if self.xy_to_polar(cell.xy)[1] > (self.size * self.margin):
                # we use the same coef as the noise coef
                #cell.diffusive_mass += val * self.environment.sigma
    
    def log_status(self):
        if self.datalog == None:
            return
        row = []
        #row.append(self.iteration)
        dm = [cell.diffusive_mass for cell in self.cells if cell]
        row.append(sum(dm))
        cm = [cell.crystal_mass for cell in self.cells if cell]
        row.append(sum(cm))
        bm = [cell.boundary_mass for cell in self.cells if cell]
        row.append(sum(bm))
        acnt = len([cell for cell in self.cells if cell and cell.attached])
        row.append(acnt)
        bcnt = len([cell for cell in self.cells if cell and cell.boundary])
        row.append(bcnt)
        d = self.snowflake_radius()
        row.append(d)
        row.append(self.environment.beta)
        row.append(self.environment.theta)
        row.append(self.environment.alpha)
        row.append(self.environment.kappa)
        row.append(self.environment.mu)
        row.append(self.environment.upsilon)
        #row.append(self.environment.sigma)
        #row.append(self.environment.gamma)
        self.datalog.append(row)
        # log the cells
        self.celllog.append((self.iteration, dm, cm))

    def write_log(self):
        self.write_datalog()
        self.write_celllog()

    def write_datalog(self):
        if self.datalog == None:
            return
        logfn = "datalog.csv"
        msg = "Saving runtime data to %s" % logfn
        log(msg)
        f = open(logfn, 'w')
        txt = ''
        txt += str.join(',', self.LogHeader) + '\n'
        for row in self.datalog:
            txt += str.join(',', map(str, row)) + '\n'
        f.write(txt)

    def write_celllog(self):
        if not self.celllog:
            return
        logfn = "cell_log_%d.pickle" % self.iteration
        f = open(logfn, 'wb')
        pickle.dump(self.celllog, f, protocol=-1)
        self.celllog = []

    def print_status(self):
        dm = sum([cell.diffusive_mass for cell in self.cells if cell])
        cm = sum([cell.crystal_mass for cell in self.cells if cell])
        bm = sum([cell.boundary_mass for cell in self.cells if cell])
        acnt = len([cell for cell in self.cells if cell and cell.attached])
        bcnt = len([cell for cell in self.cells if cell and cell.boundary])
        #msg = "Step #%d, %d attached, %d boundary, %.2f dM, %.2f bM, %.2f cM, tot %.2f M" % (self.iteration, acnt, bcnt, dm, bm, cm, dm + cm + bm)
        d = self.snowflake_radius()
        msg = "Step #%d/%dp (%.2f%% scl), %d/%d (%.2f%%), %.2f dM, %.2f bM, %.2f cM, tot %.2f M" % (self.iteration, d, (float(d * 2 * X_SCALE_FACTOR) / self.iteration) * 100, acnt, bcnt, (float(bcnt) / acnt) * 100, dm, bm, cm, dm + cm + bm)
        log(msg)

    def step(self):
        self.log_status()
        for cell in self.cells:
            if cell == None or cell.attached:
                continue
            cell.step_one()
        for cell in self.cells:
            if cell == None or cell.attached:
                continue
            cell.step_two()
        for cell in self.cells:
            if cell == None or cell.attached:
                continue
            cell.step_three()
        # run curves
        self.iteration += 1
        self.environment.step(self.iteration)

    def translate_xy(self, xy):
        (x, y) = xy
        x = int(round(x * X_SCALE_FACTOR))
        return (x, y)

    def polar_to_xy(self, args):
        (angle, distance) = args
        half = self.size / 2.0
        angle = math.radians(angle)
        y = int(round(half - (math.sin(angle) * distance)))
        x = int(round(half + (math.cos(angle) * distance)))
        return (x, y)

    def xy_to_polar(self, args):
        (x, y) = args
        half = self.size / 2.0
        x -= half
        y += half
        angle = math.degrees(math.atan2(y, x))
        distance = math.hypot(x, y)
        return (angle, distance)

    def snowflake_radius(self, angle=135):
        # we cast a ray on the 135 degeree axis
        radius = 0
        half = self.size / 2.0
        while radius < half:
            radius += 1
            xy = self.polar_to_xy((angle, radius))
            cell = self.cells[self._cell_index(xy)]
            if cell.attached or cell.boundary:
                continue
            return radius
        # uhh
        return int(round(half))

    def crop_snowflake(self, margin=None):
        def scale(val):
            return int(round(X_SCALE_FACTOR * val))
        if margin == None:
            margin = 15
        half = self.size / 2
        radius = scale(self.snowflake_radius())
        distance = min(radius + margin, half)
        half_s = scale(half)
        distance_s = scale(distance)
        box = (half_s - distance, half - distance, half_s + distance, half + distance)
        return box

    def headroom(self, margin=None):
        if self.max_steps and self.iteration >= self.max_steps:
            return False
        if margin == None:
            margin = self.margin
        assert margin > 0 and margin <= 1
        cutoff = int(round(margin * (self.size / 2.0)))
        radius = self.snowflake_radius()
        if radius > cutoff:
            return False
        return True

    def grow(self):
        while True:
            if self.debug:
                self.print_status()
            self.step()
            if self.iteration % 50 == 0:
                self.write_celllog()
                if not self.debug:
                    self.print_status()
                if not self.headroom():
                    break
        if self.debug:
            self.print_status()

    def save_image(self, fn, **kw):
        import sfgen
        r = sfgen.RenderSnowflake(self)
        r.save_image(fn, **kw)

class SnowflakeCell(object):
    def __init__(self, xy, lattice):
        self.xy = xy
        self.lattice = lattice
        self.env = lattice.environment
        self.diffusive_mass = self.env.gamma
        self.boundary_mass = 0.0
        self.crystal_mass = 0.0
        self.attached = False
        self.age = 0
        self.boundary = 0
        self.attached_neighbors = []
        self.__neighbors = None

    def __getstate__(self):
        return (self.xy, self.diffusive_mass, self.boundary_mass, self.crystal_mass, self.attached, self.age)

    def __setstate__(self, state):
        self.xy = state[0]
        self.diffusive_mass = state[1]
        self.boundary_mass = state[2]
        self.crystal_mass = state[3]
        self.attached = state[4]
        # 0.2 -> 0.3
        try:
            self.age = state[5]
        except IndexError:
            self.age = 0
        self.__neighbors = None
        self.lattice = None
        self.env = None

    def reality_check(self):
        assert len(self.neighbors)
        for neighbor in self.neighbors:
            assert self in neighbor.neighbors, "%s not in %s" % (str(self), str(neighbor.neighbors))

    def __repr__(self):
        return "(%d,%d)" % self.xy

    @property
    def neighbors(self):
        if self.__neighbors == None:
            self.__neighbors = self.lattice.get_neighbors(self.xy)
        return self.__neighbors
    
    #@property
    #def attached_neighbors(self):
    #    return [cell for cell in self.neighbors if cell.attached]

    #@property
    #def boundary(self):
    #    return (not self.attached) and any([cell.attached for cell in self.neighbors])

    def update_boundary(self):
        self.boundary = (not self.attached) and any([cell.attached for cell in self.neighbors])

    def step_one(self):
        self.update_boundary()
        if self.boundary:
            self.attached_neighbors = [cell for cell in self.neighbors if cell.attached]
        self._next_dm = self.diffusion_calc()

    def step_two(self):
        self.diffusive_mass = self._next_dm
        self.attachment_flag = self.attached
        self.freezing_step()
        self.attachment_flag = self.attachment_step()
        self.melting_step()

    def step_three(self):
        if self.boundary and self.attachment_flag:
            self.attach()
        self.noise_step()

    def diffusion_calc(self):
        next_dm = self.diffusive_mass
        if self.attached:
            return next_dm
        self.age += 1
        for cell in self.neighbors:
            if cell.attached:
                next_dm += self.diffusive_mass
            else:
                next_dm += cell.diffusive_mass
        return float(next_dm) / (len(self.neighbors) + 1)

    def attach(self, offset=0.0):
        self.crystal_mass = self.boundary_mass + self.crystal_mass + offset
        self.boundary_mass = 0
        self.attached = True

    def freezing_step(self):
        if not self.boundary:
            return
        self.boundary_mass += (1 - self.env.kappa) * self.diffusive_mass
        self.crystal_mass += (self.env.kappa * self.diffusive_mass)
        self.diffusive_mass = 0

    def attachment_step(self):
        if not self.boundary:
            return False
        attach_count = len(self.attached_neighbors)
        if attach_count <= 2:
            if self.boundary_mass > self.env.beta:
                return True
        elif attach_count == 3:
            if self.boundary_mass >= 1:
                return True
            else:
                summed_diffusion = self.diffusive_mass
                for cell in self.neighbors:
                    summed_diffusion += cell.diffusive_mass
                if summed_diffusion < self.env.theta and self.boundary_mass >= self.env.alpha:
                    return True
        elif attach_count >= 4:
            return True
        return False
    
    def melting_step(self):
        if not self.boundary:
            return
        self.diffusive_mass += self.env.mu * self.boundary_mass + self.env.upsilon * self.crystal_mass
        self.boundary_mass = (1 - self.env.mu) * self.boundary_mass
        self.crystal_mass = (1 - self.env.upsilon) * self.crystal_mass

    def noise_step(self):
        if (self.boundary or self.attached):
            return
        if random.random() >= .5:
            self.diffusive_mass = (1 - self.env.sigma) * self.diffusive_mass
        else:
            self.diffusive_mass = (1 + self.env.sigma) * self.diffusive_mass

def check_basecut(svgfn):
    # ensure there is only one path
    svg = parse(svgfn)
    for (cnt, node) in enumerate(svg.getElementsByTagName("path")):
        if cnt > 0:
            return False
    return True

def merge_svg(file_list, color_list, outfn):
    first = None
    idx = 0
    for (svgfn, color) in zip(file_list, color_list):
        svg = parse(svgfn)
        for node in svg.getElementsByTagName("g"):
            if idx == 0:
                # write a new group
                container = svg.createElement("g")
                container.setAttribute("transform", node.attributes["transform"].nodeValue)
                node.parentNode.replaceChild(container, node)
                container.appendChild(node)
                node.attributes["fill"] = "none"
                node.attributes["stroke"] = "#ff0000"
                node.attributes["stroke-width"] = ".1"
            else:
                node.attributes["fill"].nodeValue = color
            del node.attributes["transform"]
            idx += 1
            import_nodes = svg.importNode(node, True)
            container.appendChild(import_nodes)
            if first == None:
                first = svg
    f = open(outfn, 'w')
    f.write(first.toxml())

def potrace(svgfn, fn, turd=None):
    if turd:
        # "turd" supression, important for the cut layer
        cmd = "potrace -i -b svg -t %s -o %s %s" % (turd, svgfn, fn)
    else:
        cmd = "potrace -i -b svg -o %s %s" % (svgfn, fn)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)

# laser cutter pipeline
def pipeline_lasercutter(args, lattice, inches=3, dpi=96, turd=10):
    # layers
    rs = RenderSnowflake(lattice)
    name = str.join('', [c for c in args.name if c.islower()])
    layerfn = "%s_layer_%%d.bmp" % name
    resize = inches * dpi
    fnlist = rs.save_layers(layerfn, 2, resize=resize, margin=1)
    # we want to drop the heaviest layer
    del fnlist[0]
    # try to save o'natural
    imgfn = "%s_bw.bmp" % name
    svgfn = "%s_bw.svg" % name
    lattice.save_image(imgfn, scheme=BlackWhite(lattice), resize=resize, margin=1)
    potrace(svgfn, imgfn, turd=2000)
    if not check_basecut(svgfn):
        msg = "There are disconnected elements in the base cut, turning on boundary layer."
        log(msg)
        lattice.save_image(imgfn, scheme=BlackWhite(lattice, boundary=True), resize=resize, margin=1)
        potrace(svgfn, imgfn, turd=2000)
        assert check_basecut(svgfn), "Despite best efforts, base cut is still non-contiguous."
    os.unlink(svgfn)
    fnlist.insert(0, imgfn)
    colors = ["#ff0000", "#00ff00", "#0000ff", "#ff00ff", "#ffff00", "#00ffff"]
    svgs = []
    for (idx, fn) in enumerate(fnlist):
        svgfn = os.path.splitext(fn)[0]
        svgfn = "%s_laser.svg" % svgfn
        svgs.append(svgfn)
        if idx == 0:
            potrace(svgfn, fn, turd=turd)
        else:
            potrace(svgfn, fn)
    svgfn = "%s_laser_merged.svg" % name
    epsfn = "%s_laser_merged.eps" % name
    merge_svg(svgs, colors, svgfn)
    # move to eps
    cmd = "%s %s -E %s" % (InkscapePath, svgfn, epsfn)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)

# 3d pipeline
def pipeline_3d(args, lattice, inches=3, dpi=96, turd=10):
    resize = inches * dpi
    # try to save o'natural
    imgfn = "%s_bw.bmp" % args.name
    svgfn = "%s_bw.svg" % args.name
    lattice.save_image(imgfn, scheme=BlackWhite(lattice), resize=resize, margin=1)
    potrace(svgfn, imgfn, turd=2000)
    if not check_basecut(svgfn):
        msg = "There are disconnected elements in the base cut, turning on boundary layer."
        log(msg)
        lattice.save_image(imgfn, bw=True, boundary=True)
        potrace(svgfn, imgfn, turd=2000)
        assert check_basecut(svgfn), "Despite best efforts, base cut is still non-contiguous."
    #
    epsfn = "%s_3d.eps" % args.name
    dxffn = "%s_3d.dxf" % args.name
    cmd = "potrace -M .1 --tight -i -b eps -o %s %s" % (epsfn, imgfn)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)
    #
    cmd = "pstoedit -dt -f dxf:-polyaslines %s %s" % (epsfn, dxffn)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)
    #
    scad_fn = "%s_3d.scad" % args.name
    stlfn = "%s_3d.stl" % args.name
    f = open(scad_fn, 'w')
    scad_txt = 'scale([30, 30, 30]) linear_extrude(height=.18, layer="0") import("%s");\n' % dxffn
    f.write(scad_txt)
    f.close()
    cmd = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD -o %s %s" % (stlfn, scad_fn)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)
    #
    cmd = "python /Applications/Cura/Cura.app/Contents/Resources/Cura/cura.py -s %s -i %s" % (stlfn, SNOWFLAKE_INI)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)

SNOWFLAKE_DEFAULTS = {
    "size": 200,
    "name": "snowflake",
    "bw": False,
    "env": '',
    "pipeline_3d": False,
    "pipeline_lasercutter": False,
    "randomize": False,
    "max_steps": 0,
    "margin": .85,
    "curves": False,
    "datalog": False,
    "debug": False,
    "movie": False,
}

def run(args):
    log_output(args.name)
    msg = "Snowflake Generator v0.3"
    log(msg)
    pfn = "%s.pickle" % args.name
    ifn = "%s.png" % args.name
    if os.path.exists(pfn):
        cl = CrystalLattice.load_lattice(pfn)
        #cl.save_image(ifn, bw=args.bw)
        #cl.save_image(ifn)
    else:
        kw = {}
        if args.env:
            mods = {key: float(val) for (key, val) in [keyval.split('=') for keyval in args.env.split(',')]}
            env = CrystalEnvironment(mods)
            kw["environment"] = env
        elif args.randomize:
            env = CrystalEnvironment()
            env.randomize()
            msg = str.join(', ', ["%s=%.6f" % (key, env[key]) for key in env])
            log(msg)
            kw["environment"] = env
        elif args.curves:
            env = CrystalEnvironment.build_env(args.name, 50000)
            kw["environment"] = env
        kw["max_steps"] = args.max_steps
        kw["margin"] = args.margin
        kw["datalog"] = args.datalog
        kw["debug"] = args.debug
        cl = CrystalLattice(args.size, **kw)
        try:
            cl.grow()
        finally:
            cl.write_log()
            cl.save_lattice(pfn)
            #cl.save_image(ifn, bw=args.bw)
            cl.save_image(ifn)
    if args.pipeline_3d:
        pipeline_3d(args, cl)
    if args.pipeline_lasercutter:
        pipeline_lasercutter(args, cl)
    if args.movie:
        movie = RenderMovie(args.name)
        movie.run()
