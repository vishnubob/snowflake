#!/usr/bin/env python
import random
import time
import math
import collections
import Image
import ImageDraw

from snowcell import Snowcell
from fakecell import Fakecell
from edgecell import Edgecell

#from Tkinter import *

def dd_none_factory():
    return collections.defaultdict(None) 

class SnowFlake(object):
    # (3a) 
    # "A boundary site with 1 or 2 attached neighbors needs boundary mass at least beta to join the crystal
    #  This is the case when the local mesoscopic geometry near x corresponds to a tip or flat spot of the crystal. 
    #  (Distinguishing the two cases turns out to be of minor significance.) In our simulations, beta is typically 
    #  between about 1.05 and 3. We assume beta > 1 since 1 is the basic threshold of the case to follow next.
    beta = 1.3

    # (3b)
    # "A boundary site with 3 attached neighbors joins the crystal if either it has boundary mass >= 1, 
    #  or it has diffusive mass < theta in its neighborhood and it has boundary mass >= alpha"
    theta = 0.025
    alpha = 0.08

    # (2) 
    # "Proportion kappa of the diffusive mass at each boundary site crystallizes. 
    #  The remainder (proportion 1 - kappa) becomes boundary mass."
    kappa = 0.003
    kappa = 0.001

    # (4)
    # "Proportion mu of the boundary mass and proportion upsilon of the crystal mass at each boundary site become diffusive mass. 
    #  Melting represents mass flow at the boundary from ice and quasi-liquid back to vapor, reverse
    #  effects from the freezing of step ii. Typically mu is small and upsilon extremely small."
    mu = 0.07
    upsilon = 0.00005

    # (5)
    # "The diffusive mass at each site undergoes an independent random perturbation of proportion sigma"
    sigma = 0.00001

    beta = 1.5

    def __init__(self, x_cells, y_cells, cellWidth):
        self.cellWidth = cellWidth
        self.x_cells = int(x_cells)
        self.y_cells = int(y_cells)
        self.max_width = int(((x_cells * 0.9) / 2))
        self.cellHeight = (cellWidth / 2) * math.tan(math.pi / 3)
        self.frameWidth = int((x_cells * cellWidth))
        self.frameHeight = int((y_cells * self.cellHeight))
        self.boundingCircleRadius = float(0.99) / 2 * x_cells

    def initialise(self):
        self.realCells = []
        self.cells = collections.defaultdict(dd_none_factory)
        self.iterations = 0

        for i in range(self.x_cells):
            for j in range(self.y_cells):
                self.cells[i][j] = Snowcell(i, j, self.x_cells, self.y_cells, self)

        for i in range(self.x_cells):
            for j in range(self.y_cells):
                xy = self.getXYFromIndex(i, j)
                polar = self.getPolarFromXY(xy[0], xy[1])
                if (i == self.x_cells / 2) and (j == self.y_cells / 2):
                    pass
                elif polar[0] >= -math.pi and polar[0] <= (2 * math.pi / 3):
                    self.cells[i][j] = Fakecell(i, j, self.x_cells, self.y_cells, self)
                if not self.cells[i][j].isFake():
                    if polar[1] < self.boundingCircleRadius:
                        self.realCells.append(self.cells[i][j])
                    elif polar[1] <= self.x_cells / 2:
                        self.cells[i][j] = Edgecell(i, j, self.x_cells, self.y_cells, self)
                        self.realCells.append(self.cells[i][j])

        for i in range(self.x_cells):
            for j in range(self.y_cells):
                self.cells[i][j].getNeighbours()

        for i in range(self.x_cells):
            for j in range(self.y_cells):
                self.cells[i][j].updateNeighbours()

        self.roomToGrow()
        self.initialising = False

    def messageSetup(self):
        """ generated source for method messageSetup """
        for cell in realCells:
            cell.setDiffusionMass(float(0.0))
            if cell.getPolar().getY() < self.x_cells / 6:
                cell.setDiffusionMass(float(1))

    def placeSeed(self):
        """ generated source for method placeSeed """
        self.cells[self.x_cells / 2][self.y_cells / 2].setState()

    def calculate(self):
        """ generated source for method calculate """
        self.iterations += 1
        for cell in self.realCells:
            cell.doDiffusion()
        for cell in self.realCells:
            cell.doFreezing()
            cell.doAttachment()
            cell.doMelting()
            cell.updateState()
        for cell in self.realCells:
            cell.updateNeighbours()

    def makeHexFrame(cls):
        """ generated source for method makeHexFrame """
        cls.hexFrameBlack = BufferedImage(cls.frameWidth, cls.frameHeight, BufferedImage.TYPE_INT_ARGB)
        cls.hexFrameWhite = BufferedImage(cls.frameWidth, cls.frameHeight, BufferedImage.TYPE_INT_ARGB)
        osg = cls.hexFrameBlack.createGraphics()
        osg.setComposite(AlphaComposite.Src)
        osg.setColor(Color(0, 0, 0))
        osg.fillRect(0, 0, cls.frameWidth, cls.frameHeight)
        hex = getHexagon(cls.frameWidth / 2, cls.frameHeight / 2, int((cls.frameWidth * 0.99 / 2)))
        osg.setColor(Color(0, 0, 0, 0))
        osg.fillPolygon(hex)
        osg = cls.hexFrameWhite.createGraphics()
        osg.setComposite(AlphaComposite.Src)
        osg.setColor(Color(255, 255, 255))
        osg.fillRect(0, 0, cls.frameWidth, cls.frameHeight)
        osg.setColor(Color(0, 0, 0, 0))
        osg.fillPolygon(hex)

    @classmethod
    def getHexagon(cls, x, y, h):
        """ generated source for method getHexagon """
        hexagon = Polygon()
        i = 0
        while i < 7:
            hexagon.addPoint(int((round(x + math.sin(hex) * h))), int((round(y + math.cos(hex) * h))))
            i += 1
        return hexagon

    def roomToGrow(self):
        i = self.x_cells / 2
        while i < self.x_cells:
            self.snowFlakeWidth = i
            testCell = self.cells[i][self.y_cells / 2]
            if not testCell.getState():
                break
            i += 1
        self.snowFlakeWidth -= self.x_cells / 2
        if self.snowFlakeWidth > self.max_width:
            return False
        return True

    def updateHumidity(self, knob1):
        self.humidityDisplay = float((20 + 60 * knob1))
        self.newDiffusionMass = knob1
        self.newDiffusionMass /= 2
        self.newDiffusionMass += 0.2
        for cell in self.realCells:
            if cell.getState() == False and cell.getBoundary() == False:
                if cell.getPolar()[1] > (self.snowFlakeWidth + self.x_cells / 40):
                    cell.setDiffusionMass(self.newDiffusionMass)
        self.oldDiffusionMass = self.newDiffusionMass

    def updateTemperature(self, knob2):
        self.temperatureDisplay = float((-5 - 10 * knob2))
        knob2 = 1 - knob2
        newYF = knob2
        self.b = 1 + newYF
        self.alpha = newYF * float(0.1)
        self.theta = newYF * float(0.01)
        self.k = newYF * float(0.0001)
        self.u = newYF * float(0.01)
        self.y = newYF * float(0.0001)

    def getWidthHeight(self):
        return (self.frameWidth + 2 * self.controlBarWidth, self.frameHeight)

    def getXYFromPolar(self, angle, distance):
        y = math.sin(angle) * distance
        x = math.cos(angle) * distance
        return (x, y)

    def getPolarFromXY(self, x, y):
        angle = math.atan2(y, x)
        distance = math.hypot(x, y)
        return (angle, distance)

    def getXYFromIndex(self, xIndex, yIndex):
        x = xIndex - (self.x_cells / 2) + 0.5
        if yIndex % 2 != 0:
            x -= 0.5
        y = (self.y_cells / 2) - yIndex
        y /= self.cellWidth / self.cellHeight
        return (x, y)

    def getIndexFromXY(self, x, y):
        yRatio = self.cellHeight / self.cellWidth
        yIndex = int(round(self.y_cells / 2 - y / yRatio))
        if yIndex % 2 == 0:
            x -= 0.5
        xIndex = int(round(x))
        xIndex += self.x_cells / 2
        return (int(xIndex), int(yIndex))

    def surfaceIt(self, fn):
        txt = ''
        for y in range(self.y_cells):
            row = []
            for x in range(self.x_cells):
                cell = self.cells[x][y]
                color = 0
                if cell.getPolar()[1] > self.boundingCircleRadius:
                    color = 0
                else:
                    if cell.getState():
                        color = 1 * cell.getCrystalMass()
                    else:
                        color = 1 * cell.getDiffusionMass()
                color = min(1, int(math.floor(color)))
                row.append(color)
            row = str.join(' ', map(str, row))
            txt += row + '\n'
        f = open(fn, 'w')
        f.write(txt)

    def imageIt(self, fn):
        calcOffset = int(round(self.cellWidth / 2))
        calcCellWidth = int(math.ceil(self.cellWidth))
        calcCellHeight = int(math.ceil(self.cellHeight))

        img = Image.new("RGB", (self.x_cells, self.y_cells))
        draw = ImageDraw.Draw(img)
        for y in range(self.y_cells):
            for x in range(self.x_cells):
                cell = self.cells[x][y]
                color = 0
                if cell.getPolar()[1] > self.boundingCircleRadius:
                    continue
                if cell.getState():
                    color = 200 * cell.getCrystalMass()
                else:
                    color = 200 * cell.getDiffusionMass()
                color = min(255, int(color))
                offset = 0
                if y % 2 == 0:
                    offset = calcOffset
                xPix = round(x * self.cellWidth + offset)
                yPix = int(y * self.cellHeight)
                color = (color, color, color)
                draw.rectangle((xPix, yPix, xPix + calcCellWidth, yPix + calcCellHeight), fill=color, outline=color)
        img.save(fn)

    def drawIt(self):
        """ generated source for method drawIt """
        calcOffset = int(round(self.cellWidth / 2))
        calcCellWidth = int(math.ceil(self.cellWidth))
        calcCellHeight = int(math.ceil(self.cellHeight))
        y = 0
        canvas.delete(ALL)

        for y in range(self.y_cells):
            for x in range(self.x_cells):
                cell = self.cells[x][y]
                #if cell.getPolar()[1] > self.boundingCircleRadius:
                #    continue 
                if cell.getState():
                    color = 200 * cell.getCrystalMass()
                else:
                    color = 200 * cell.getDiffusionMass()
                color = min(255, int(color))
                offset = 0
                if y % 2 == 0:
                    offset = calcOffset
                xPix = round(x * self.cellWidth + offset)
                yPix = int(y * self.cellHeight)
                color = "#%02x%02x%02x" % (color, color, color)
                canvas.create_rectangle(xPix, yPix, xPix + calcCellWidth, yPix + calcCellHeight, fill=color, outline=color)
        canvas.update()

