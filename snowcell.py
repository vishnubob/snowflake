import math
from cell import Cell

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

class CrystalLattice(object):
    # technically a "pie slice"
    def __init__(self, radius, angle=60, celltype):
        self.radius = radius
        self.angle = angle
        self.celltype = celltype

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
                if self._cell_clipped(xy):
                    continue
                cell = self.celltype(xy, self)
                idx = self._cell_index(xy)
                self.cells[idx] = cell

    def _cell_index(self, xy):
        (x, y) = xy
        return y * self.radius + x

    def _cell_clipped(self, xy):
        (angle, distance) = xy_to_polar(xy)
        return (angle < 0 or angle > self.angle or distance > self.radius)
        

class SnowflakeCell(object):

    def __init__(self, xy, lattice, env):
        self.xy = xy
        self.lattice = lattice
        self.env = env
        self.diffusive_mass = 0.2
        self.boundary_mass = None
        self.crystal_mass = None
        self.__neighbors = None
        self._next_dm = None

    @property
    def neighbors(self):
        if self.__neighbors == None:
            self.__neighbors = self.lattice.get_neighbors(self.xy)
        return self.__neighbors

    @property
    def frozen(self):

    @property
    def boundary(self):
        return any([cell.frozen for cell in self.neighbors])

    def diffusion_step(self):
        self._next_dm = 0
        if self.frozen:
            assert self.diffusive_mass == 0
            self._next_dm = self.diffusive_mass
        else:
            if self.boundary:
                for cell in self.neighbors:
                    if cell.frozen:
                        self._next_dm += self.diffusive_mass
                    else:
                        self._next_dm += cell.diffusive_mass
            else:
                for cell in self.neighbors:
                    self._next_dm += cell.diffusive_mass
            self._next_dm += self.diffusive_mass
            self._next_dm /= (len(self.neighbors) + 1)

    def freezing_step(self):
        self.diffusive_mass = self._next_dm
        if self.boundary:
            self.diffusive_mass = 0
            self._next_bm = self.boundaryMass + (1 - self.env.kappa) * self.diffusionMass
            self.newCrystalMass = self.crystalMass + self.env.kappa * self.diffusionMass
        elif self.frozen:
            pass
        else:
            self._next_bm = self.boundaryMass
            self.newCrystalMass = self.crystalMass

    #  step 3
    def doAttachment(self):
        self.boundaryMass = self._next_bm
        self.crystalMass = self.newCrystalMass
        if self.boundary:
            if self.attachedNeighbours <= 2:
                if self.boundaryMass > self.snow.beta:
                    self.newState = True
            elif self.attachedNeighbours == 3:
                if self.boundaryMass >= 1:
                    self.newState = True
                else:
                    summedDiffusion = self.diffusionMass
                    for cell in self.neighbors:
                        summedDiffusion += cell.getDiffusionMass()
                    if summedDiffusion < self.snow.theta and self.boundaryMass >= self.snow.alpha:
                        self.newState = True
            elif self.attachedNeighbours >= 4:
                self.newState = True
        # if (newState)
        # changed = true;

    #  step 4
    def doMelting(self):
        if self.boundary:
            self.diffusionMass = self.diffusionMass + self.snow.mu * self.boundaryMass + self.snow.upsilon * self.crystalMass
            self.crystalMass = (1 - self.snow.upsilon) * self.crystalMass
            self.boundaryMass = (1 - self.snow.upsilon) * self.boundaryMass
            # changed = true;

    def updateState(self):
        if self.newState:
            self.newState = False
            self.state = True
            self.crystalMass = self.boundaryMass + self.crystalMass
            self.diffusionMass = 0
            self.boundaryMass = 0
            self.boundary = False
            self.doCalc = False

    def updateNeighbours(self):
        #  finishing the freeze
        if self.state == False:
            self.attachedNeighbours = 0
            for cell in self.neighbors:
                if cell.getState():
                    self.boundary = True
                    self.attachedNeighbours += 1
        self.oldDiffusionMass = self.diffusionMass

    def doCalcs(self):
        if self.state:
            return False
        if self.boundary:
            return True
        if self.doCalc:
            return True
        return False

    def setState(self):
        self.state = True
        self.diffusionMass = 0
        self.boundaryMass = 0
        self.crystalMass = 1
        self.boundary = False

    def getState(self):
        return self.state

    def getAttachedNeighbours(self):
        return self.attachedNeighbours

    def getBoundary(self):
        return self.boundary

    def setDiffusionMass(self, mass):
        self.diffusionMass = mass

    def getDiffusionMass(self):
        return self.diffusionMass

    def getCrystalMass(self):
        return self.crystalMass

    def getBoundaryMass(self):
        return self.boundaryMass

    def printState(self):
        print self.state, self.diffusionMass, self.boundaryMass, self.crystalMass, seld.boundary
        #  System.out.print( "x:" + nf( X, 3 ) + " y:" + nf( Y, 3 ) + " df: " +
        #  nf( diffusionMass, 1, 2 ) );
        #  System.out.print( " state:" + state );
        #  print "";



