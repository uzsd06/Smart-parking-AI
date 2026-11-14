"""SmartPark AI - core engine: lot model, multi-factor cost, search algorithms."""
import itertools, math, time
import numpy as np

REG, EV, ACC, RES = range(4)
KIND = ["Regular", "EV", "Accessible", "Reserved"]
COLOR = ["#9ecae1", "#74c476", "#fd8d3c", "#9e9ac8"]
# PEN[vehicle_kind][slot_kind]: penalty for parking a vehicle in that slot type
PEN = np.array([[0, 30, 60, 60],
                [50, 0, 60, 60],
                [40, 40, 0, 60],
                [30, 30, 60, 0]], float)


class Lot:
    def __init__(self, rows=6, cols=10, occ=0.3, seed=0):
        rng = np.random.default_rng(seed)
        n = rows * cols
        r, c = np.divmod(np.arange(n), cols)
        self.rows, self.cols = rows, cols
        self.xy = np.c_[c * 3.0, r * 6.0]            # 3 m bays, 6 m aisle pitch
        self.zone = r                                 # one aisle per row
        kind = np.full(n, REG)
        kind[(c == cols - 1) & (r < 3)] = EV
        kind[(r == rows - 1) & (c < 2)] = ACC
        kind[(r == rows - 1) & ((c == 2) | (c == 3))] = RES
        self.kind = kind
        self.free = rng.random(n) > occ
        self.entrance = np.array([0.0, -6.0])
        top = rows * 6 + 3.0
        self.gates = np.array([[0, top], [cols * 1.5, top], [cols * 3.0, top]])
        self.base = 4.0 * (1 - np.arange(rows) / rows)   # aisles near entrance are busier


class Vehicles:
    def __init__(self, kind, dest):
        self.kind, self.dest = np.asarray(kind), np.asarray(dest, float)

    def __len__(self):
        return len(self.kind)


def make_vehicles(lot, n, seed=0):
    rng = np.random.default_rng(seed + 1)
    kind = rng.choice(4, n, p=[0.7, 0.15, 0.1, 0.05])
    dest = lot.gates[rng.integers(0, len(lot.gates), n)]
    return Vehicles(kind, dest)


# ---------- heuristic (cost) function:  Cost = w1*D + w2*C + w3*P ----------
def breakdown(a, lot, veh):
    xy = lot.xy[a]
    D = np.abs(xy - veh.dest).sum() + 0.3 * np.abs(xy - lot.entrance).sum()
    n = np.bincount(lot.zone[a], minlength=lot.rows)
    C = (lot.base * n + 3.0 * n ** 2 / lot.cols).sum()   # non-additive: depends on the whole state
    P = PEN[veh.kind, lot.kind[a]].sum()
    return D, C, P


def cost(a, lot, veh, w):
    D, C, P = breakdown(a, lot, veh)
    return w[0] * D + w[1] * C + w[2] * P


# ---------- neighbourhood ----------
def moves(a, movable, slots, k, rng):
    used = set(a.tolist())
    spare = [s for s in slots if s not in used]
    m = [("swap", i, j) for i, j in itertools.combinations(movable, 2)]
    m += [("move", i, s) for i in movable for s in spare]
    if len(m) > k:
        m = [m[x] for x in rng.choice(len(m), k, replace=False)]
    return m


def apply(a, mv):
    b = a.copy()
    if mv[0] == "swap":
        b[mv[1]], b[mv[2]] = a[mv[2]], a[mv[1]]
    else:
        b[mv[1]] = mv[2]
    return b


def random_move(a, movable, slots, rng):
    used = set(a.tolist())
    spare = [s for s in slots if s not in used]
    if spare and (len(movable) < 2 or rng.random() < 0.5):
        return ("move", int(rng.choice(movable)), int(rng.choice(spare)))
    if len(movable) >= 2:
        i, j = rng.choice(movable, 2, replace=False)
        return ("swap", int(i), int(j))
    return None


