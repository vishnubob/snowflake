#!/usr/bin/env pypy
import cPickle as pickle
import os
from snowflake import *

def add_example(name):
    print "Processing %s..." % name
    ret = ''
    pfn = "%s.pickle" % name
    f = open(pfn)
    sf = pickle.load(f)
    env = sf.environment
    env_keys = env.keys()
    env_keys.sort()
    caption = ["%s = %s" % (key, env[key]) for key in env_keys]
    caption = str.join(', ', caption)
    ret += "<div style='border: 2px'>\n"
    ret += "<h1>%s</h1>\n" % name
    ret += "<img src='%s.bmp' width = '200'/>\n" % name
    ret += "<p />%s\n" % caption
    ret += "</div>\n"
    return ret

HTML = """<html><head><title>Mah Sn0wFl4K3z!@!##@</title></head>
<body>%s</body>
</html>"""

if __name__ == "__main__":
    body = ''
    for fn in os.listdir("."):
        if fn.endswith(".pickle"):
            body += add_example(fn.split(".")[0])
    html = HTML % body
    fn = "snowflakes.html"
    f = open(fn, 'w')
    f.write(html)
