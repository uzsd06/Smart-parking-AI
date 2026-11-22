"""Member C's data layer: read-only queries, notifications, analytics helpers.
Adds new code only - it never edits A's or B's files."""
import random
import pandas as pd
from database.db import get_connection


def ensure_tables():
    """Create the notifications table (kept out of B's schema.sql on purpose)."""
    con = get_connection()
    con.execute("""CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_read INTEGER NOT NULL DEFAULT 0)""")
    con.commit()
    con.close()


_SQL = """
SELECT b.booking_id, b.user_id, u.name AS user_name, v.registration_number AS vehicle,
       v.vehicle_type, p.slot_number, b.arrival_time, b.duration, b.destination_gate,
       b.requires_charging, b.status, b.created_at
FROM bookings b
JOIN users u ON u.user_id = b.user_id
JOIN vehicles v ON v.vehicle_id = b.vehicle_id
LEFT JOIN parking_slots p ON p.slot_id = b.slot_id
"""


def all_bookings():
    """Every booking as a DataFrame, with slot numbers and start/end datetimes."""
    con = get_connection()
    try:
        df = pd.read_sql_query(_SQL + " ORDER BY b.arrival_time DESC", con)
    finally:
        con.close()
    if df.empty:
        df["arrival"] = pd.Series(dtype="datetime64[ns]")
        df["end"] = pd.Series(dtype="datetime64[ns]")
        return df
    try:
        df["arrival"] = pd.to_datetime(df["arrival_time"], format="ISO8601")
    except (TypeError, ValueError):
        df["arrival"] = pd.to_datetime(df["arrival_time"])
    df["end"] = df["arrival"] + pd.to_timedelta(df["duration"], unit="h")
    return df


def user_bookings(user_id):
    df = all_bookings()
    return df[df.user_id == user_id].reset_index(drop=True)


def lot_at(when):
    """One row per slot with its status at time `when`: available/occupied/blocked/maintenance."""
    from backend.parking_slots import get_all_slots
    slots = pd.DataFrame(get_all_slots(),
                         columns=["slot_id", "slot_number", "slot_type", "gate", "db_status"])
    bk = all_bookings()
    bk = bk[bk.status.isin(["allocated", "checked-in"]) & bk.slot_number.notna()]
    busy = set(bk[(bk.arrival <= when) & (bk.end > when)].slot_number)
    slots["status"] = [
        s if s != "available" else ("occupied" if n in busy else "available")
        for n, s in zip(slots.slot_number, slots.db_status)]
    return slots


# ---------- notifications ----------
def _snapshot():
    return {r.booking_id: (r.user_id, r.slot_number, r.status) for r in all_bookings().itertuples()}


def run_and_notify(fn, *args, **kwargs):
    """Call an integration function, then tell users whose slot changed because of it.
    Returns (result_of_fn, list_of_messages)."""
    before = _snapshot()
    result = fn(*args, **kwargs)
    after = _snapshot()
    notes = []
    for bid, (uid, slot, status) in after.items():
        if bid not in before:
            continue
        _, old, old_status = before[bid]
        if status == "cancelled" or old_status in ("checked-in", "completed", "cancelled") or old == slot:
            continue
        if old and slot:
            msg = f"Booking #{bid}: your slot changed from {old} to {slot} after re-optimisation."
        elif slot:
            msg = f"Booking #{bid}: you have been allocated slot {slot}."
        else:
            msg = f"Booking #{bid}: you were moved to the waiting list."
        notes.append((uid, msg))
    if notes:
        con = get_connection()
        con.executemany("INSERT INTO notifications (user_id, message) VALUES (?, ?)", notes)
        con.commit()
        con.close()
    return result, [m for _, m in notes]


def unread_notifications(user_id):
    con = get_connection()
    try:
        return con.execute("SELECT id, message, created_at FROM notifications "
                           "WHERE user_id = ? AND is_read = 0 ORDER BY id DESC", (user_id,)).fetchall()
    finally:
        con.close()


def mark_all_read(user_id):
    con = get_connection()
    con.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    con.commit()
    con.close()


# ---------- AI vs baselines (for the results slide) ----------
def ai_vs_baselines():
    """Score the current Hill Climbing allocation against Random and First-available
    allocations of the SAME active bookings, using Member A's fitness (higher = better)."""
    from integration import load_slots_from_database, load_active_bookings
    from hill_climbing import fitness, is_compatible, has_time_conflict
    slots = load_slots_from_database()
    reqs, alloc, _ = load_active_bookings()
    if not reqs or not slots:
        return None
    ids = {s.slot_id for s in slots}
    hc = [a if a in ids else None for a in alloc]

    def greedy(slot_order):
        state = [None] * len(reqs)
        for i, r in enumerate(reqs):
            for s in slot_order:
                if is_compatible(r, s) and not any(
                        state[j] == s.slot_id and has_time_conflict(r, reqs[j]) for j in range(i)):
                    state[i] = s.slot_id
                    break
        return state

    shuffled = slots[:]
    random.Random(0).shuffle(shuffled)
    lookup = {s.slot_id: s for s in slots}
    rows = []
    for name, state in [("Random", greedy(shuffled)),
                        ("First available", greedy(sorted(slots, key=lambda s: s.slot_id))),
                        ("Hill Climbing (current)", hc)]:
        done = [(r, lookup[x]) for r, x in zip(reqs, state) if x]
        dist = sum(s.gate_distances.get(r.destination_gate, 30) for r, s in done)
        rows.append({"Method": name, "Fitness score": fitness(reqs, slots, state),
                     "Allocated": len(done), "Unallocated": len(reqs) - len(done),
                     "Avg gate distance (m)": round(dist / len(done), 1) if done else 0})
    return pd.DataFrame(rows)
