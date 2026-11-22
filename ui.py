"""Shared UI helpers (Member C): styling, page setup, login guard, lot map, live refresh."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import io
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, FancyBboxPatch
from database.db import initialize_database
from services.extra import ensure_tables

ADMIN_EMAILS = {"admin@smartpark.com"}      # who sees the admin pages
GATES = ["North Gate", "South Gate"]        # gates A's integration code accepts
TYPE_COLOR = {"regular": "#9ECAE1", "EV": "#74C476", "accessible": "#FD8D3C"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
.stApp, .stMarkdown { font-family: 'Inter', 'Segoe UI', sans-serif; }
h1, h2, h3 { font-family: 'Poppins', 'Segoe UI', sans-serif !important; letter-spacing: -0.01em; }
footer { visibility: hidden; }
.block-container { padding-top: 1.8rem; max-width: 1180px; }
[data-testid="stSidebar"] { background: #EEF4F7; border-right: 1px solid #DCE5EB; }
[data-testid="stSidebarNav"] a, a[data-testid="stSidebarNavLink"] { border-radius: 12px !important; margin: 2px 4px; transition: background .15s ease; }
[data-testid="stSidebarNav"] a:hover, a[data-testid="stSidebarNavLink"]:hover { background: #DCEBF2 !important; }
[data-testid="stSidebarNav"] a[aria-current="page"], a[data-testid="stSidebarNavLink"][aria-current="page"] { background: #CFE6EE !important; font-weight: 700 !important; }
.sp-side-note { color:#52606D; font-size:.88rem; padding:.2rem .4rem .8rem; line-height:1.45; }
.sp-side-foot { color:#6C7A89; font-size:.78rem; text-align:center; margin-top:1.2rem; line-height:1.5; }
.sp-hero { background: linear-gradient(135deg,#0B3C5D 0%,#1C7293 62%,#2BB3A3 100%); color:#fff; border-radius:24px; padding:2.7rem 2.5rem; box-shadow:0 16px 36px rgba(11,60,93,.25); position:relative; overflow:hidden; min-height:430px; }
.sp-hero:after { content:""; position:absolute; right:-70px; top:-70px; width:280px; height:280px; border-radius:50%; background:rgba(255,255,255,.08); }
.sp-hero:before { content:""; position:absolute; right:60px; bottom:-90px; width:200px; height:200px; border-radius:50%; background:rgba(255,255,255,.06); }
.sp-badge { display:inline-block; background:rgba(255,255,255,.18); padding:.35rem .9rem; border-radius:999px; font-size:.82rem; font-weight:600; margin-bottom:1.1rem; }
.sp-hero-title { font-family:'Poppins',sans-serif; font-size:3rem; font-weight:700; line-height:1.1; margin:0 0 .9rem 0; }
.sp-hero p { font-size:1.08rem; opacity:.93; max-width:33rem; line-height:1.55; margin:0; }
.sp-chips { display:flex; gap:.8rem; flex-wrap:wrap; margin-top:1.8rem; position:relative; z-index:1; }
.sp-chip { background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.28); border-radius:16px; padding:.75rem 1.15rem; min-width:105px; }
.sp-chip b { display:block; font-family:'Poppins',sans-serif; font-size:1.7rem; }
.sp-chip span { font-size:.78rem; opacity:.88; }
.sp-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:1rem; }
.sp-card { background:#fff; border:1px solid #E3EAF0; border-radius:18px; padding:1.35rem 1.25rem; box-shadow:0 4px 14px rgba(27,42,65,.06); transition:transform .15s ease, box-shadow .15s ease; }
.sp-card:hover { transform:translateY(-4px); box-shadow:0 14px 28px rgba(27,42,65,.13); }
.sp-ico { font-size:2rem; margin-bottom:.45rem; }
.sp-card h4 { margin:.1rem 0 .4rem 0; font-family:'Poppins',sans-serif; font-size:1.05rem; color:#0B3C5D; }
.sp-card p { margin:0; color:#52606D; font-size:.92rem; line-height:1.5; }
.sp-h2 { font-family:'Poppins',sans-serif; font-size:1.75rem; font-weight:700; color:#0B3C5D; margin:2.6rem 0 .25rem 0; }
.sp-sub { color:#52606D; margin:0 0 1.1rem 0; }
.sp-num { width:2.5rem; height:2.5rem; border-radius:50%; background:linear-gradient(135deg,#1C7293,#2BB3A3); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; margin-bottom:.7rem; }
.sp-tech { display:flex; gap:.6rem; flex-wrap:wrap; margin-top:.4rem; }
.sp-tech span { background:#E9F1F5; color:#0B3C5D; border-radius:999px; padding:.35rem .9rem; font-size:.85rem; font-weight:600; }
.sp-footer { margin-top:3rem; padding:1.5rem 1rem; text-align:center; color:#6C7A89; font-size:.88rem; border-top:1px solid #DCE5EB; }
.sp-banner { background:linear-gradient(120deg,#0B3C5D,#1C7293 70%,#2BB3A3); color:#fff; border-radius:20px; padding:1.5rem 1.9rem; margin-bottom:1.3rem; box-shadow:0 10px 24px rgba(11,60,93,.18); }
.sp-banner-title { font-family:'Poppins',sans-serif; font-size:1.9rem; font-weight:700; margin:0; }
.sp-banner-sub { opacity:.92; margin:.25rem 0 0 0; }
.sp-user { display:flex; align-items:center; gap:.7rem; background:#fff; border:1px solid #E3EAF0; border-radius:14px; padding:.7rem .8rem; margin-bottom:.6rem; }
.sp-avatar { width:2.4rem; height:2.4rem; border-radius:50%; background:linear-gradient(135deg,#1C7293,#2BB3A3); color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center; }
.sp-user small { color:#6C7A89; }
[data-testid="stMetric"] { background:#fff; border:1px solid #E3EAF0; border-radius:16px; padding:1rem 1.1rem; box-shadow:0 4px 14px rgba(27,42,65,.06); }
[data-testid="stForm"] { background:#fff; border:1px solid #E3EAF0; border-radius:20px; padding:1.4rem 1.4rem 1.1rem; box-shadow:0 10px 26px rgba(27,42,65,.09); }
.stButton > button, .stFormSubmitButton > button { border-radius:12px; font-weight:600; padding:.55rem 1.3rem; transition:all .15s ease; }
.stButton > button:hover, .stFormSubmitButton > button:hover { transform:translateY(-1px); box-shadow:0 8px 16px rgba(28,114,147,.25); }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"], .stFormSubmitButton > button[kind="primary"], button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] { background:linear-gradient(135deg,#1C7293,#2BB3A3); color:#fff; border:none; }
[data-testid="stPageLink"] a, a[data-testid="stPageLink-NavLink"] { display:flex; justify-content:center; text-align:center; width:100%; background:#fff; border:1px solid #E3EAF0; border-radius:14px; padding:1rem 1rem; box-shadow:0 4px 14px rgba(27,42,65,.06); font-weight:600; transition:all .15s ease; }
[data-testid="stPageLink"] a:hover, a[data-testid="stPageLink-NavLink"]:hover { border-color:#1C7293; transform:translateY(-2px); }
.stTabs [data-baseweb="tab"] { font-weight:600; }
</style>
"""


