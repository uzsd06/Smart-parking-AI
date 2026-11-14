"""SmartPark AI dashboard.  Run:  streamlit run app.py"""
import numpy as np, pandas as pd, streamlit as st
import matplotlib.pyplot as plt
from smartpark_core import *

st.set_page_config("SmartPark AI", layout="wide")
st.title("🅿️ SmartPark AI – Congestion-Aware Parking Optimisation (Hill Climbing)")

sb = st.sidebar
sb.header("Scenario")
rows = sb.slider("Aisles (rows)", 3, 10, 6)
cols = sb.slider("Bays per aisle", 6, 14, 10)
occ = sb.slider("Already occupied %", 0, 70, 30) / 100
nveh = sb.slider("Incoming vehicles", 5, 40, 20)
seed = sb.number_input("Random seed", 0, 999, 1)
sb.header("Heuristic weights")
w = (sb.slider("w1  distance", 0.0, 3.0, 1.0, 0.1),
     sb.slider("w2  congestion", 0.0, 3.0, 1.0, 0.1),
     sb.slider("w3  priority mismatch", 0.0, 3.0, 1.0, 0.1))
sb.header("Algorithm")
restarts = sb.slider("Random restarts", 2, 30, 10)
k = sb.slider("Neighbours sampled / step", 50, 1500, 300, 50)


@st.cache_data(show_spinner="Optimising…")
def solve(rows, cols, occ, nveh, w, seed, restarts, k):
    lot = Lot(rows, cols, occ, seed)
    veh = make_vehicles(lot, min(nveh, int(lot.free.sum())), seed)
    return lot, veh, run_all(lot, veh, w, seed, restarts, k)


lot, veh, res = solve(rows, cols, occ, nveh, w, seed, restarts, k)


def draw(lot, veh, a, title):
    fig, ax = plt.subplots(figsize=(6, 4.6))
    for kd in range(4):
        m = (lot.kind == kd) & lot.free
        ax.scatter(*lot.xy[m].T, c=COLOR[kd], s=170, marker="s", label=KIND[kd], zorder=2)
    ax.scatter(*lot.xy[~lot.free].T, c="#555", s=170, marker="s", label="Occupied", zorder=2)
    for i, s in enumerate(a):
        ax.text(*lot.xy[s], str(i), ha="center", va="center", fontsize=7, zorder=4,
                color="white" if veh.kind[i] else "black",
                bbox=dict(boxstyle="circle,pad=0.15", fc="red" if veh.kind[i] else "yellow", ec="k", lw=.5))
    ax.scatter(*lot.gates.T, marker="^", c="k", s=90, label="Gate", zorder=3)
    ax.scatter(*lot.entrance, marker="*", c="gold", ec="k", s=220, label="Entrance", zorder=3)
    ax.set_title(title, fontsize=10); ax.axis("off")
    ax.legend(fontsize=6, ncol=4, loc="upper center", bbox_to_anchor=(.5, -.01))
    return fig


t_map, t_opt, t_cmp, t_exp, t_live = st.tabs(
    ["Parking map", "Optimisation", "Comparison", "Experiments", "Live simulation"])

with t_map:
    c1, c2 = st.columns(2)
    for col, name in ((c1, "First available"), (c2, "Hill climbing")):
        col.pyplot(draw(lot, veh, res[name]["a"], f"{name} – cost {res[name]['cost']:.0f}"))
    st.caption("Numbered discs = incoming vehicles (red = EV / accessible / reserved, yellow = regular). "
               "Grey = already occupied.")
    imp = 100 * (1 - res["Hill climbing"]["cost"] / res["First available"]["cost"])
    st.metric("Cost reduction vs first-available", f"{imp:.1f}%")

with t_opt:
    c1, c2 = st.columns(2)
    fig, ax = plt.subplots()
    for n in ("Hill climbing", "Random-restart HC", "Simulated annealing"):
        ax.plot(res[n]["hist"], label=n)
    ax.set_xlabel("Iteration"); ax.set_ylabel("Cost"); ax.set_title("Convergence"); ax.legend()
    c1.pyplot(fig)
    bd = pd.DataFrame({n: [w[0] * r["D"], w[1] * r["C"], w[2] * r["P"]] for n, r in res.items()},
                      index=["Distance", "Congestion", "Priority"]).T
    fig, ax = plt.subplots(); bd.plot.bar(stacked=True, ax=ax); ax.set_title("Cost breakdown")
    plt.xticks(rotation=30, ha="right"); c2.pyplot(fig)

