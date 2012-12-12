#! /usr/bin/env python

"""A simple splines package.

This package aims to be simple to use, but also simple to read - it's as much an exegesis on splines as it is a package. It's also developed to support somewhat more general exploratory programming with curves, so it supports slightly peripheral things like the ability to fit low-order polynomials to sequences of points.

Note that the only code in the package which knows the dimensionality of the space being worked in is the Point class. This code is two-dimensional, but a few changes to Point would make it three-dimensional.

Performance is almost certainly execrable.

(c) 2005 Tom Anderson <twic@urchin.earth.li> - all rights reserved

Redistribution and use in source and binary forms, with or without modification, are permitted.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

"""todo:

- make calculation of multiple points more efficient; support a form of call which evaluates over a range or an iteratable of u values
- allow subclasses to handle this themselves, so they can cache intermediate results
- support slices in the spline subclasses, maybe - do this by supporting slice objects as parameters to __getitem__
- does list() use slices? in 2.2, it appears to use getitem with scalar indices - and not to use len, but to rely on getting an IndexError!

"""

# excuse this - i'm on 2.2 here
try:
	True
except NameError:
	True = 1 == 1
	False = 1 == 0

def tuples2points(ts):
	return map(lambda t: Point(*t), ts)

class Point(object):
	"A point. Actually a somewhat general vector, but never mind. Implements more behaviour than it strictly needs to."
	__slots__ = ("x", "y")
	def __init__(self, x, y):
		self.x = float(x)
		self.y = float(y)
	def __add__(self, other):
		return Point((self.x + other.x), (self.y + other.y))
	def __sub__(self, other):
		return Point((self.x - other.x), (self.y - other.y))
	def __mul__(self, factor):
		return Point((self.x * factor), (self.y * factor))
	def __div__(self, factor):
		return Point((self.x / factor), (self.y / factor))
	def __neg__(self):
		return Point(-(self.x), -(self.y))
	def __abs__(self):
		"Computes the magnitude of the vector."
		return (~self) ** 0.5
	def __xor__(self, other):
		"Computes the dot product. If you look at '^' long enough, it looks like '.'. You don't think so? Keep looking."
		return (self.x * other.x) + (self.y * other.y)
	def __invert__(self):
		"Computes the dot-square, ie the dot product of the point with itself. Hey, if the xor operator can mean dot, the complement operator can mean this!"
		return (self.x ** 2) + (self.y ** 2)
	def __hash__(self):
		return hash(self.x) ^ hash(self.y)
	def __cmp__(self, other):
		"This is a pretty arbitrary order, but i'm told i have to have one."
		d = cmp(self.x, other.x)
		if (d == 0): d = cmp(self.y, other.y)
		return d
	def __iter__(self):
		"A bit of a funny method, this; the idea is to make it possible to do tuple(p)."
		# if you have a python which supports generators (unlike me), uncomment these lines and comment out or delete the last line
		# yield self.x
		# yield self.y
		return iter((self.x, self.y))
	def __nonzero__(self):
		return (self.x != 0.0) and (self.y != 0.0)
	def __str__(self):
		return "(" + str(self.x) + "," + str(self.y) + ")"
	def __repr__(self):
		return "splines.Point(" + str(self.x) + ", " + str(self.y) + ")"

class Curve(object):
	"A curve describes a continuous sequence of points. Points are discriminated by their distance along the curve, which is measured in a vague, dimensionless way, using a coordinate called 'u'; a given value of u corresponds to a particular point p on the curve. Individual coordinates of p do not necessarily vary monotonically with u, and multiple values of u may map to the same value of p, if the curve crosses itself. I think this is called a 'parametric' curve. In this package, curves are maps from u to p, not from x to y. This is very important!"
	def __call__(self, u):
		"Finds the position of the curve at coordinate u."
		raise NotImplementedError

class Line(Curve):
	"A straight line."
	def __init__(self, a, b):
		"a and b are the 0th and 1st order coefficients, respectively; the equation of the curve is p = a + ub. The coefficients are all points."
		self.a = a
		self.b = b
	def __call__(self, u):
		return self.a + (self.b * u)
	def __str__(self):
		return str(self.a) + " + " + str(self.b) + "u"
	def __repr__(self):
		return "splines.Line(" + repr(self.a) + ", " + repr(self.b) + ")"
	def fit(p, q):
		"Fits a line to two points, so that at u = 0, it passes through p, and at u = 1, it passes through q."
		a = p
		b = (q - p)
		return Line(a, b)
	fit = staticmethod(fit)

class Quadratic(Curve):
	"A quadratic curve."
	def __init__(self, a, b, c):
		"a, b and c are the 0th, 1st and 2nd order coefficients, respectively; the equation of the curve is p = a + ub + (u**2)c. The coefficients are all points."
		self.a = a
		self.b = b
		self.c = c
	def __call__(self, u):
		return self.a + (self.b * u) + (self.c * (u ** 2))
	def __str__(self):
		return str(self.a) + " + " + str(self.b) + "u + " + str(self.c) + "u**2"
	def __repr__(self):
		return "splines.Quadratic(" + repr(self.a) + ", " + repr(self.b) + ", " + repr(self.c) + ")"
	def fit(o, p, q):
		"Fits a quadratic to three points, so that it passes through o, p and q at u = -1, 0 and 1, respectively."
		a = p
		b = (q - o) / 2.0
		c = ((q + o) / 2.0) - p
		return Quadratic(a, b, c)
	fit = staticmethod(fit)

class Cubic(Curve):
	"A cubic curve."
	def __init__(self, a, b, c, d):
		"a, b, c and d are the 0th, 1st, 2nd and 3rd order coefficients, respectively; the equation of the curve is p = a + ub + (u**2)c + (u**3)d. The coefficients are all points."
		self.a = a
		self.b = b
		self.c = c
		self.d = d
	def __call__(self, u):
		return self.a + (self.b * u) + (self.c * (u ** 2)) + (self.d * (u ** 3))
	def __str__(self):
		return str(self.a) + " + " + str(self.b) + "u + " + str(self.c) + "u**2 + " + str(self.d) + "u**3"
	def __repr__(self):
		return "splines.Cubic(" + repr(self.a) + ", " + repr(self.b) + ", " + repr(self.c) + ", " + repr(self.d) + ")"
	def fit(o, p, q, r):
		"Fits a cubic to four points, so that it passes through o, p, q and r at u = -1, 0, 1 and 2, respectively."
		# there's probably a slightly simpler way of working this out ...
		a = p
		c = ((o + q) / 2.0) - a
		d = (((r - (q * 2.0)) + a) - (c * 2.0)) / 6.0
		b = ((q - o) / 2.0) - d
		return Cubic(a, b, c, d)
	fit = staticmethod(fit)

class Spline(Curve):
	"A spline is a curve defined be a sequence of knots, each knot being a point, and a way of drawing a curve between these points. Some splines pass exactly through their knots; others do not. The spline may not reach all the knots at its ends: these are known as loose knots (the knots which are reached being tight knots), and the number at each end is fixed for splines of a given type; if a spline has loose knots, it has a property called 'looseKnots' giving the number at either end. The parametric coordinate for splines is defined to be 0 at their first knot, increasing by 1 at each knot. The sequence of knots is exposed as the member variable 'knots', which can be manipulated directly. Note that splines generally require at least three tight knots to work; don't expect sensible behaviour from smaller splines."
	def __init__(self, knots=None):
		if (knots != None):
			self.knots = list(knots)
		else:
			self.knots = []
	def __repr__(self):
		return type(self).__name__ + "([" + ", ".join(self.knots) + "])"

class PiecewiseSpline(Spline):
	"A piecewise spline is one in which the curve is drawn by constructing 'pieces', curves which connect adjacent knots. The spline is simply the concatenation of the pieces."
	def __getitem__(self, i):
		"Get the ith piece of the spline (the piece valid from i <= u < (i + 1)). A position u on the spline corresponds to a position v = (u - i) on the piece. An index i is valid iff 0 <= i < len(self)."
		raise NotImplementedError
	def __call__(self, u):
		if (u < 0.0):
			i = 0
		elif (u >= len(self)):
			i = len(self) - 1
		else:
			i = int(u)
		v = u - i
		return self[i](v)
	def __len__(self):
		"The length of a spline is the number of pieces in it, which is one less than the number of tight knots."
		return len(self.knots) - ((2 * getattr(self, "looseKnots", 0)) + 1)

class Polyline(PiecewiseSpline):
	"The simplest possible spline!"
	def __getitem__(self, i):
		return Line.fit(self.knots[i], self.knots[(i + 1)])

class NaturalCubicSpline(PiecewiseSpline):
	"The daddy! Since the calculation of the pieces is fairly heavy work, we cache the results."
	def __init__(self, knots=None):
		Spline.__init__(self, knots)
		self.cachedknots = None
	def __getitem__(self, i):
		if (self.knots != self.cachedknots):
			self.calculate()
		return self.pieces[i]
	def calculate(self):
		"This code is ultimately derived from some written by Tim Lambert. Cheers Tim."
		# you are not expected to understand this
		# i certainly don't
		p = self.knots
		self.cachedknots = list(p)
		g = _gamma(len(p))
		e = _epsilon(g, _delta(p, g))
		self.pieces = []
		for i in range((len(p) - 1)):
			a = p[i]
			b = e[i]
			c = ((p[(i + 1)] - p[i]) * 3.0) - ((e[i] * 2.0) + e[(i + 1)])
			d = ((p[i] - p[(i + 1)]) * 2.0) + e[i] + e[(i + 1)]
			self.pieces.append(Cubic(a, b, c, d))
		# i am always absolutely outraged that this voodoo works!

# don't ask what happened to alpha and beta

def _gamma(n):
	g = [0.5]
	for i in range(1, (n - 1)):
		g.append((1.0 / (4.0 - g[(i - 1)])))
	g.append((1.0 / (2.0 - g[-1])))
	return g

def _delta(p, g):
	d = [((p[1] - p[0]) * (g[0] * 3.0))]
	for i in range(1, (len(p) - 1)):
		d.append(((((p[(i + 1)] - p[(i - 1)]) * 3.0) - d[(i - 1)]) * g[i]))
	d.append(((((p[-1] - p[-2]) * 3.0) - d[-1]) * g[-1]))
	return d

def _epsilon(g, d):
	# todo: would be nice to find a way to do this without the reverse
	# the original code built an empty length-len(g) list, then filled it backwards
	e = [d[-1]]
	for i in range((len(d) - 2), -1, -1):
		e.append((d[i] - (e[-1] * g[i])))
	e.reverse()
	return e

class BlendedSpline(Spline):
	"A blended spline is composed of a sequence of tangent curves which sit at the knots; the overall shape of the curve is found by blending together the tangents. The blending is such that, where the tangent to a knot k is given by tan(k), between two knots k and l, at a distance v from k, the curve is (1 - v) * tan(k) + v * tan(l); note that it follows from this that at a knot k, the curve is exactly equal to tan(k)."
	def __getitem__(self, i):
		"Get the ith tangent of the spline (the tangent which applies from (i - 1) < u < (i + 1)). A position u on the spline corresponds to a position v = (u - i) on the piece. An index i is valid iff 0 <= i < len(self)."
		raise NotImplementedError
	def __call__(self, u):
		if (u < 0.0):
			return self[0](u)
		elif (u >= (len(self) - 1)):
			l = len(self) - 1
			return self[l]((u - l))
		else:
			i = int(u)
			v = u - i
			w = 1 - v
			return (self[i](v) * w) + (self[(i + 1)](-w) * v)
	def __len__(self):
		"The length of a blended spline is the number of tangents in it, which is equal to the number of tight knots."
		return len(self.knots) - (2 * getattr(self, "looseKnots", 0))

class BlendedQuadraticSpline(BlendedSpline):
	"Note that tangents are not cached. They probably should be."
	def __getitem__(self, i):
		if (i == 0):
			return Line.fit(self.knots[0], self.knots[1])
		elif (i == (len(self) - 1)):
			end = self.knots[-1]
			prev = self.knots[-2]
			proj = (end * 2.0) - prev
			return Line.fit(end, proj)
		else:
			return Quadratic.fit(self.knots[(i - 1)], self.knots[i], self.knots[(i + 1)])

class BlendedQuarticSpline(BlendedSpline):
	"I'm not going to implement this, but it would be interesting - hopefully, it would be smoother than the quadratic, which, compared to the natural cubic, is a bit angular."
	def __init__(self, knots=None):
		raise NotImplementedError

class BlendedPiecewiseSpline(PiecewiseSpline):
	"I'm not going to implement this. This would be another general kind of spline; the way it would work is that, rather than demanding that the pieces fit together smoothly, it only requires they pass through the knots at each end, and then blends adjacent pieces to produce the final curve. A given interval would be derived by blending the piece for that interval with the piece for the nearest adjacent interval; at knots, the curve would be an even mix of the pieces on each side, and halfway between two knots, it would be purely one piece. The obvious piece curve would be a line, but a cubic (fitted to the adjacent knots and the knots on either side) would also be good, and much smoother. Note that such curves would be local, like other blended splines."
	def __init__(self, knots=None):
		raise NotImplementedError

def test_spline(splinetype=NaturalCubicSpline, trim=False):
	"Fits a spline of some sort through a simple spiral-shaped sequence of knots, and returns a trace along it as a list of 2-tuples. Note that blended splines will have a bit of a tail; set trim to True to trim it off."
	knots = [(0, 0), (0, 1), (1, 0), (0, -2), (-3, 0)] # a spiral
	points = []
	c = splinetype(tuples2points(knots))
	u = 0.0
	du = 0.1
	if (trim):
		lim = (len(c) - 1) + du
	else:
		lim = len(c) + du
	while (u < lim):
		p = c(u)
		points.append(tuple(p))
		u = u + du
	return points