def _html(s):
    st.markdown(s, unsafe_allow_html=True)


# ---------- HTML building blocks ----------
def hero_html(free, total, zones):
    return ('<div class="sp-hero"><span class="sp-badge">AI-powered parking allocation</span>'
            '<div class="sp-hero-title">Park smarter,<br>not harder.</div>'
            '<p>SmartPark AI uses Hill Climbing search to give every booking the best possible slot: '
            'shorter walks, less congestion, and the right spot for EV and accessible vehicles.</p>'
            '<div class="sp-chips">'
            f'<div class="sp-chip"><b>{free}</b><span>free right now</span></div>'
            f'<div class="sp-chip"><b>{total}</b><span>total slots</span></div>'
            f'<div class="sp-chip"><b>{zones}</b><span>zones</span></div>'
            '</div></div>')


def _cards(items, numbered=False):
    out = '<div class="sp-grid">'
    for i, (icon, title, text) in enumerate(items, 1):
        top = f'<div class="sp-num">{i}</div>' if numbered else f'<div class="sp-ico">{icon}</div>'
        out += f'<div class="sp-card">{top}<h4>{title}</h4><p>{text}</p></div>'
    return out + '</div>'


def features_html():
    return _cards([
        ("🧠", "AI-optimised allocation", "Hill Climbing searches many vehicle-to-slot combinations to cut walking distance and wasted slots."),
        ("⚡", "EV and accessible priority", "Charging and accessible slots go to the vehicles that need them, and ordinary cars are kept out."),
        ("🔄", "Smart re-allocation", "When a booking is cancelled, waiting and upcoming bookings are re-optimised automatically."),
        ("📊", "Live insights", "A real-time lot map, peak-hour analytics and utilisation charts for administrators."),
    ])


def steps_html():
    return _cards([
        ("", "Register and add your vehicle", "Create an account and save your vehicle type: regular, EV or accessible."),
        ("", "Choose time and gate", "Tell us when you arrive, how long you stay and which gate you are heading to. The AI picks the slot."),
        ("", "Park, and we keep planning", "Check in on arrival. If anything changes, other bookings are re-optimised and owners are notified."),
    ], numbered=True)


def tech_html():
    return ('<div class="sp-tech">' + "".join(f"<span>{t}</span>" for t in
            ["Python", "Hill Climbing", "Streamlit", "SQLite", "Pandas", "Matplotlib"]) + '</div>')


def footer_html():
    return ('<div class="sp-footer">SmartPark AI &nbsp;|&nbsp; IGDTUW &nbsp;|&nbsp; AI Lab and Theory Project<br>'
            'Congestion-aware parking allocation using Hill Climbing</div>')


def section(title, sub=""):
    _html(f'<div class="sp-h2">{title}</div><div class="sp-sub">{sub}</div>')


