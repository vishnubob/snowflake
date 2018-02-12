def run(args):
    log_output(args.name)
    msg = "Snowflake Generator v0.3"
    log(msg)
    pfn = "%s.pickle" % args.name
    ifn = "%s.png" % args.name
    if os.path.exists(pfn):
        cl = CrystalLattice.load_lattice(pfn)
        #cl.save_image(ifn, bw=args.bw)
        #cl.save_image(ifn)
    else:
        kw = {}
        if args.env:
            mods = {key: float(val) for (key, val) in [keyval.split('=') for keyval in args.env.split(',')]}
            env = CrystalEnvironment(mods)
            kw["environment"] = env
        elif args.randomize:
            env = CrystalEnvironment()
            env.randomize()
            msg = str.join(', ', ["%s=%.6f" % (key, env[key]) for key in env])
            log(msg)
            kw["environment"] = env
        elif args.curves:
            env = CrystalEnvironment.build_env(args.name, 50000)
            kw["environment"] = env
        kw["max_steps"] = args.max_steps
        kw["margin"] = args.margin
        kw["datalog"] = args.datalog
        kw["debug"] = args.debug
        cl = CrystalLattice(args.size, **kw)
        try:
            cl.grow()
        finally:
            cl.write_log()
            cl.save_lattice(pfn)
            #cl.save_image(ifn, bw=args.bw)
            cl.save_image(ifn)
    if args.pipeline_3d:
        pipeline_3d(args, cl)
    if args.pipeline_lasercutter:
        pipeline_lasercutter(args, cl)
    if args.movie:
        movie = RenderMovie(args.name)
        movie.run()