def run_flake(width, height, res_factor, cnt, cutoff):
    #w = width / res_factor
    #h = height / res_factor
    #p = 1.0001 * res_factor
    w = width
    h = height
    p = res_factor
    print w, h, p
    sn = SnowFlake(w, h, p)
    sn.initialise();
    sn.placeSeed();
    temp = 1
    hum = .01
    while True:
        #print "calc #%d (%.4f, %.4f) %.2f" % (sn.iterations, temp, hum, sn.temperatureDisplay)
        print "calc #%d" % sn.iterations
        sn.calculate()
        """
        if random.choice((1, 0)):
            temp += (random.random() / 101)
        else:
            temp -= (random.random() / 100)
        if random.choice((1, 0)):
            hum += random.random() / 250
        else:
            hum -= random.random() / 500
        sn.updateTemperature(temp)
        sn.updateHumidity(hum)
        """
        if sn.iterations == cutoff:
            break
    now = time.time()
    print "draw"
    #sn.surfaceIt("snowflake_%d.dat" % cnt)
    sn.imageIt("snowflake_%d.png" % cnt)
    later = time.time()
    print "draw finished in %.2f seconds." % (later - now)

width = 403
height = 403
#window = Tk()
#canvas = Canvas(window, width=width, height=height, bg='black')
#canvas.pack()

cutoff = random.randint(-250, 250) + 1000
cnt = 1
run_flake(width, height, 1.7, cnt, 2000)
