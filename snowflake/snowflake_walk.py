import os
from snowflake import *

def steps(low, high, step):
	val = low
	while val < high:
		yield val
		val += step


cnt = 0
base_fn = "snowflake_beta_%03d"

for beta_val in steps(0.8, 1.2, 0.05):
	for gamma_val in steps(0.3, 0.6, 0.02):
		ifn = (base_fn % cnt) + ".bmp"
		lfn = (base_fn % cnt) + ".pickle"
		if os.path.exists(lfn):
			print "Found %s, skipping..." % ifn
			cnt += 1
			continue
		print beta_val
		env = CrystalEnvironment()
		env["beta"] = beta_val
		env["gamma"] = gamma_val
		cl = CrystalLattice(300, environment=env)
		cl.grow()
		cnt += 1
		cl.save_image(ifn)
		cl.save_lattice(lfn)
