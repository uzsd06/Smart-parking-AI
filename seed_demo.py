"""Run once from the project root:  python seed_demo.py
Creates 30 slots, an admin, demo users + vehicles, 30 days of booking history (for the
analytics page) and a set of upcoming bookings allocated by Hill Climbing."""
import io, random, contextlib
from datetime import datetime, timedelta
from database.db import initialize_database, get_connection
from services.extra import ensure_tables
from backend.users import register_user
from backend.vehicles import add_vehicle
from backend.parking_slots import add_slot
from integration import allocate_new_booking

rng = random.Random(42)
quiet = lambda: contextlib.redirect_stdout(io.StringIO())      # hide A's print() output

with quiet():
    initialize_database()
ensure_tables()
con = get_connection()

# 1. Slots: zones A, B, C x 10 (1-2 accessible, 3-5 EV, 6-10 regular)
if con.execute("SELECT COUNT(*) FROM parking_slots").fetchone()[0] == 0:
    for z in "ABC":
        for n in range(1, 11):
            t = "accessible" if n <= 2 else "EV" if n <= 5 else "regular"
            gate = "North Gate" if z == "A" else "South Gate" if z == "B" else ("North Gate" if n % 2 else "South Gate")
            add_slot(f"{z}{n:02d}", t, gate)

# 2. Users and vehicles
register_user("Admin", "admin@smartpark.com", "Admin@12345")
for i in range(1, 9):
    register_user(f"Demo User {i}", f"demo{i}@example.com", "demo12345")
    uid = con.execute("SELECT user_id FROM users WHERE email = ?", (f"demo{i}@example.com",)).fetchone()[0]
    for k in range(2):
        add_vehicle(uid, f"DL{i}C{k}{rng.randint(1000, 9999)}", rng.choices(["regular", "EV", "accessible"], [70, 20, 10])[0])

users = [r[0] for r in con.execute("SELECT user_id FROM users WHERE email LIKE 'demo%'")]
vehicles = con.execute("SELECT vehicle_id, user_id, vehicle_type FROM vehicles").fetchall()
slots = con.execute("SELECT slot_id, slot_type, gate FROM parking_slots").fetchall()
fits = {"accessible": ("accessible",), "EV": ("EV", "regular"), "regular": ("regular", "EV")}

# 3. History: ~300 past bookings, peaks at 9-11 and 17-19, busier on weekdays
if con.execute("SELECT COUNT(*) FROM bookings WHERE status = 'completed'").fetchone()[0] == 0:
    hour_w = [1, 1, 1, 1, 1, 2, 4, 8, 12, 16, 14, 10, 9, 9, 8, 8, 10, 15, 14, 8, 4, 2, 1, 1]
    busy, made, tries = {}, 0, 0
    while made < 300 and tries < 3000:
        tries += 1
        day = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(days=rng.randint(1, 30))
        if day.weekday() >= 5 and rng.random() < 0.5:
            continue
        start = day.replace(hour=rng.choices(range(24), hour_w)[0])
        hours = rng.choice([1, 1, 2, 2, 3, 4])
        end = start + timedelta(hours=hours)
        vid, uid, vt = rng.choice(vehicles)
        for sid, st_, gate in rng.sample(slots, len(slots)):
            if st_ in fits[vt] and all(end <= a or start >= b for a, b in busy.get(sid, [])):
                busy.setdefault(sid, []).append((start, end))
                status = "cancelled" if rng.random() < 0.1 else "completed"
                con.execute("""INSERT INTO bookings (user_id, vehicle_id, slot_id, arrival_time, duration,
                               destination_gate, requires_charging, status, created_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (uid, vid, sid, start.isoformat(), hours, gate,
                             int(vt == "EV" and rng.random() < 0.4), status,
                             (start - timedelta(hours=rng.randint(1, 48))).isoformat(sep=" ")))
                made += 1
                break
    con.commit()
con.close()

# 4. Upcoming bookings through the real Hill Climbing pipeline
con = get_connection()
vehicles = con.execute("SELECT vehicle_id, user_id, vehicle_type FROM vehicles").fetchall()
con.close()
rng.shuffle(vehicles)
base = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
ok_count = 0
for vid, uid, vt in vehicles[:14]:
    with quiet():
        ok, _ = allocate_new_booking(uid, vid, (base + timedelta(hours=rng.randint(0, 5))).isoformat(),
                                     rng.choice([1, 2, 3]), rng.choice(["North Gate", "South Gate"]),
                                     vt == "EV" and rng.random() < 0.5)
    ok_count += ok
print(f"Seeded. Upcoming bookings allocated: {ok_count}")
print("Admin login : admin@smartpark.com / Admin@12345")
print("Demo login  : demo1@example.com / demo12345")
