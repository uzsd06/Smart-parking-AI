"""SmartPark AI - entry point, navigation and Home page.   Run:  streamlit run Home.py"""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from datetime import datetime
import streamlit as st
import ui
from backend.users import register_user, login_user
from services.extra import lot_at, user_bookings, unread_notifications

ui.setup()
if not hasattr(st, "navigation"):
    st.error("This app needs a newer Streamlit. Run:  pip install -U streamlit")
    st.stop()


def find_page(keyword):
    """Path of the newest file in pages/ whose name contains `keyword`.
    Works even if a download renamed it to something like '1_Book_Parking (1).py'."""
    matches = [p for p in (ROOT / "pages").glob("*.py") if keyword.lower() in p.stem.lower()]
    return f"pages/{max(matches, key=lambda p: p.stat().st_mtime).name}" if matches else None


PG = {}


def home_view():
    user = st.session_state.get("user")
    if not user:
        landing()
    else:
        dashboard(user)


def landing():
    lot = lot_at(datetime.now())
    free, total = int((lot.status == "available").sum()), len(lot)
    zones = lot.slot_number.str[0].nunique() if total else 0
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.markdown(ui.hero_html(free, total, zones), unsafe_allow_html=True)
    with right:
        tab_in, tab_up = st.tabs(["Log in", "Create account"])
        with tab_in:
            with st.form("login"):
                st.markdown("### Welcome back")
                email = st.text_input("Email", placeholder="you@example.com")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("Log in", type="primary", use_container_width=True):
                    found = login_user(email, pw)
                    if found:
                        st.session_state["user"] = found
                        st.rerun()
                    else:
                        st.error("Wrong email or password.")
        with tab_up:
            with st.form("register"):
                st.markdown("### Join SmartPark")
                name = st.text_input("Full name")
                email2 = st.text_input("Email address", placeholder="you@example.com")
                phone = st.text_input("Phone (optional)")
                pw2 = st.text_input("Password (min 8 characters)", type="password")
                if st.form_submit_button("Create account", type="primary", use_container_width=True):
                    ok, msg = register_user(name, email2, pw2, phone or None)
                    (st.success if ok else st.error)(msg + (" You can log in now." if ok else ""))

    ui.section("Why SmartPark AI", "Parking that thinks about the whole lot, not just one car.")
    st.markdown(ui.features_html(), unsafe_allow_html=True)
    ui.section("How it works", "Three steps from booking to parking.")
    st.markdown(ui.steps_html(), unsafe_allow_html=True)
    ui.section("Live availability", "A look at the lot right now. It refreshes automatically.")

    @ui.live(5)
    def preview():
        with ui.card():
            ui.show(ui.draw_lot(lot_at(datetime.now())))

    preview()
    ui.section("Built with")
    st.markdown(ui.tech_html(), unsafe_allow_html=True)
    st.markdown(ui.footer_html(), unsafe_allow_html=True)


def dashboard(user):
    first = user["name"].split()[0]
    ui.page_header(f"Welcome back, {first} 👋", "Here is what is happening in the lot right now.", "")

    cards = [("book", "Book Parking", "🚗"), ("bookings", "My Bookings", "📋")]
    if ui.is_admin(user):
        cards += [("admin", "Admin Dashboard", "🛠️"), ("analytics", "Analytics", "📊")]
    cols = st.columns(len(cards))
    for col, (key, label, icon) in zip(cols, cards):
        with col:
            ui.nav_card(PG.get(key), label, icon)
    st.write("")

    @ui.live(5)
    def overview():
        lot = lot_at(datetime.now())
        mine = user_bookings(user["user_id"])
        upcoming = 0
        if not mine.empty:
            upcoming = int((mine.status.isin(["pending", "allocated"]) & (mine.end > datetime.now())).sum())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Free slots now", int((lot.status == "available").sum()))
        c2.metric("Occupied", int((lot.status == "occupied").sum()))
        c3.metric("My upcoming bookings", upcoming)
        c4.metric("Unread notifications", len(unread_notifications(user["user_id"])))
        st.write("")
        with ui.card():
            ui.show(ui.draw_lot(lot))

    overview()
    st.markdown(ui.footer_html(), unsafe_allow_html=True)


# ---------- navigation (sidebar titles and icons are set here, not by file names) ----------
PG["home"] = st.Page(home_view, title="Home", icon="🏠", default=True)
for key, keyword, title, icon, url in [
        ("book", "Book_Parking", "Book Parking", "🚗", "book-parking"),
        ("bookings", "My_Bookings", "My Bookings", "📋", "my-bookings"),
        ("admin", "Admin_Dashboard", "Admin Dashboard", "🛠️", "admin"),
        ("analytics", "Analytics", "Analytics", "📊", "analytics")]:
    path = find_page(keyword)
    if path:
        PG[key] = st.Page(path, title=title, icon=icon, url_path=url)

user = st.session_state.get("user")
menu = {"Menu": [PG["home"]]}
if user:
    menu["Menu"] += [PG[k] for k in ("book", "bookings") if k in PG]
if ui.is_admin(user):
    menu["Administration"] = [PG[k] for k in ("admin", "analytics") if k in PG]

nav = st.navigation(menu)
ui.sidebar_user()
nav.run()
