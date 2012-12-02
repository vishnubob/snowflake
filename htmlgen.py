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

    def add_example(self, name):
        print "Processing %s..." % name
        pfn = "%s.pickle" % name
        f = open(pfn)
        sf = pickle.load(f)
        env = sf.environment
        env_keys = env.keys()
        env_keys.sort()
	caption = "%s=%s %s=%s" % (env_keys[1], env[env_keys[1]],env_keys[2], env[env_keys[2]])      
	#caption = ["%s = %s" % (key, env[key]) for key in env_keys]
        #caption = str.join('\n', caption)
        content = ''
        #content += "%s\n" % name
        content += "<img src='%s.bmp' style='height:300px; top:-100px'/>\n" % name
        content += "<p />%s\n" % caption
        self.add_cell(content)

    def add_cell(self, content):
        if len(self.row) >= self.ppr:
            self.table.append(self.row)
            self.row = []
        self.row.append(content)

    def render(self):
        if self.row:
            self.table.append(self.row)
        table = ''
        for row in self.table:
            html_row = ''
            for cell in row:
                html_row += "<td>%s</td>\n" % cell
            table += "<tr>%s</tr>\n" % html_row
        return "<table>%s</table\n" % table

HTML = """<html><head><title>Mah Sn0wFl4K3z!@!##@</title></head>
<body>%s</body>
</html>"""

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
