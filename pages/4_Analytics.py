import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import ui
from services.extra import all_bookings, ai_vs_baselines

ui.require_admin()
ui.page_header("Analytics", "Peak hours, demand patterns, utilisation and AI-vs-baseline results.", "📊")

df = all_bookings()
if df.empty:
    st.info("No bookings yet. Run seed_demo.py to create demo history.")
    st.stop()

used = df[df.status.isin(["allocated", "checked-in", "completed"]) & df.slot_number.notna()]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total bookings", len(df))
c2.metric("Cancellation rate", f"{100 * (df.status == 'cancelled').mean():.1f}%")
c3.metric("Avg duration (h)", f"{df.duration.mean():.1f}")
c4.metric("EV share", f"{100 * (df.vehicle_type == 'EV').mean():.1f}%")

left, right = st.columns(2)
hours = df.arrival.dt.hour.value_counts().reindex(range(24), fill_value=0)
fig, ax = plt.subplots()
ax.bar(hours.index, hours.values, color="#1C7293")
ax.set_xlabel("Hour of day"); ax.set_ylabel("Bookings"); ax.set_title("Arrivals by hour (peak hours)")
with left:
    ui.show(fig)
    top = hours.nlargest(3).index.tolist()
    st.caption("Peak hours: " + ", ".join(f"{h}:00" for h in sorted(top)))

heat = pd.crosstab(df.arrival.dt.dayofweek, df.arrival.dt.hour).reindex(index=range(7), columns=range(24), fill_value=0)
fig, ax = plt.subplots()
im = ax.imshow(heat.values, aspect="auto", cmap="Blues")
ax.set_yticks(range(7)); ax.set_yticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
ax.set_xlabel("Hour of day"); ax.set_title("Demand heatmap (weekday x hour)"); fig.colorbar(im)
with right:
    ui.show(fig)

left, right = st.columns(2)
zone = used.groupby(used.slot_number.str[0]).duration.sum()
fig, ax = plt.subplots()
ax.bar(zone.index, zone.values, color=["#1C7293", "#D1603D", "#C98A0B"][:len(zone)])
ax.set_xlabel("Zone"); ax.set_ylabel("Booked hours"); ax.set_title("Utilisation by zone")
with left:
    ui.show(fig)
status = df.status.value_counts()
fig, ax = plt.subplots()
ax.bar(status.index, status.values, color="#6C7A89")
ax.set_title("Bookings by status"); ax.set_ylabel("Count")
with right:
    ui.show(fig)

st.subheader("Hill Climbing vs baselines (active bookings)")
res = ai_vs_baselines()
if res is None:
    st.caption("No active bookings right now.")
else:
    st.dataframe(res, use_container_width=True, hide_index=True)
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(res["Method"], res["Fitness score"], color=["#6C7A89", "#C98A0B", "#1C7293"])
    ax.set_ylabel("Fitness (higher is better)")
    ui.show(fig)

st.download_button("Download all bookings (CSV)", df.drop(columns=["arrival", "end"]).to_csv(index=False),
                   file_name="smartpark_bookings.csv", mime="text/csv")
