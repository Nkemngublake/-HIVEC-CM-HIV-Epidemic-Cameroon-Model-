import os
import sys
import threading
from queue import Queue, Empty
from typing import List, Dict, Any

import dash
from dash import html, dcc, Output, Input, State
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from hivec_cm.models.parameters import load_parameters
from hivec_cm.models.model import EnhancedHIVModel


# Global state for a single run (simple MVP)
RUN_QUEUE: Queue | None = None
RUN_UPDATES: List[Dict[str, Any]] = []
RUN_THREAD: threading.Thread | None = None
RUN_MODEL: EnhancedHIVModel | None = None
RUNNING: bool = False


def start_run(population: int, years: int, dt: float, start_year: int, seed: int | None,
              mixing_method: str, use_numba: bool):
    global RUN_QUEUE, RUN_UPDATES, RUN_THREAD, RUN_MODEL, RUNNING
    params = load_parameters(os.path.join(os.path.dirname(__file__), '../config/parameters.json'))
    params.initial_population = population
    RUN_QUEUE = Queue()
    RUN_UPDATES = []

    def on_year_result(row: dict):
        if RUN_QUEUE is not None:
            RUN_QUEUE.put(row)

    RUN_MODEL = EnhancedHIVModel(
        params,
        start_year=start_year,
        seed=seed,
        mixing_method=mixing_method,
        use_numba=use_numba,
        on_year_result=on_year_result,
    )

    def target():
        global RUNNING
        try:
            RUN_MODEL.run_simulation(years=years, dt=dt)
        finally:
            RUNNING = False

    RUN_THREAD = threading.Thread(target=target, daemon=True)
    RUNNING = True
    RUN_THREAD.start()


def stop_run():
    global RUN_MODEL
    if RUN_MODEL is not None:
        RUN_MODEL.request_stop()


app = dash.Dash(__name__)
app.title = 'HIVEC-CM Live (Dash)'

app.layout = html.Div([
    html.H2('HIVEC-CM: Live Simulation (Dash)'),

    html.Div([
        html.Label('Population'),
        dcc.Input(id='population', type='number', value=25000, min=1000, step=1000),
        html.Label('Years'),
        dcc.Input(id='years', type='number', value=30, min=1, step=1),
        html.Label('dt'),
        dcc.Dropdown(id='dt', options=[0.1, 0.2, 0.5, 1.0], value=0.1, clearable=False),
        html.Label('Start Year'),
        dcc.Input(id='start-year', type='number', value=1990, min=1960, step=1),
        html.Label('Seed'),
        dcc.Input(id='seed', type='number', value=42, min=0, step=1),
        html.Label('Mixing'),
        dcc.Dropdown(id='mixing', options=['binned', 'scan'], value='binned', clearable=False),
        dcc.Checklist(id='use-numba', options=[{'label': 'Use Numba', 'value': 'yes'}], value=[]),
        html.Button('Start', id='btn-start', n_clicks=0, style={'marginRight': '10px'}),
        html.Button('Pause', id='btn-pause', n_clicks=0, style={'marginRight': '10px'}),
        html.Button('Resume', id='btn-resume', n_clicks=0, style={'marginRight': '10px'}),
        html.Button('Stop', id='btn-stop', n_clicks=0),
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(8, minmax(130px, 1fr))', 'gap': '10px'}),

    dcc.Store(id='run-data', data=[]),
    dcc.Interval(id='tick', interval=300, n_intervals=0),
    html.Div(id='status'),
    dcc.Graph(id='fig-prev'),
    dcc.Graph(id='fig-art'),
    dcc.Graph(id='fig-inf'),
    dcc.Graph(id='fig-pop'),
])


@app.callback(
    Output('run-data', 'data'),
    Output('status', 'children'),
    Input('tick', 'n_intervals'),
    State('run-data', 'data')
)
def poll_updates(_n, data):
    global RUN_QUEUE, RUNNING, RUN_UPDATES
    # Drain queue
    if RUN_QUEUE is not None:
        while True:
            try:
                item = RUN_QUEUE.get_nowait()
                RUN_UPDATES.append(item)
            except Empty:
                break
    status = 'Running…' if RUNNING else ('Idle' if not RUN_UPDATES else 'Completed/Stopped')
    return RUN_UPDATES, status


@app.callback(
    Output('fig-prev', 'figure'),
    Output('fig-art', 'figure'),
    Output('fig-inf', 'figure'),
    Output('fig-pop', 'figure'),
    Input('run-data', 'data')
)
def redraw_figures(rows):
    years = [r['year'] for r in rows] if rows else []
    prev = [r['hiv_prevalence'] * 100 for r in rows] if rows else []
    art = [((r['art_coverage'] or 0) * 100) for r in rows] if rows else []
    inf = [r['new_infections'] for r in rows] if rows else []
    pop = [r['total_population'] for r in rows] if rows else []

    fig1 = go.Figure([go.Scatter(x=years, y=prev, mode='lines')])
    fig1.update_layout(title='HIV Prevalence (%)', xaxis_title='Year', yaxis_title='%')
    fig2 = go.Figure([go.Scatter(x=years, y=art, mode='lines')])
    fig2.update_layout(title='ART Coverage (%)', xaxis_title='Year', yaxis_title='%')
    fig3 = go.Figure([go.Scatter(x=years, y=inf, mode='lines')])
    fig3.update_layout(title='New Infections', xaxis_title='Year', yaxis_title='#')
    fig4 = go.Figure([go.Scatter(x=years, y=pop, mode='lines')])
    fig4.update_layout(title='Total Population', xaxis_title='Year', yaxis_title='#')
    return fig1, fig2, fig3, fig4


@app.callback(
    Output('btn-start', 'n_clicks'),
    Input('btn-start', 'n_clicks'),
    State('population', 'value'), State('years', 'value'), State('dt', 'value'),
    State('start-year', 'value'), State('seed', 'value'), State('mixing', 'value'),
    State('use-numba', 'value')
)
def on_start(n, population, years, dt, start_year, seed, mixing, use_numba):
    if n and n > 0:
        start_run(int(population), int(years), float(dt), int(start_year), int(seed), str(mixing), ('yes' in (use_numba or [])))
        return 0
    return dash.no_update


@app.callback(
    Output('btn-stop', 'n_clicks'),
    Input('btn-stop', 'n_clicks')
)
def on_stop(n):
    if n and n > 0:
        stop_run()
        return 0
    return dash.no_update


if __name__ == '__main__':
    app.run(debug=True)
@app.callback(
    Output('btn-pause', 'n_clicks'),
    Input('btn-pause', 'n_clicks')
)
def on_pause(n):
    global RUN_MODEL
    if n and n > 0 and RUN_MODEL is not None:
        RUN_MODEL.request_pause()
        return 0
    return dash.no_update


@app.callback(
    Output('btn-resume', 'n_clicks'),
    Input('btn-resume', 'n_clicks')
)
def on_resume(n):
    global RUN_MODEL
    if n and n > 0 and RUN_MODEL is not None:
        RUN_MODEL.resume()
        return 0
    return dash.no_update

