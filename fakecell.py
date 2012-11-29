import math
from cell import Cell

class Fakecell(Cell):
    """ generated source for class Fakecell """
    mirror = Cell()
    fakeX = int()
    fakeY = int()
    polar = (0.0, 0.0)
    segment = 0

    def __init__(self, x, y, w, h, snow):
        """ generated source for method __init__ """
        super(Fakecell, self).__init__()
        self.snow = snow
        self.cells = self.snow.cells
        XY = self.snow.getXYFromIndex(x, y)
        self.polar = self.snow.getPolarFromXY(*XY)
        # map from 0 to 2PI
        fakeAngle = self.polar[0]
        # checked
        if self.polar[0] <= -2 * math.pi / 3:
            fakeAngle = self.polar[0] - math.pi / 3
            self.segment = 1
        elif self.polar[0] <= -math.pi / 3:
            fakeAngle = self.polar[0] - 2 * math.pi / 3
            self.segment = 2
        elif self.polar[0] <= 0:
            fakeAngle = self.polar[0] - math.pi
            self.segment = 3
        elif self.polar[0] <= math.pi / 3:
            fakeAngle = self.polar[0] + 2 * math.pi / 3
            self.segment = 4
        elif self.polar[0] <= 2 * math.pi / 3:
            fakeAngle = self.polar[0] + math.pi / 3
            self.segment = 5
        # segment = (int) ((realAngle + math.pi ) / ( math.pi / 3 ));
        fakeXY = snow.getXYFromPolar(fakeAngle, self.polar[1])
        fakeIndex = snow.getIndexFromXY(fakeXY[0], fakeXY[1])
        # if( fakeIndex[1] % 2 == 0 && fakeIndex[0] > 0)
        # fakeIndex[0] --;
        try:
            self.mirror = self.cells[fakeIndex[0]][fakeIndex[1]]
            self.fakeX = fakeIndex[0]
            self.fakeY = fakeIndex[1]
        except KeyError:
            self.mirror = self.cells[snow.x_cells - 1][snow.y_cells - 1]
            self.fakeX = snow.x_cells - 1
            self.fakeY = snow.y_cells - 1

    def getPolar(self):
        """ generated source for method getPolar """
        return self.polar

    def getSegment(self):
        """ generated source for method getSegment """
        return self.segment

    def getX(self):
        """ generated source for method getX """
        return self.fakeX

    def getAttachedNeighbours(self):
        """ generated source for method getAttachedNeighbours """
        return self.mirror.getAttachedNeighbours()

    def getY(self):
        """ generated source for method getY """
        return self.fakeY

    def isFake(self):
        """ generated source for method isFake """
        return True

    def getDiffusionMass(self):
        """ generated source for method getDiffusionMass """
        return self.mirror.getDiffusionMass()

    def getCrystalMass(self):
        """ generated source for method getCrystalMass """
        return self.mirror.getCrystalMass()

    def getState(self):
        """ generated source for method getState """
        return self.mirror.getState()

    def getBoundary(self):
        """ generated source for method getBoundary """
        return self.mirror.getBoundary()

    def updateState(self):
        """ generated source for method updateState """

    def getNeighbours(self):
        """ generated source for method getNeighbours """

    def updateNeighbours(self):
        """ generated source for method updateNeighbours """

    def setState(self):
        """ generated source for method setState """

    def setDiffusionMass(self, mass):
        """ generated source for method setDiffusionMass """

    def doFreezing(self):
        """ generated source for method doFreezing """

    def doAttachment(self):
        """ generated source for method doAttachment """

    def doMelting(self):
        """ generated source for method doMelting """

    def doDiffusion(self):
        """ generated source for method doDiffusion """