# ---------- algorithms ----------
def hill_climb(lot, veh, w, init, movable=None, k=300, max_iter=300, rng=None):
    """Steepest-ascent (here: steepest-descent on cost) hill climbing."""
    rng = rng or np.random.default_rng()
    movable = list(range(len(init))) if movable is None else list(movable)
    slots = np.flatnonzero(lot.free)
    a, cur = init.copy(), cost(init, lot, veh, w)
    hist = [cur]
    for _ in range(max_iter):
        best, best_c = None, cur
        for mv in moves(a, movable, slots, k, rng):
            b = apply(a, mv)
            c = cost(b, lot, veh, w)
            if c < best_c - 1e-9:
                best, best_c = b, c
        if best is None:          # no better neighbour -> local optimum
            break
        a, cur = best, best_c
        hist.append(cur)
    return a, hist


def random_restart(lot, veh, w, restarts=10, k=300, rng=None):
    rng = rng or np.random.default_rng()
    slots = np.flatnonzero(lot.free)
    best, best_h, total_iters = None, None, 0
    for _ in range(restarts):
        init = rng.choice(slots, len(veh), replace=False)
        a, h = hill_climb(lot, veh, w, init, k=k, rng=rng)
        total_iters += len(h) - 1
        if best is None or h[-1] < best_h[-1]:
            best, best_h = a, h
    return best, best_h, total_iters


def anneal(lot, veh, w, init, T0=40.0, alpha=0.995, steps=2500, rng=None):
    rng = rng or np.random.default_rng()
    slots = np.flatnonzero(lot.free)
    movable = list(range(len(init)))
    a, cur = init.copy(), cost(init, lot, veh, w)
    best, best_c, T, hist = a.copy(), cur, T0, [cur]
    for _ in range(steps):
        mv = random_move(a, movable, slots, rng)
        if mv is None:
            break
        b = apply(a, mv)
        c = cost(b, lot, veh, w)
        if c < cur or rng.random() < math.exp(-(c - cur) / max(T, 1e-9)):
            a, cur = b, c
            if cur < best_c:
                best, best_c = a.copy(), cur
        T *= alpha
        hist.append(best_c)
    return best, hist


def greedy_nearest(lot, veh):
    slots, taken, a = np.flatnonzero(lot.free), set(), []
    for i in range(len(veh)):
        s = min((s for s in slots if s not in taken), key=lambda s: np.abs(lot.xy[s] - veh.dest[i]).sum())
        taken.add(s)
        a.append(s)
    return np.array(a)


def run_all(lot, veh, w, seed=0, restarts=10, k=300, with_sa=True):
    rng = np.random.default_rng(seed)
    slots, V, out = np.flatnonzero(lot.free), len(veh), {}

    def record(name, fn):
        t = time.perf_counter()
        r = fn()
        a, h = r[0], r[1]
        iters = r[2] if len(r) > 2 else len(h) - 1
        D, C, P = breakdown(a, lot, veh)
        out[name] = dict(a=a, hist=h, iters=iters, time=time.perf_counter() - t, D=D, C=C, P=P,
                         cost=w[0] * D + w[1] * C + w[2] * P,
                         mismatch=int((veh.kind != lot.kind[a]).sum()),
                         load_std=float(np.bincount(lot.zone[a], minlength=lot.rows).std()))

    rnd = rng.choice(slots, V, replace=False)
    first = slots[:V]
    record("Random", lambda: (rnd, [cost(rnd, lot, veh, w)]))
    record("First available", lambda: (first, [cost(first, lot, veh, w)]))
    g = greedy_nearest(lot, veh)
    record("Greedy nearest", lambda: (g, [cost(g, lot, veh, w)]))
    record("Hill climbing", lambda: hill_climb(lot, veh, w, first, k=k, rng=rng))
    record("Random-restart HC", lambda: random_restart(lot, veh, w, restarts, k, rng))
    if with_sa:
        record("Simulated annealing", lambda: anneal(lot, veh, w, first, rng=rng))
    return out


if __name__ == "__main__":
    lot = Lot(6, 10, 0.3, seed=1)
    veh = make_vehicles(lot, 20, seed=1)
    for name, r in run_all(lot, veh, (1, 1, 1), seed=1).items():
        print(f"{name:22s} cost={r['cost']:8.1f}  iters={r['iters']:4d}  time={r['time']:.2f}s  mismatches={r['mismatch']}")
