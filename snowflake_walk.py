from snowflake import *

def steps(low, high, step):
	val = low
	while val < high:
		yield val
		val += step


cnt = 0
base_fn = "snowflake_beta_%03d"

for beta_val in steps(0.8, 1.2, 0.05):
	for gamma_val in steps(0.3, 0.9, 0.01):
		print beta_val
		env = CrystalEnvironment()
		env["beta"] = beta_val
		env["gamma"] = gamma_val
		cl = CrystalLattice(100, environment=env)
		cl.grow()
		ifn = (base_fn % cnt) + ".bmp"
		lfn = (base_fn % cnt) + ".pickle"
		cnt += 1
		cl.save_image(ifn)
		cl.save_lattice(lfn)
