import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from datetime import datetime, date, timedelta
import streamlit as st
import ui
from backend.vehicles import add_vehicle, get_user_vehicles
from integration import allocate_new_booking
from services.extra import run_and_notify, user_bookings, lot_at

user = ui.require_login()
ui.page_header("Book Parking", "Pick your vehicle, time and gate. Hill Climbing chooses the best slot for you.", "🚗")

vehicles = get_user_vehicles(user["user_id"])          # [(vehicle_id, reg, type), ...]
with st.expander("Add a vehicle", expanded=not vehicles):
    with st.form("add_vehicle"):
        reg = st.text_input("Registration number")
        vtype = st.selectbox("Vehicle type", ["regular", "EV", "accessible"])
        if st.form_submit_button("Save vehicle"):
            ok, msg = add_vehicle(user["user_id"], reg, vtype)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
if not vehicles:
    st.stop()

options = {f"{reg} ({vt})": (vid, vt) for vid, reg, vt in vehicles}
label = st.selectbox("Vehicle", list(options))
vehicle_id, vehicle_type = options[label]

c1, c2, c3 = st.columns(3)
day = c1.date_input("Date", min_value=date.today())
start = c2.time_input("Arrival time", value=(datetime.now() + timedelta(hours=1)).time().replace(minute=0, second=0, microsecond=0))
hours = c3.number_input("Duration (whole hours)", min_value=1, max_value=12, value=2, step=1)
gate = st.selectbox("Destination gate", ui.GATES)
charging = st.checkbox("I need EV charging") if vehicle_type == "EV" else False

if st.button("Book with AI allocation", type="primary"):
    arrival = datetime.combine(day, start).replace(second=0, microsecond=0)
    if arrival < datetime.now() - timedelta(minutes=5):
        st.error("Arrival time is in the past.")
    else:
        (ok, msg), notes = run_and_notify(allocate_new_booking, user["user_id"], vehicle_id,
                                          arrival.isoformat(), int(hours), gate, bool(charging))
        if ok:
            st.success(msg)
            if notes:
                st.info(f"{len(notes)} other booking(s) were re-optimised and their owners notified.")
            mine = user_bookings(user["user_id"])
            if not mine.empty and mine.iloc[0].slot_number:
                st.write(f"Your slot **{mine.iloc[0].slot_number}** at {arrival:%d %b %H:%M}:")
                ui.show(ui.draw_lot(lot_at(arrival), highlight={mine.iloc[0].slot_number}))
        else:
            st.error(msg)
