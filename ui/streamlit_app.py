import os
import threading
import time
from queue import Queue, Empty

import plotly.graph_objects as go
import streamlit as st

from hivec_cm.models.parameters import load_parameters
from hivec_cm.models.model import EnhancedHIVModel


st.set_page_config(page_title="HIVEC-CM Live Simulation", layout="wide")
st.title("HIVEC-CM: Live Simulation (Local)")


def start_simulation(population: int, years: int, dt: float, start_year: int,
                     seed: int | None, mixing_method: str, use_numba: bool):
    params = load_parameters(os.path.join(os.path.dirname(__file__), "../config/parameters.json"))
    params.initial_population = population

    st.session_state.queue = Queue()
    updates = st.session_state.updates = []  # list of rows

    def on_year_result(row: dict):
        st.session_state.queue.put(row)

    model = EnhancedHIVModel(
        params,
        start_year=start_year,
        seed=seed,
        mixing_method=mixing_method,
        use_numba=use_numba,
        on_year_result=on_year_result,
    )
    st.session_state.model = model

    def runner():
        try:
            model.run_simulation(years=years, dt=dt)
        finally:
            st.session_state.running = False

    st.session_state.thread = threading.Thread(target=runner, daemon=True)
    st.session_state.running = True
    st.session_state.thread.start()


def stop_simulation():
    model = st.session_state.get("model")
    if model is not None:
        model.request_stop()


with st.sidebar:
    st.header("Controls")
    population = st.number_input("Population", min_value=1000, max_value=500_000, value=25_000, step=1000)
    years = st.number_input("Years", min_value=1, max_value=200, value=30, step=1)
    dt = st.select_slider("dt (years)", options=[0.1, 0.2, 0.5, 1.0], value=0.1)
    start_year = st.number_input("Start year", min_value=1960, max_value=2100, value=1990)
    seed = st.number_input("Seed (optional)", min_value=0, max_value=10**6, value=42)
    mixing_method = st.selectbox("Mixing method", ["binned", "scan"], index=0)
    use_numba = st.checkbox("Use Numba acceleration (if available)", value=False)

    cols = st.columns(4)
    if cols[0].button("Start", type="primary"):
        start_simulation(int(population), int(years), float(dt), int(start_year), int(seed), mixing_method, bool(use_numba))
    if cols[1].button("Pause"):
        if st.session_state.get("model"):
            st.session_state.model.request_pause()
            st.session_state.paused = True
    if cols[2].button("Resume"):
        if st.session_state.get("model"):
            st.session_state.model.resume()
            st.session_state.paused = False
    if cols[3].button("Stop"):
        stop_simulation()


ph1 = st.empty()
ph2 = st.empty()
ph3 = st.empty()
ph4 = st.empty()
status_ph = st.empty()


def render_charts(rows: list[dict]):
    if not rows:
        return
    years = [r['year'] for r in rows]

    # Prevalence (%)
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=years, y=[r['hiv_prevalence'] * 100 for r in rows], mode='lines', name='Prevalence %'))
    fig1.update_layout(title="HIV Prevalence (%)", xaxis_title="Year", yaxis_title="%")
    ph1.plotly_chart(fig1, use_container_width=True)

    # ART coverage (%)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=years, y=[(r['art_coverage'] or 0) * 100 for r in rows], mode='lines', name='ART %'))
    fig2.update_layout(title="ART Coverage (%)", xaxis_title="Year", yaxis_title="%")
    ph2.plotly_chart(fig2, use_container_width=True)

    # New infections
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=years, y=[r['new_infections'] for r in rows], mode='lines', name='New infections'))
    fig3.update_layout(title="New Infections", xaxis_title="Year", yaxis_title="#")
    ph3.plotly_chart(fig3, use_container_width=True)

    # Total population
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=years, y=[r['total_population'] for r in rows], mode='lines', name='Population'))
    fig4.update_layout(title="Total Population", xaxis_title="Year", yaxis_title="#")
    ph4.plotly_chart(fig4, use_container_width=True)


# Live update loop
if st.session_state.get("running"):
    status_ph.info("Simulation running… (pause/resume supported)")
    t_last = time.time()
    while st.session_state.get("running"):
        try:
            item = st.session_state.queue.get(timeout=0.2)
            st.session_state.updates.append(item)
        except Empty:
            pass
        # Redraw at most ~5 fps
        if time.time() - t_last > 0.2:
            render_charts(st.session_state.updates)
            t_last = time.time()
        # Yield to UI
        time.sleep(0.05)
    status_ph.success("Simulation finished or stopped.")
    render_charts(st.session_state.updates)
else:
    if st.session_state.get("updates"):
        status = "Paused" if st.session_state.get("paused") else "Idle"
        status_ph.info(f"Last run displayed below. Status: {status}")
        render_charts(st.session_state.updates)
