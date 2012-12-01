#!/usr/bin/env python

import random
import math

import Image
import ImageDraw

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

class CrystalLattice(object):
    # technically a "pie slice"
    def __init__(self, radius, angle=60, environment=None, celltype=None):
        self.radius = radius
        self.angle = angle
        if environment == None:
            self.environment = CrystalEnvironment()
        if celltype == None:
            celltype = SnowflakeCell
        self.celltype = celltype
        self.iteration = 1
        self._init_cells()

    def get_neighbors(self, xy):
        (x, y) = xy
        # up, down, left, right
        nlist = [(x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y)]
        # next is tricky
        if y & 1:
            nlist += [(x - 1, y + 1), (x - 1, y - 1)]
        else:
            nlist += [(x + 1, y + 1), (x + 1, y - 1)]
        nlist = map(self._cell_index, nlist)
        nlist = filter(lambda x: x > 0 and x < len(self.cells), nlist)
        return tuple([self.cells[nidx] for nidx in nlist if self.cells[nidx] != None])

    def _init_cells(self):
        self.cells = [None] * (self.radius * self.radius)
        for x in range(self.radius):
            for y in range(self.radius):
                xy = (x, y)
                #if self._cell_clipped(xy):
                #    continue
                cell = self.celltype(xy, self)
                idx = self._cell_index(xy)
                self.cells[idx] = cell
        idx = self._cell_index((self.radius / 2, self.radius / 2))
        self.cells[idx].attached = True
        self.cells[idx].crystal_mass = self.cells[idx].diffusive_mass
        self.cells[idx].diffusive_mass = 0

    def _cell_index(self, xy):
        (x, y) = xy
        return y * self.radius + x

    def _cell_xy(self, idx):
        y = idx / self.radius
        x = idx % self.radius
        return (x, y)

    def _cell_clipped(self, xy):
        (angle, distance) = xy_to_polar(xy)
        return (angle < 0 or angle > self.angle or distance > self.radius)

    def print_status(self):
        dm = sum([cell.diffusive_mass for cell in self.cells if cell])
        cm = sum([cell.crystal_mass for cell in self.cells if cell])
        bm = sum([cell.boundary_mass for cell in self.cells if cell])
        acnt = len([cell for cell in self.cells if cell and cell.attached])
        bcnt = len([cell for cell in self.cells if cell and cell.boundary])
        print "Step #%d, %d attached cells, %d boundary cells, %.2f dM, %.2f bM, %.2f cM, tot %.2f M" % (self.iteration, acnt, bcnt, dm, bm, cm, dm + cm + bm)

    def step(self):
        self.print_status()
        for step in range(5):
            for cell in self.cells:
                if cell == None or cell.attached:
                    continue
                cell.step(step)
        self.iteration += 1

    def headroom(self):
        margin = self.radius * .95
        for cell in self.cells:
            if cell == None:
                continue
            if not cell.boundary:
                continue
            # get angle
            (angle, distance) = xy_to_polar(cell.xy)
            (margin_x, margin_y) = polar_to_xy((angle, margin))
            (cell_x, cell_y) = cell.xy
            if (cell_x > margin_x) and (cell_y > margin_y):
                return False
        return True

    def grow(self):
        while self.headroom():
            self.step()

    def save_image(self, fn):
        img = Image.new("RGB", (self.radius, self.radius))
        for (idx, cell) in enumerate(self.cells):
            if cell == None:
                continue
            xy = self._cell_xy(idx)
            if cell.attached:
                color = 200 * cell.crystal_mass
            else:
                color = 200 * cell.diffusive_mass
            color = min(255, int(color))
            color = (color, color, color)
            img.putpixel(xy, color)
        img = img.resize((int(10 * self.radius), int(10 * self.radius * (1 / math.sqrt(3)))))
        img = img.rotate(45)
        img.save(fn)

class SnowflakeCell(object):
    def __init__(self, xy, lattice):
        self.xy = xy
        self.lattice = lattice
        self.env = lattice.environment
        self.diffusive_mass = 0.2
        self.boundary_mass = 0.0
        self.crystal_mass = 0.0
        self.attached = False
        self.__neighbors = None

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

    def step(self, step):
        if step == 0:
            self.diffusion_step()
        elif step == 1:
            self.freezing_step()
        elif step == 2:
            self.attachment_step()
        elif step == 3:
            self.melting_step()
        elif step == 4:
            self.noise_step()
        else:
            raise ValueError, "Unknown step!"

    def diffusion_step(self):
        if not self.attached:
            _next_dm = self.diffusive_mass
            for cell in self.neighbors:
                if cell.attached:
                    _next_dm += self.diffusive_mass
                else:
                    _next_dm += cell.diffusive_mass
            _next_dm /= (len(self.neighbors) + 1)
            self.diffusive_mass = _next_dm

    def freezing_step(self):
        if self.boundary:
            self.boundary_mass = self.boundary_mass + (1 - self.env.kappa) * self.diffusive_mass
            self.crystal_mass = self.crystal_mass + (self.env.kappa * self.diffusive_mass)
            self.diffusive_mass = 0

    def attachment_step(self):
        if self.boundary:
            if len(self.attached_neighbors) <= 2:
                if self.boundary_mass > self.env.beta:
                    self.attached = True
            elif len(self.attached_neighbors) == 3:
                if self.boundary_mass >= 1:
                    self.attached = True
                else:
                    summed_diffusion = self.diffusive_mass
                    for cell in self.neighbors:
                        summed_diffusion += cell.diffusive_mass
                    if summed_diffusion < self.env.theta and self.boundary_mass >= self.env.alpha:
                        self.attached = True
            elif len(self.attached_neighbors) >= 4:
                self.attached = True
            # if this is true, we just became attached
            if self.attached:
                self.crystal_mass = self.boundary_mass + self.crystal_mass
                self.boundary_mass = 0

    def melting_step(self):
        if self.boundary:
            self.diffusive_mass = self.diffusive_mass + self.env.mu * self.boundary_mass + self.env.upsilon * self.crystal_mass
            self.boundary_mass = (1 - self.env.mu) * self.boundary_mass
            self.crystal_mass = (1 - self.env.upsilon) * self.crystal_mass

    def noise_step(self):
        if random.choice([True, False]):
            self.diffusive_mass = (1 - self.env.sigma) * self.diffusive_mass
        else:
            self.diffusive_mass = (1 + self.env.sigma) * self.diffusive_mass

try:
    cl = CrystalLattice(40)
    cl.grow()
finally:
    cl.save_image("sf.png")
