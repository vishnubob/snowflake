class RenderMovie(object):
    def __init__(self, name):
        self.name = name
        self.replay = LatticeReplay(name)

    def run(self):
        if not os.path.exists("frames"):
            os.mkdir("frames")
        x = iter(self.replay)
        for (idx, frame) in enumerate(self.replay):
            fn = "frames/%s_%09d.png" % (self.name, idx + 1)
            frame.save_image(fn)

class LatticeReplay(object):
    class ReplayIterator(object):
        def __init__(self, replay):
            self.replay = replay
            self.idx = 0

        def next(self):
            try:
                lattice = self.replay.get_lattice(self.idx)
                self.idx += 1
                return lattice
            except IndexError:
                raise StopIteration

    def __init__(self, name):
        self.name = name
        self.current_frame = None
        self.current_replay = None
        pfn = "%s.pickle" % self.name
        self.lattice = CrystalLattice.load_lattice(pfn)
        self.scan_replays()

    def __iter__(self):
        return self.ReplayIterator(self)

    def get_lattice(self, step):
        (step, dm, cm) = self.get_step(step)
        for (idx, cell) in enumerate(zip(dm, cm)):
            self.lattice.cells[idx].diffusive_mass = cell[0]
            self.lattice.cells[idx].crystal_mass = cell[1]
            self.lattice.cells[idx].attached = bool(cell[1])
        for cell in self.lattice.cells:
            cell.update_boundary()
        return self.lattice

    def get_step(self, step):
        idx = bisect.bisect_left(self.replay_map, step + 1)
        if self.current_frame != idx or not self.current_replay:
            self.current_frame = idx
            fn = self.replays[self.current_frame]
            print "loading", fn
            f = open(fn)
            self.current_replay = pickle.load(f)
        offset = self.current_replay[0][0]
        return self.current_replay[step - offset]

    def scan_replays(self):
        replays = []
        fn_re = re.compile("cell_log_(\d+).pickle")
        for fn in os.listdir('.'):
            m = fn_re.search(fn)
            if m:
                step = int(m.group(1))
                replays.append((fn, step))
        replays.sort(key=operator.itemgetter(1))
        self.replays = [rp[0] for rp in replays]
        self.replay_map = [rp[1] for rp in replays]


