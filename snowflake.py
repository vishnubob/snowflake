#!/usr/bin/env pypy

import random
import math
import argparse
import cPickle as pickle
import logging
import os

import Image
import ImageDraw

logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.DEBUG)
log = logging.info

def polar_to_xy(args):
    (angle, distance) = args
    angle = math.radians(angle)
    y = int(round(math.sin(angle) * distance))
    x = int(round(math.cos(angle) * distance))
    return (x, y)

def xy_to_polar(args):
    (x, y) = args
    angle = math.degrees(math.atan2(y, x))
    distance = math.hypot(x, y)
    return (angle, distance)

class CrystalEnvironment(dict):
    def __init__(self, *args, **kw):
        self._init_defaults()
        self.update(*args, **kw)

    def __getattr__(self, name):
        return self[name]

    def __getstate__(self):
        return dict(self)

    def __setstate__(self, state):
        self.update(state)

    def randomize(self):
        for key in self:
            self[key] += (random.choice([1, -1]) * (random.random() / random.randint(10, 1000)))

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
        self["sigma"] = 0

        # initial diffusion
        self["gamma"] = 0.5

class CrystalLattice(object):
    def __init__(self, size, environment=None, celltype=None, max_steps=0):
        self.size = size
        if environment == None:
            environment = CrystalEnvironment()
        self.environment = environment
        if celltype == None:
            celltype = SnowflakeCell
        self.celltype = celltype
        self.iteration = 1
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
        f = open(fn, 'w')
        pickle.dump(self, f)

    @classmethod
    def load_lattice(cls, fn):
        msg = "Loading %s..." % fn
        log(msg)
        f = open(fn)
        obj = pickle.load(f)
        for cell in obj.cells:
            cell.lattice = obj
            cell.env = obj.environment
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

    def _xy_ok(self, xy):
        (x, y) = xy
        return (x >= 0 and x < self.size and y >= 0 and y < self.size)

    def _cell_index(self, xy):
        (x, y) = xy
        return y * self.size + x

    def _cell_xy(self, idx):
        y = idx / self.size
        x = idx % self.size
        return (x, y)

    def print_status(self):
        dm = sum([cell.diffusive_mass for cell in self.cells if cell])
        cm = sum([cell.crystal_mass for cell in self.cells if cell])
        bm = sum([cell.boundary_mass for cell in self.cells if cell])
        acnt = len([cell for cell in self.cells if cell and cell.attached])
        bcnt = len([cell for cell in self.cells if cell and cell.boundary])
        msg = "Step #%d, %d attached cells, %d boundary cells, %.2f dM, %.2f bM, %.2f cM, tot %.2f M" % (self.iteration, acnt, bcnt, dm, bm, cm, dm + cm + bm)
        log(msg)

    def step(self):
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
        self.iteration += 1

    def headroom(self):
        if self.max_steps and self.iteration >= self.max_steps:
            return False
        margin = self.size * .98
        for cell in self.cells:
            if cell == None:
                continue
            if not cell.attached:
                continue
            # get angle
            (angle, distance) = xy_to_polar(cell.xy)
            (margin_x, margin_y) = polar_to_xy((angle, margin))
            (cell_x, cell_y) = cell.xy
            if (cell_x > margin_x) and (cell_y > margin_y):
                return False
        return True

    def grow(self):
        while True:
            self.step()
            if self.iteration % 100 == 0:
                self.print_status()
                if not self.headroom():
                    break

    def save_image(self, fn, bw=False):
        if bw:
            parts = fn.split(".")
            parts[0] += "_bw"
            fn = str.join(".", parts)
        msg = "Saving %s..." % fn
        log(msg)
        img = Image.new("RGB", (self.size, self.size))
        for (idx, cell) in enumerate(self.cells):
            if cell == None:
                continue
            xy = self._cell_xy(idx)
            color = (0, 0, 0)
            if cell.attached:
                if bw:
                    color = 0xff
                    color = (color, color, color)
                else:
                    color = 200 * cell.crystal_mass
                    color = min(255, int(color))
                    color = (color, color, color)
            elif not bw:
                color = 200 * cell.diffusive_mass
                color = min(255, int(color))
                color = (color, color, color)
            img.putpixel(xy, color)
        img = img.rotate(45)
        img = img.resize((int(self.size * (1 / math.sqrt(3))), int(self.size)))
        img.save(fn)

