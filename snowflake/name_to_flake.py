import os
import string
from snowflake import *

friend_name = raw_input('What is your name? Enter it here: ')
print "Great, thanks.  I will make you a snowflake."
#flake_size = raw_input('But first, how big do you want it (heh, heh)?  Smaller sizes are faster output.  Integers only please.  300 is a good start.: ')

base_fn = "second_snowflake_for_%s" % friend_name

def sanitize_text(friend_name):
	for char in friend_name:
		if char not in string.letters:
			friend_name = string.replace(friend_name, char, '')
	return str.lower(friend_name)

def name_val(name):
	nameval = 0
	for letter in name:
		nameval += ord(letter)-ord('a') + 1
	return nameval

archetype_list = [SpikeEndFlake(), FernFlake(), ClassicFlake(), DelicateFlake(), RandomBeautyFlake()]

def archetype_chooser(name):
	print name[0]
	if name[0] in 'abcde':
		print 'Caution:  You are a Spike End Flake (sharp!)'
		flake_type = SpikeEndFlake()
	elif name[0] in 'fghij':
		print 'Looks like you\'re what I call a Fern Flake (many fingered and soft to the touch, rawr)'
		flake_type = FernFlake()
	elif name[0] in 'klmno':
		print 'You are a Classic Flake (you\'ve got excellent form)'
		flake_type = ClassicFlake()
	elif name[0] in 'pqrst':
		print 'I\'ve determined that you are a Delicate Snowflake (har)'
		flake_type = DelicateFlake()
	else:
		print 'Your etheral beauty cannot be captured except to say that you are a Random Beauty of a Snowflake'
		flake_type = RandomBeautyFlake()
	return flake_type

def archetype_chooser_2(nameval):
	flake_type = archetype_list[nameval % len(archetype_list)]
	return flake_type


def makeflake(flake):
	ifn = (base_fn) + ".bmp"
	lfn = (base_fn) + ".pickle"
	if os.path.exists(lfn):
		print "Found %s, skipping..." % ifn
	print flake
	cl = CrystalLattice(500, environment=flake)
	cl.grow()
	cl.save_image(ifn)
	cl.save_lattice(lfn)

sanitized_name = sanitize_text(friend_name)

namevalue = name_val(sanitized_name)
print 'Your namevalue is ', namevalue

#flakity = archetype_chooser(sanitized_name)
flakity = archetype_chooser_2(namevalue)
print 'the flake values are',flakity
print type(flakity)

#for key in flakity:
#	flakity[key] = flakity[key] - (flakity[key])* (1/float(len(sanitized_name)))


for key in flakity:
	if flakity[key] == 0:
		continue
	if int(1/flakity[key]) % 2:
		print 'make ', key, 'a little bit bigger'
		flakity[key] = 1.0 / ((1.0/flakity[key]) * (1.0 - 1.0/float(namevalue)))
	else:
		print 'make ',key,'a little bit smaller'
		flakity[key] = 1.0 / ((1.0/flakity[key]) * (1.0 + 1.0/float(len(sanitized_name))))

print 'the customized flake values are', flakity

makeflake(flakity)