class Snowcell(Cell):
    X = int()
    Y = int()
    diffusionMass = float(0.2)
    initDiffusionMass = diffusionMass
    oldDiffusionMass = float()
    crystalMass = 0
    boundaryMass = 0
    newDiffusionMass = 0
    newCrystalMass = 0
    _next_bm = 0
    newState = False
    polar = (0.0, 0.0)
    finished = False
    doCalc = False
    changed = False
    attachedNeighbours = 0
    state = False
    boundary = False
    width = int()
    height = int()

    def __init__(self, x, y, w, h, snow):
        super(Snowcell, self).__init__()
        self.X = x
        self.Y = y
        self.width = w
        self.height = h
        self.snow = snow
        self.cells = self.snow.cells
        XY = self.snow.getXYFromIndex(x, y)
        self.polar = self.snow.getPolarFromXY(XY[0], XY[1])
        self.neighbors = []
        self._init_neighbors()

    def _init_neighbors(self):
        x = self.X
        y = self.Y
        if x > 1:
            self.neighbors.append(self.cells[x - 1][y])
        if x < self.width - 1:
            self.neighbors.append(self.cells[x + 1][y])
        if y > 1:
            self.neighbors.append(self.cells[x][y - 1])
        if y < self.height - 1:
            self.neighbors.append(self.cells[x][y + 1])
        if y % 2 == 0:
            if (x < self.width - 1) and (y > 1):
                self.neighbors.append(self.cells[x + 1][y - 1])
            if (x < self.width - 1) and (y < self.height - 1):
                self.neighbors.append(self.cells[x + 1][y + 1])
        else:
            if (x > 1) and (y > 1):
                self.neighbors.append(self.cells[x - 1][y - 1])
            if (x > 1) and (y < self.height - 1):
                self.neighbors.append(self.cells[x - 1][y + 1])

    def getPolar(self):
        return self.polar

    def getSegment(self):
        return 0

    def getX(self):
        return self.X

    def getY(self):
        return self.Y

    def isFake(self):
        return False

    #  step 1
    def doDiffusion(self):
        # changed = false;
        if self.state == False:
            self.newDiffusionMass = 0
            if self.boundary:
                #  reflecting boundary conditions
                for cell in self.neighbors:
                    if cell.getState():
                        self.newDiffusionMass += self.getDiffusionMass()
                    else:
                        self.newDiffusionMass += cell.getDiffusionMass()
            else:
                #  discrete diffusion with uniform weight of 1/7
                for cell in self.neighbors:
                    #  cell.printState();
                    self.newDiffusionMass += cell.getDiffusionMass()
            #  my own diffusion mass
            self.newDiffusionMass += self.getDiffusionMass()
            self.newDiffusionMass /= (len(self.neighbors) + 1)
        else:
            self.newDiffusionMass = self.diffusionMass
            #  should always be 0?
            if self.diffusionMass != 0:
                print "diffusion mass not 0!"
        # 		if (newDiffusionMass != 0)
        # changed = true;

    #  step 2
    def doFreezing(self):
        self.diffusionMass = self.newDiffusionMass
        if self.boundary:
            self._next_bm = self.boundaryMass + (1 - self.snow.kappa) * self.diffusionMass
            self.newCrystalMass = self.crystalMass + self.snow.kappa * self.diffusionMass
            #  surely this next bit can't be right?
            self.diffusionMass = 0
            # changed = true;
        else:
            self._next_bm = self.boundaryMass
            self.newCrystalMass = self.crystalMass

    #  step 3
    def doAttachment(self):
        self.boundaryMass = self._next_bm
        self.crystalMass = self.newCrystalMass
        if self.boundary:
            if self.attachedNeighbours <= 2:
                if self.boundaryMass > self.snow.beta:
                    self.newState = True
            elif self.attachedNeighbours == 3:
                if self.boundaryMass >= 1:
                    self.newState = True
                else:
                    summedDiffusion = self.diffusionMass
                    for cell in self.neighbors:
                        summedDiffusion += cell.getDiffusionMass()
                    if summedDiffusion < self.snow.theta and self.boundaryMass >= self.snow.alpha:
                        self.newState = True
            elif self.attachedNeighbours >= 4:
                self.newState = True
        # if (newState)
        # changed = true;

    #  step 4
    def doMelting(self):
        if self.boundary:
            self.diffusionMass = self.diffusionMass + self.snow.mu * self.boundaryMass + self.snow.upsilon * self.crystalMass
            self.crystalMass = (1 - self.snow.upsilon) * self.crystalMass
            self.boundaryMass = (1 - self.snow.upsilon) * self.boundaryMass
            # changed = true;

    def updateState(self):
        if self.newState:
            self.newState = False
            self.state = True
            self.crystalMass = self.boundaryMass + self.crystalMass
            self.diffusionMass = 0
            self.boundaryMass = 0
            self.boundary = False
            self.doCalc = False

    def updateNeighbours(self):
        #  finishing the freeze
        if self.state == False:
            self.attachedNeighbours = 0
            for cell in self.neighbors:
                if cell.getState():
                    self.boundary = True
                    self.attachedNeighbours += 1
        self.oldDiffusionMass = self.diffusionMass

    def doCalcs(self):
        if self.state:
            return False
        if self.boundary:
            return True
        if self.doCalc:
            return True
        return False

    def setState(self):
        self.state = True
        self.diffusionMass = 0
        self.boundaryMass = 0
        self.crystalMass = 1
        self.boundary = False

    def getState(self):
        return self.state

    def getAttachedNeighbours(self):
        return self.attachedNeighbours

    def getBoundary(self):
        return self.boundary

    def setDiffusionMass(self, mass):
        self.diffusionMass = mass

    def getDiffusionMass(self):
        return self.diffusionMass

    def getCrystalMass(self):
        return self.crystalMass

    def getBoundaryMass(self):
        return self.boundaryMass

    def printState(self):
        print self.state, self.diffusionMass, self.boundaryMass, self.crystalMass, seld.boundary
        #  System.out.print( "x:" + nf( X, 3 ) + " y:" + nf( Y, 3 ) + " df: " +
        #  nf( diffusionMass, 1, 2 ) );
        #  System.out.print( " state:" + state );
        #  print "";

