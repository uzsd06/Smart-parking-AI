import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from datetime import datetime, date, time
import streamlit as st
import ui
from backend.parking_slots import update_slot_status, get_all_slots
from integration import reallocate_waiting_bookings
from services.extra import run_and_notify, lot_at, all_bookings, ai_vs_baselines

ui.require_admin()
ui.page_header("Admin Dashboard", "Live lot, bookings, optimiser and slot management.", "🛠️")
t_live, t_book, t_opt, t_slots = st.tabs(["Live lot", "Bookings", "Optimiser", "Slots"])

with t_live:
    pick = st.checkbox("View a specific time instead of now")
    when = datetime.combine(st.date_input("Date", value=date.today()), st.time_input("Time", value=time(12, 0))) if pick else None


    @ui.live(5)
    def panel(when):
        lot = lot_at(when or datetime.now())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Available", int((lot.status == "available").sum()))
        c2.metric("Occupied", int((lot.status == "occupied").sum()))
        c3.metric("Blocked / maintenance", int(lot.status.isin(["blocked", "maintenance"]).sum()))
        bk = all_bookings()
        c4.metric("Waiting list", int((bk.status == "pending").sum()))
        ui.show(ui.draw_lot(lot))


    panel(when)

with t_book:
    bk = all_bookings()
    ALL_STATUSES = ["pending", "allocated", "checked-in", "completed", "cancelled"]
    sel = st.multiselect("Status filter", ALL_STATUSES, default=["pending", "allocated", "checked-in"])
    cols = ["booking_id", "user_name", "vehicle", "vehicle_type", "slot_number", "arrival_time", "duration",
            "destination_gate", "requires_charging", "status"]
    st.dataframe(bk[bk.status.isin(sel)][cols], use_container_width=True, hide_index=True)

with t_opt:
    st.write("Re-run Hill Climbing over all pending and allocated bookings. Checked-in cars never move.")
    if st.button("Re-optimise now", type="primary"):
        (ok, msg), notes = run_and_notify(reallocate_waiting_bookings)
        (st.success if ok else st.error)(msg + f" {len(notes)} user(s) notified.")
    st.subheader("Hill Climbing vs baselines (current active bookings)")
    res = ai_vs_baselines()
    if res is None:
        st.caption("No active bookings to compare yet.")
    else:
        st.dataframe(res, use_container_width=True, hide_index=True)
        st.caption("Fitness score is Member A's function: higher is better.")

with t_slots:
    slots = get_all_slots()                    # (slot_id, number, type, gate, status)
    st.dataframe([{"Slot": s[1], "Type": s[2], "Gate": s[3], "Status": s[4]} for s in slots],
                 use_container_width=True, hide_index=True)
    names = {s[1]: s[0] for s in slots}
    c1, c2 = st.columns(2)
    chosen = c1.selectbox("Slot", list(names))
    new = c2.selectbox("New status", ["available", "blocked", "maintenance"])
    if st.button("Update slot"):
        ok, msg = update_slot_status(names[chosen], new)
        (st.success if ok else st.error)(msg)
        if ok:
            st.rerun()
    st.caption("After blocking a slot, press 'Re-optimise now' so affected bookings move to other slots.")
