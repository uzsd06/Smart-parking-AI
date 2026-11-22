import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import streamlit as st
import ui
from backend.bookings import update_booking_status
from integration import cancel_booking_and_reallocate
from services.extra import run_and_notify, user_bookings, unread_notifications, mark_all_read

user = ui.require_login()
ui.page_header("My Bookings", "Track, check in, cancel, and see any changes to your slot.", "📋")


@ui.live(5)
def notifications():
    notes = unread_notifications(user["user_id"])
    if notes:
        for _, msg, when in notes:
            st.info(f"{msg}  ({when})")
        if st.button("Mark all as read"):
            mark_all_read(user["user_id"])
            st.rerun()


notifications()

df = user_bookings(user["user_id"])
if df.empty:
    st.write("You have no bookings yet. Go to **Book Parking**.")
    st.stop()

show = df[["booking_id", "vehicle", "slot_number", "arrival_time", "duration",
           "destination_gate", "requires_charging", "status"]].rename(columns={
    "booking_id": "ID", "vehicle": "Vehicle", "slot_number": "Slot", "arrival_time": "Arrival",
    "duration": "Hours", "destination_gate": "Gate", "requires_charging": "Charging", "status": "Status"})
st.dataframe(show, use_container_width=True, hide_index=True)

st.subheader("Manage a booking")
active = df[df.status.isin(["pending", "allocated", "checked-in"])]
if active.empty:
    st.caption("No active bookings to manage.")
else:
    bid = int(st.selectbox("Booking", active.booking_id.tolist()))
    status = active[active.booking_id == bid].iloc[0].status
    a, b, c = st.columns(3)
    if a.button("Cancel booking", disabled=status == "checked-in"):
        (ok, msg), _ = run_and_notify(cancel_booking_and_reallocate, bid, user["user_id"])
        (st.success if ok else st.error)(msg)
        st.rerun()
    if b.button("Check in", disabled=status != "allocated"):
        ok, msg = update_booking_status(bid, "checked-in")
        (st.success if ok else st.error)(msg)
        st.rerun()
    if c.button("Complete (leave)", disabled=status != "checked-in"):
        ok, msg = update_booking_status(bid, "completed")
        (st.success if ok else st.error)(msg)
        st.rerun()
