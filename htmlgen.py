#!/usr/bin/env pypy
import cPickle as pickle
import os
import Image
from snowflake import *

class ExampleTable(object):
    def __init__(self, pics_per_row=15):
        self.ppr = pics_per_row
        self.table = []
        self.row = []
        self.load_cache()

    def load_cache(self):
        fn = "htmlgen_cache.dill"
        try:
            f = open(fn)
            self._cache = pickle.load(f)
        except:
            self._cache = {}
    
    def save_cache(self):
        fn = "htmlgen_cache.dill"
        f = open(fn, 'w')
        pickle.dump(self._cache, f)

    def get(self, name):
        if name not in self._cache:
            pfn = "%s.pickle" % name
            f = open(pfn)
            sf = pickle.load(f)
            env = dict(sf.environment)
            self._cache[name] = env
        return self._cache[name]

    def add_example(self, name):
        print "Processing %s..." % name
        env = self.get(name)
        env_keys = env.keys()
        env_keys.sort()
        caption = "%s=%s %s=%s" % (env_keys[1], env[env_keys[1]],env_keys[2], env[env_keys[2]])      
        #caption = ["%s = %s" % (key, env[key]) for key in env_keys]
        #caption = str.join('\n', caption)
        content = ''
        content += "%s\n" % name
        content += "<div class='crop'>\n"
        content += "<img src='%s.bmp' style='height:300px; top:-100px'/>\n" % name
        content += "</div>\n"
        content += "<p />%s\n" % caption
        self.add_cell(content)

    def add_cell(self, content):
        if len(self.row) >= self.ppr:
            self.table.append(self.row)
            self.row = []
        self.row.append(content)

    def render(self):
        self.save_cache()
        if self.row:
            self.table.append(self.row)
        table = ''
        for row in self.table:
            html_row = ''
            for cell in row:
                html_row += "<td>%s</td>\n" % cell
            table += "<tr>%s</tr>\n" % html_row
        return "<table border='1px'>%s</table\n" % table

HTML = """
<html>
<head>
<style>
.crop { width: 200px; height: 150px; overflow: hidden; }
.crop img { width: 400px; height: 300px; margin: -75px 0 0 -100px; }
</style>
<title>Mah Sn0wFl4K3z!@!##@</title></head>
<body>%s</body>
</html>
"""

if __name__ == "__main__":
    body = ''
    table = ExampleTable()
    for fn in os.listdir("."):
        if fn.endswith(".pickle"):
            table.add_example(fn.split(".")[0])
    html = HTML % table.render()
    fn = "snowflakes.html"
    f = open(fn, 'w')
    f.write(html)
