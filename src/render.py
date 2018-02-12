def check_basecut(svgfn):
    # ensure there is only one path
    svg = parse(svgfn)
    for (cnt, node) in enumerate(svg.getElementsByTagName("path")):
        if cnt > 0:
            return False
    return True

def merge_svg(file_list, color_list, outfn):
    first = None
    idx = 0
    for (svgfn, color) in zip(file_list, color_list):
        svg = parse(svgfn)
        for node in svg.getElementsByTagName("g"):
            if idx == 0:
                # cut layer
                # write a new group
                container = svg.createElement("g")
                container.setAttribute("transform", node.attributes["transform"].nodeValue)
                node.parentNode.replaceChild(container, node)
                container.appendChild(node)
                node.attributes["fill"] = "none"
                node.attributes["stroke"] = "rgb(0, 0, 255)"
                node.attributes["stroke-opacity"] = "1"
                node.attributes["stroke-width"] = ".01mm"
            else:
                node.attributes["fill"] = color
            del node.attributes["transform"]
            idx += 1
            import_nodes = svg.importNode(node, True)
            container.appendChild(import_nodes)
            if first == None:
                first = svg
    f = open(outfn, 'w')
    f.write(first.toxml())

def potrace(svgfn, fn, turd=None, size=None):
    cmd = ["potrace", "-i", "-b", "svg"]
    if turd != None:
        cmd.extend(["-t", str(turd)])
    if size != None:
        sz = map(str, size)
        cmd.extend(["-W", sz[0], "-H", sz[1]])
    cmd.extend(["-o", svgfn, fn])
    cmd = str.join(' ', cmd)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)

# laser cutter pipeline
def pipeline_lasercutter(args, lattice, inches=3, dpi=96, turd=10):
    # layers
    rs = RenderSnowflake(lattice)
    name = str.join('', [c for c in args.name if c.islower()])
    size = args.target_size
    layerfn = "%s_layer_%%d.bmp" % name
    resize = inches * dpi
    fnlist = rs.save_layers(layerfn, 2, resize=resize, margin=1)
    # we want to drop the heaviest layer
    del fnlist[0]
    # try to save o'natural
    imgfn = "%s_bw.bmp" % name
    svgfn = "%s_bw.svg" % name
    lattice.save_image(imgfn, scheme=BlackWhite(lattice), resize=resize, margin=1)
    potrace(svgfn, imgfn, turd=2000)
    if not check_basecut(svgfn):
        msg = "There are disconnected elements in the base cut, turning on boundary layer."
        log(msg)
        lattice.save_image(imgfn, scheme=BlackWhite(lattice, boundary=True), resize=resize, margin=1)
        potrace(svgfn, imgfn, turd=2000)
        assert check_basecut(svgfn), "Despite best efforts, base cut is still non-contiguous."
    os.unlink(svgfn)
    fnlist.insert(0, imgfn)
    # adjusted for ponoko
    # cut layer is blue
    # etch layer are black, or shades of grey
    colors = ["#000000", "#111111", "#222222", "#333333", "#444444", "#555555"]
    svgs = []
    for (idx, fn) in enumerate(fnlist):
        svgfn = os.path.splitext(fn)[0]
        svgfn = "%s_laser.svg" % svgfn
        svgs.append(svgfn)
        if idx == 0:
            potrace(svgfn, fn, turd=turd, size=size)
        else:
            potrace(svgfn, fn, size=size)
    svgfn = "%s_laser_merged.svg" % name
    epsfn = "%s_laser_merged.eps" % name
    merge_svg(svgs, colors, svgfn)
    """
    # move to eps
    cmd = "%s %s -E %s" % (InkscapePath, svgfn, epsfn)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)
    """

# 3d pipeline
def pipeline_3d(args, lattice, inches=3, dpi=96, turd=10):
    resize = inches * dpi
    # try to save o'natural
    imgfn = "%s_bw.bmp" % args.name
    svgfn = "%s_bw.svg" % args.name
    lattice.save_image(imgfn, scheme=BlackWhite(lattice), resize=resize, margin=1)
    potrace(svgfn, imgfn, turd=2000)
    if not check_basecut(svgfn):
        msg = "There are disconnected elements in the base cut, turning on boundary layer."
        log(msg)
        lattice.save_image(imgfn, bw=True, boundary=True)
        potrace(svgfn, imgfn, turd=2000)
        assert check_basecut(svgfn), "Despite best efforts, base cut is still non-contiguous."
    #
    epsfn = "%s_3d.eps" % args.name
    dxffn = "%s_3d.dxf" % args.name
    cmd = "potrace -M .1 --tight -i -b eps -o %s %s" % (epsfn, imgfn)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)
    #
    cmd = "pstoedit -dt -f dxf:-polyaslines %s %s" % (epsfn, dxffn)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)
    #
    scad_fn = "%s_3d.scad" % args.name
    stlfn = "%s_3d.stl" % args.name
    f = open(scad_fn, 'w')
    scad_txt = 'scale([30, 30, 30]) linear_extrude(height=.18, layer="0") import("%s");\n' % dxffn
    f.write(scad_txt)
    f.close()
    cmd = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD -o %s %s" % (stlfn, scad_fn)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)
    #
    cmd = "python /Applications/Cura/Cura.app/Contents/Resources/Cura/cura.py -s %s -i %s" % (stlfn, SNOWFLAKE_INI)
    msg = "Running '%s'" % cmd
    log(msg)
    os.system(cmd)

SNOWFLAKE_DEFAULTS = {
    "size": 200,
    "name": "snowflake",
    "bw": False,
    "env": '',
    "pipeline_3d": False,
    "pipeline_lasercutter": False,
    "randomize": False,
    "max_steps": 0,
    "margin": .85,
    "curves": False,
    "datalog": False,
    "debug": False,
    "movie": False,
}