def page_header(title, subtitle="", icon=""):
    _html(f'<div class="sp-banner"><div class="sp-banner-title">{icon} {title}</div>'
          f'<div class="sp-banner-sub">{subtitle}</div></div>')


def nav_card(page, label, icon):
    """A clickable card that opens `page` (a st.Page object)."""
    if page is None:
        return
    try:
        st.page_link(page, label=label, icon=icon)
    except Exception:
        st.write(f"{icon} {label}")


def card():
    try:
        return st.container(border=True)
    except TypeError:
        return st.container()


# ---------- app plumbing ----------
@st.cache_resource
def _init_once():
    initialize_database()
    ensure_tables()
    return True


def setup():
    """Call once, from Home.py: page config, styling and the sidebar logo."""
    try:
        st.set_page_config(page_title="SmartPark AI", page_icon="🅿️", layout="wide")
    except Exception:
        pass
    _init_once()
    _html(CSS)
    logo = pathlib.Path(__file__).resolve().parent / "assets" / "logo.svg"
    if logo.exists() and hasattr(st, "logo"):
        try:
            st.logo(str(logo), size="large", icon_image=str(logo))
        except TypeError:
            st.logo(str(logo))


def sidebar_user():
    """Sidebar account card + log out button (call after st.navigation)."""
    user = st.session_state.get("user")
    with st.sidebar:
        if not user:
            _html('<div class="sp-side-note">Log in to book parking, manage your bookings and get notified '
                  'when your slot changes.</div>')
        else:
            role = "Administrator" if is_admin(user) else "Driver"
            _html('<div class="sp-user"><div class="sp-avatar">' + user["name"][:1].upper() + '</div><div>'
                  f'<b>{user["name"]}</b><br><small>{role}</small></div></div>')
            if st.button("Log out", use_container_width=True):
                st.session_state.pop("user", None)
                st.rerun()
        _html('<div class="sp-side-foot">SmartPark AI<br>AI Lab and Theory Project</div>')


def is_admin(user):
    return bool(user) and user["email"] in ADMIN_EMAILS


def require_login():
    user = st.session_state.get("user")
    if not user:
        st.warning("Please log in from the Home page first.")
        st.stop()
    return user


def require_admin():
    user = require_login()
    if not is_admin(user):
        st.error("This page is for administrators only.")
        st.stop()
    return user


def live(seconds=5):
    """Auto-refresh a section (needs Streamlit 1.37+; otherwise it just renders once)."""
    def deco(fn):
        return st.fragment(run_every=seconds)(fn) if hasattr(st, "fragment") else fn
    return deco


# ---------- parking map ----------
def draw_lot(df, highlight=()):
    """Draw the lot from a lot_at() DataFrame. `highlight` = slot numbers to ring in gold."""
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    zones = sorted({s[0] for s in df.slot_number})
    for zi, z in enumerate(zones):
        ax.add_patch(FancyBboxPatch((zi * 3.2 - 0.55, -0.6), 2.1, 5.2, boxstyle="round,pad=0.02,rounding_size=0.25",
                                    fc="#E9F1F5", ec="none", zorder=0))
        ax.text(zi * 3.2 + 0.5, 4.85, f"Zone {z}", ha="center", va="bottom", fontweight="bold", color="#0B3C5D", fontsize=11)
    for r in df.itertuples():
        try:
            zi, n = zones.index(r.slot_number[0]), int(r.slot_number[1:])
        except ValueError:
            continue
        x, y = zi * 3.2 + ((n - 1) % 2), 4 - (n - 1) // 2
        if r.status == "available":
            col = TYPE_COLOR.get(r.slot_type, "#CCCCCC")
        elif r.status == "occupied":
            col = "#4A5560"
        else:
            col = "#D62728"
        gold = r.slot_number in highlight
        ax.add_patch(FancyBboxPatch((x - 0.4, y - 0.36), 0.8, 0.72, boxstyle="round,pad=0.02,rounding_size=0.14",
                                    fc=col, ec="#F2B705" if gold else "white", lw=3.2 if gold else 1.2, zorder=2))
        ax.text(x, y, r.slot_number, ha="center", va="center", fontsize=8, fontweight="bold", zorder=3,
                color="white" if col in ("#4A5560", "#D62728") else "#1B2A41")
    mid = (len(zones) * 3.2 - 1.2) / 2
    ax.text(mid, 5.7, "▲  NORTH GATE", ha="center", color="#1C7293", fontweight="bold", fontsize=10)
    ax.text(mid, -1.25, "▼  SOUTH GATE", ha="center", color="#1C7293", fontweight="bold", fontsize=10)
    ax.set_xlim(-0.8, len(zones) * 3.2 - 0.6)
    ax.set_ylim(-1.7, 6.1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(handles=[Patch(color=c, label=("EV" if t == "EV" else t.capitalize())) for t, c in TYPE_COLOR.items()] +
              [Patch(color="#4A5560", label="Occupied"), Patch(color="#D62728", label="Blocked / maintenance")],
              ncol=5, loc="upper center", bbox_to_anchor=(0.5, 0.02), fontsize=8, frameon=False)
    return fig


def show(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", transparent=True)
    plt.close(fig)
    st.image(buf)