class SnowflakeCell(object):
    def __init__(self, xy, lattice):
        self.xy = xy
        self.lattice = lattice
        self.env = lattice.environment
        self.diffusive_mass = self.env.gamma
        self.boundary_mass = 0.0
        self.crystal_mass = 0.0
        self.attached = False
        self.__neighbors = None

    def __getstate__(self):
        return (self.xy, self.diffusive_mass, self.boundary_mass, self.crystal_mass, self.attached)

    def __setstate__(self, state):
        self.xy = state[0]
        self.diffusive_mass = state[1]
        self.boundary_mass = state[2]
        self.crystal_mass = state[3]
        self.attached = state[4]
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
    
    @property
    def attached_neighbors(self):
        return [cell for cell in self.neighbors if cell.attached]

    @property
    def boundary(self):
        return (not self.attached) and any([cell.attached for cell in self.neighbors])

    def diffusion_calc(self):
        next_dm = self.diffusive_mass
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

    def step_one(self):
        self._next_dm = 0
        if not self.attached:
            self._next_dm = self.diffusion_calc()

    def step_two(self):
        self.diffusive_mass = self._next_dm
        self.attachment_flag = self.attached
        if self.boundary:
            self.freezing_step()
            self.attachment_flag = self.attachment_step()
            self.melting_step()

    def step_three(self):
        if self.boundary and self.attachment_flag:
            self.attach()

    def freezing_step(self):
        assert self.boundary
        self.boundary_mass += (1 - self.env.kappa) * self.diffusive_mass
        self.crystal_mass += (self.env.kappa * self.diffusive_mass)
        self.diffusive_mass = 0

    def attachment_step(self):
        assert self.boundary
        if len(self.attached_neighbors) <= 2:
            if self.boundary_mass > self.env.beta:
                return True
        elif len(self.attached_neighbors) == 3:
            if self.boundary_mass >= 1:
                return True
            else:
                summed_diffusion = self.diffusive_mass
                for cell in self.neighbors:
                    summed_diffusion += cell.diffusive_mass
                if summed_diffusion < self.env.theta and self.boundary_mass >= self.env.alpha:
                    return True
        elif len(self.attached_neighbors) >= 4:
            return True
        return False
    
    def melting_step(self):
        assert self.boundary
        self.diffusive_mass += self.env.mu * self.boundary_mass + self.env.upsilon * self.crystal_mass
        self.boundary_mass = (1 - self.env.mu) * self.boundary_mass
        self.crystal_mass = (1 - self.env.upsilon) * self.crystal_mass

    def noise_step(self):
        if random.choice([True, False]):
            self.diffusive_mass = (1 - self.env.sigma) * self.diffusive_mass
        else:
            self.diffusive_mass = (1 + self.env.sigma) * self.diffusive_mass

DEFAULTS = {
    "size": 200,
    "name": "snowflake",
    "load": False,
    "bw": False,
    "env": '',
    "pipeline_3d": False,
    "randomize": False,
    "max_steps": 0,
}

def get_cli():
    parser = argparse.ArgumentParser(description='Snowflake Generator.')
    parser.add_argument('-s', '--size', dest="size", type=int, help="The size of the snowflake.")
    parser.add_argument('-n', '--name', dest="name",  help="The name of the snowflake.")
    parser.add_argument('-l', '--load', dest='load', action='store_true', help='Load the pickle file.')
    parser.add_argument('-e', '--env', dest='env', help='comma seperated key=val env overrides')
    parser.add_argument('-b', '--bw', dest='bw', action='store_true', help='write out the image in black and white')
    parser.add_argument('-r', '--randomize', dest='randomize', action='store_true', help='randomize environment.')
    parser.add_argument('-x', '--extrude', dest='pipeline_3d', action='store_true', help='Enable 3d pipeline.')
    parser.add_argument('-M', '--max-steps', dest='max_steps', type=int, help='Maximum number of iterations.')

    parser.set_defaults(**DEFAULTS)
    args = parser.parse_args()
    return args

# 3d pipeline
def pipeline_3d(args):
    cmd = "potrace -i -b eps -o %s.eps %s_bw.bmp" % (args.name, args.name)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)
    #
    cmd = "pstoedit -dt -f dxf:-polyaslines %s.eps %s.dxf" % (args.name, args.name)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)
    #
    scad_fn = "%s.scad" % args.name
    f = open(scad_fn, 'w')
    scad_txt = 'linear_extrude(height=.03, scale=200, layer="0") import("%s.dxf");\n' % args.name
    f.write(scad_txt)
    f.close()
    cmd = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD -o %s.stl %s" % (args.name, scad_fn)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)
    #
    cmd = "python /Applications/Cura/Cura.app/Contents/Resources/Cura/cura.py -s %s.stl -i snowflake.ini" % args.name
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)

def run():
    msg = "Snowflake Generator v0.2"
    log(msg)
    args = get_cli()
    pfn = "%s.pickle" % args.name
    ifn = "%s.bmp" % args.name
    if args.pipeline_3d:
        args.bw = True
    if args.load:
        cl = CrystalLattice.load_lattice(pfn)
        cl.save_image(ifn, bw=args.bw)
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
        kw["max_steps"] = args.max_steps
        cl = CrystalLattice(args.size, **kw)
        try:
            cl.grow()
        finally:
            cl.save_image(ifn, bw=args.bw)
            cl.save_lattice(pfn)
    if args.pipeline_3d:
        pipeline_3d(args)

if __name__ == "__main__":
    run()
