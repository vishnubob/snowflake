#!/usr/bin/env python
import random
import time
import math
import collections
import Image

from snowcell import Snowcell
from fakecell import Fakecell
from edgecell import Edgecell

#from Tkinter import *

def dd_none_factory():
    return collections.defaultdict(None) 

class Snow(object):
    #  constants
    b = float(1.3)

    #  keep above 1
    alpha = float(0.08)
    theta = float(0.025)
    k = float(0.003)
    u = float(0.07)
    y = float(0.00005)
    iterations = 0
    oldDiffusionMass = float(0.5)
    newDiffusionMass = 0
    humidityDisplay = 0
    temperatureDisplay = 0
    snowFlakeWidth = 0
    maxSnowFlakeWidth = int()
    Xcells = int()
    Ycells = int()
    snowArray = []
    realCells = []
    cellWidth = float()
    cellHeight = float()

    def __init__(self, Xcells, Ycells, cellWidth):
        self.cellWidth = cellWidth
        self.Xcells = int(Xcells)
        self.Ycells = int(Ycells)
        self.maxSnowFlakeWidth = int(((Xcells * 0.9) / 2))
        self.cellHeight = (cellWidth / 2) * math.tan(math.pi / 3)
        self.frameWidth = int((Xcells * cellWidth))
        self.frameHeight = int((Ycells * self.cellHeight))
        self.boundingCircleRadius = float(0.99) / 2 * Xcells
        #makeHexFrame()
        # 		initialise();

    def initialise(self):
        self.initialising = True
        self.realCells = []
        self.snowArray = collections.defaultdict(dd_none_factory)

        for i in range(self.Xcells):
            for j in range(self.Ycells):
                self.snowArray[i][j] = Snowcell(i, j, self.Xcells, self.Ycells, self)

        for i in range(self.Xcells):
            for j in range(self.Ycells):
                xy = self.getXYFromIndex(i, j)
                polar = self.getPolarFromXY(xy[0], xy[1])
                if (i == self.Xcells / 2) and (j == self.Ycells / 2):
                    pass
                elif polar[0] >= -math.pi and polar[0] <= (2 * math.pi / 3):
                    self.snowArray[i][j] = Fakecell(i, j, self.Xcells, self.Ycells, self)
                if not self.snowArray[i][j].isFake():
                    if polar[1] < self.boundingCircleRadius:
                        self.realCells.append(self.snowArray[i][j])
                    elif polar[1] <= self.Xcells / 2:
                        self.snowArray[i][j] = Edgecell(i, j, self.Xcells, self.Ycells, self)
                        self.realCells.append(self.snowArray[i][j])

        for i in range(self.Xcells):
            for j in range(self.Ycells):
                self.snowArray[i][j].getNeighbours()

        for i in range(self.Xcells):
            for j in range(self.Ycells):
                self.snowArray[i][j].updateNeighbours()

        self.roomToGrow()
        self.initialising = False

    def messageSetup(self):
        """ generated source for method messageSetup """
        for cell in realCells:
            cell.setDiffusionMass(float(0.0))
            if cell.getPolar().getY() < self.Xcells / 6:
                cell.setDiffusionMass(float(1))

    def placeSeed(self):
        """ generated source for method placeSeed """
        self.snowArray[self.Xcells / 2][self.Ycells / 2].setState()

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
        i = self.Xcells / 2
        while i < self.Xcells:
            self.snowFlakeWidth = i
            testCell = self.snowArray[i][self.Ycells / 2]
            if not testCell.getState():
                break
            i += 1
        self.snowFlakeWidth -= self.Xcells / 2
        if self.snowFlakeWidth > self.maxSnowFlakeWidth:
            return False
        return True

    def updateHumidity(self, knob1):
        self.humidityDisplay = float((20 + 60 * knob1))
        self.newDiffusionMass = knob1
        self.newDiffusionMass /= 2
        self.newDiffusionMass += 0.2
        for cell in self.realCells:
            if cell.getState() == False and cell.getBoundary() == False:
                if cell.getPolar()[1] > (self.snowFlakeWidth + self.Xcells / 40):
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
        x = xIndex - (self.Xcells / 2) + 0.5
        if yIndex % 2 != 0:
            x -= 0.5
        y = (self.Ycells / 2) - yIndex
        y /= self.cellWidth / self.cellHeight
        return (x, y)

    def getIndexFromXY(self, x, y):
        yRatio = self.cellHeight / self.cellWidth
        yIndex = int(round(self.Ycells / 2 - y / yRatio))
        if yIndex % 2 == 0:
            x -= 0.5
        xIndex = int(round(x))
        xIndex += self.Xcells / 2
        return (int(xIndex), int(yIndex))

    def surfaceIt(self, fn):
        txt = ''
        for y in range(self.Ycells):
            row = []
            for x in range(self.Xcells):
                cell = self.snowArray[x][y]
                colour = 0
                if cell.getPolar()[1] > self.boundingCircleRadius:
                    colour = 0
                else:
                    if cell.getState():
                        colour = 1 * cell.getCrystalMass()
                    else:
                        colour = 1 * cell.getDiffusionMass()
                colour = min(1, int(math.floor(colour)))
                row.append(colour)
            row = str.join(' ', map(str, row))
            txt += row + '\n'
        f = open(fn, 'w')
        f.write(txt)

    def imageIt(self, fn):
        data = ''
        for y in range(self.Ycells):
            for x in range(self.Xcells):
                cell = self.snowArray[x][y]
                colour = 0
                if cell.getPolar()[1] > self.boundingCircleRadius:
                    data += str.join('', map(chr, (colour, colour, colour)))
                    continue
                if cell.getState():
                    colour = 200 * cell.getCrystalMass()
                else:
                    colour = 200 * cell.getDiffusionMass()
                colour = min(255, int(colour))
                data += str.join('', map(chr, (colour, colour, colour)))
        print len(data)
        print self.Xcells, self.Ycells
        img = Image.fromstring("RGB", (self.Xcells, self.Ycells), data, "raw", "RGB", 0, 1)
        img.save(fn)

    def drawIt(self):
        """ generated source for method drawIt """
        calcOffset = int(round(self.cellWidth / 2))
        calcCellWidth = int(math.ceil(self.cellWidth))
        calcCellHeight = int(math.ceil(self.cellHeight))
        y = 0
        canvas.delete(ALL)

        for y in range(self.Ycells):
            for x in range(self.Xcells):
                cell = self.snowArray[x][y]
                if cell.getPolar()[1] > self.boundingCircleRadius:
                    continue 
                if cell.getState():
                    colour = 200 * cell.getCrystalMass()
                else:
                    colour = 200 * cell.getDiffusionMass()
                colour = min(255, int(colour))
                if y % 2 == 0:
                    offset = calcOffset
                xPix = round(x * self.cellWidth + offset)
                yPix = int(y * self.cellHeight)
                colour = "#%02x%02x%02x" % (colour, colour, colour)
                canvas.create_rectangle(xPix, yPix, xPix + calcCellWidth, yPix + calcCellHeight, fill=colour, outline=colour)
        canvas.update()

    def adjustDraw(self, knob1, knob2):
        """ generated source for method adjustDraw """
        calcOffset = int(round(self.cellWidth / 2))
        calcCellWidth = int(math.ceil(self.cellWidth))
        calcCellHeight = int(math.ceil(self.cellHeight))

        for y in range(self.Ycells):
            for x in range(self.Xcells):
                cell = self.snowArray[x][y]
                if cell.getState():
                    colour = float((knob1 + 0.35)) * 300 * cell.getCrystalMass()
                else:
                    colour = float(((knob2 + 0.5) * 4000 * cell.getDiffusionMass()))
                colour = min(255, max(0, int(colour)))
                if y % 2 == 0:
                    offset = calcOffset
                xPix = round(x * self.cellWidth + offset)
                yPix = round(y * self.cellHeight)
                
                colour = "#%02x%02x%02x" % (colour, colour, colour)
                #canvas.create_rectangle(xPix, yPix, xPix + calcCellWidth, yPix + calcCellHeight, fill=colour, outline=colour)
        canvas.update()

def run_flake(width, height, res_factor, cnt):
    w = width / res_factor
    h = height / res_factor
    p = 1.0001 * res_factor
    print w,h,p
    sn = Snow(w, h, p)
    #sn = Snow(403, 403, 1.7)
    #sn = Snow(403, 403, 1.01)

    sn.initialise();
    sn.placeSeed();
    temp = 1
    hum = .01
    cutoff = random.randint(-250, 250) + 1000
    while True:
        print "calc #%d (%.4f, %.4f) %.2f" % (sn.iterations, temp, hum, sn.temperatureDisplay)
        sn.calculate()
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
        if sn.iterations == cutoff:
            now = time.time()
            print "draw"
            sn.surfaceIt("snowflake_%d.dat" % cnt)
            sn.imageIt("snowflake_%d.png" % cnt)
            #sn.adjustDraw(temp, hum)
            later = time.time()
            print "draw finished in %.2f seconds." % (later - now)
            break

width = 200
height = 200
#window = Tk()
#canvas = Canvas(window, width=width, height=height, bg='black')
#canvas.pack()

cnt = 1
while 1:
    run_flake(width, height, 1.0001, cnt)
    cnt += 1
