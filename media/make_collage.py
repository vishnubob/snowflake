#!/usr/bin/env python

import random
import argparse
from PIL import Image

random.seed("i am a big purple potato")

parser = argparse.ArgumentParser()

parser.add_argument('-g', '--grid', default=None)
parser.add_argument('-o', '--output', default='collage.jpg')
parser.add_argument('images', nargs='+')

args = parser.parse_args()

n = len(args.images)
print 'reading %d images: %r' % (n, args.images)

if args.grid:
    (grid_width, grid_height) = map(int, args.grid.split('x'))
else:
    (grid_width, grid_height) = n, 1

images = []
target_size = 1000

random.shuffle(args.images)

for path in args.images:
    image = Image.open(path)
    (width, height) = image.size
    ratio = width / float(height)
    new_width = int(target_size * ratio)
    new_height = int(target_size / ratio)
    if new_width > target_size:
        image = image.resize((new_width, target_size))
        left_pad = (new_width - target_size) / 2
        image = image.crop((left_pad, 0, left_pad + target_size, target_size))
    else:
        image = image.resize((target_size, new_height))
        upper_pad = (new_width - target_size) / 2
        image = image.crop((0, upper_pad, target_size, upper_pad + target_size))
    (new_width, new_height) = image.size
    print "(%s x %s) -> (%s x %s)" % (width, height, new_width, new_height)
    images.append(image)

collage = Image.new('RGB', (target_size * grid_width, target_size * grid_height))

for (idx, image) in enumerate(images):
    x = idx % grid_width
    y = idx / grid_width
    if y > grid_height:
        break
    collage.paste(image.copy(), (x * target_size, y * target_size))

collage.save(open("collage_huge.png", 'wb'))
# large
large = collage.resize((4096, 4096))
large.save(open("collage_large.jpg", 'wb'))
# medium
medium = collage.resize((1024, 1024))
medium.save(open("collage_medium.jpg", 'wb'))
# small
medium = collage.resize((640, 640))
medium.save(open("collage_medium.jpg", 'wb'))
# small
small = collage.resize((200, 200))
small.save(open("collage_small.jpg", 'wb'))