with t_cmp:
    df = pd.DataFrame(res).T[["cost", "D", "C", "P", "mismatch", "load_std", "iters", "time"]]
    df.columns = ["Total cost", "Distance", "Congestion", "Priority", "Type mismatches",
                  "Aisle-load std-dev", "Iterations", "Time (s)"]
    st.dataframe(df.astype(float).round(2), use_container_width=True)
    fig, ax = plt.subplots(figsize=(8, 3.5)); df["Total cost"].plot.bar(ax=ax, color="#3182bd")
    plt.xticks(rotation=25, ha="right"); st.pyplot(fig)

with t_exp:
    st.write("Sweep one parameter and average over several random scenarios.")
    param = st.selectbox("Parameter", ["Number of vehicles", "Occupancy %", "Congestion weight w2"])
    runs = st.slider("Scenarios per point", 3, 15, 5)
    if st.button("Run experiment"):
        grid = {"Number of vehicles": [8, 14, 20, 26, 32],
                "Occupancy %": [10, 25, 40, 55],
                "Congestion weight w2": [0.0, 0.5, 1.0, 2.0, 3.0]}[param]
        rows_out, bar = [], st.progress(0.0)
        for gi, g in enumerate(grid):
            for s in range(runs):
                o = (occ if param != "Occupancy %" else g / 100)
                nv = nveh if param != "Number of vehicles" else g
                ww = w if param != "Congestion weight w2" else (w[0], g, w[2])
                L = Lot(rows, cols, o, s); V = make_vehicles(L, min(nv, int(L.free.sum())), s)
                r = run_all(L, V, ww, s, 3, 200, with_sa=False)
                for n in ("Random", "First available", "Greedy nearest", "Hill climbing"):
                    rows_out.append((g, n, r[n]["cost"]))
            bar.progress((gi + 1) / len(grid))
        d = pd.DataFrame(rows_out, columns=[param, "Method", "Cost"]).groupby([param, "Method"]).Cost.mean().unstack()
        st.line_chart(d); st.dataframe(d.round(1))

with t_live:
    st.write("Vehicles that are still **en route** can be re-assigned when the situation changes; "
             "parked vehicles stay locked.")
    window = st.slider("En-route vehicles (re-optimisable)", 1, 10, 5)
    if "sim" not in st.session_state or st.button("Reset simulation"):
        st.session_state.sim = [lot, Vehicles(veh.kind.copy(), veh.dest.copy()), res["Hill climbing"]["a"].copy()]
        st.session_state.log = []
    L, V, A = st.session_state.sim

    def reoptimise(A, V, label):
        before = cost(A, L, V, w)
        mov = range(max(0, len(A) - window), len(A))
        A2, _ = hill_climb(L, V, w, A, movable=mov, k=300, rng=np.random.default_rng())
        st.session_state.log.append(f"{label}: cost {before:.0f} → {cost(A2, L, V, w):.0f}")
        return A2

    b1, b2 = st.columns(2)
    if b1.button("🚗 Vehicle arrives"):
        spare = [s for s in np.flatnonzero(L.free) if s not in set(A.tolist())]
        if spare:
            nv = make_vehicles(L, 1, int(np.random.randint(1e6)))
            V = Vehicles(np.append(V.kind, nv.kind), np.vstack([V.dest, nv.dest]))
            A = reoptimise(np.append(A, spare[0]), V, "Arrival re-allocation")
        else:
            st.warning("Lot is full.")
    if b2.button("🚙 Random vehicle leaves") and len(A) > 1:
        i = np.random.randint(len(A))
        A, V = np.delete(A, i), Vehicles(np.delete(V.kind, i), np.delete(V.dest, i, axis=0))
        A = reoptimise(A, V, "Departure re-allocation")
    st.session_state.sim = [L, V, A]
    st.pyplot(draw(L, V, A, f"Live lot – {len(A)} vehicles, cost {cost(A, L, V, w):.0f}"))
    for line in st.session_state.log[-6:][::-1]:
        st.write("• " + line)
