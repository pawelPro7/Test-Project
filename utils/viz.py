"""
Komponenty wizualne: boisko, mapy cieplne stref, mapy zdarzen (jesli events.csv ma
wspolrzedne x/y), mapy strzalow oraz wykresy radarowe do porownan zawodnikow.

Konwencja wspolrzednych boiska (znormalizowane, niezalezne od jednostek w zrodle):
  x: 0 (linia wlasnej bramki) -> 100 (linia bramki rywala)
  y: 0 (jedna linia boczna)  -> 100 (druga linia boczna)
Jesli events.csv ma inny zakres (np. 0-105 / 0-68 w metrach), dane sa przeskalowywane
do 0-100 przed rysowaniem - patrz normalize_xy().
"""
import numpy as np
import plotly.graph_objects as go

from utils.styling import COLORS, apply_plotly_theme, FONT_MONO

PITCH_LEN_M, PITCH_WID_M = 105.0, 68.0


def _m2x(m):
    return m * 100 / PITCH_LEN_M


def _m2y(m):
    return m * 100 / PITCH_WID_M


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha:.3f})"


def normalize_xy(series, observed_max):
    """Skaluje wspolrzedne do zakresu 0-100, jesli zrodlo uzywa np. metrow (0-105/0-68)."""
    if observed_max is None or observed_max <= 0:
        return series
    if observed_max <= 101:
        return series
    return series / observed_max * 100


def _pitch_base_shapes():
    shapes = []
    line = COLORS["line"]

    def rect(x0, y0, x1, y1, layer="above", width=1.6, fill=None):
        d = dict(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=line, width=width), layer=layer)
        if fill:
            d["fillcolor"] = fill
        return d

    def circle(x0, y0, x1, y1, layer="above", width=1.6):
        return dict(type="circle", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=line, width=width), layer=layer)

    # murawa (subtelne pasy koszenia)
    n_stripes = 10
    for i in range(n_stripes):
        x0, x1 = i * 100 / n_stripes, (i + 1) * 100 / n_stripes
        fill = "#122016" if i % 2 == 0 else "#132419"
        shapes.append(rect(x0, 0, x1, 100, layer="below", width=0, fill=fill))

    # obrys boiska
    shapes.append(rect(0, 0, 100, 100, width=2))
    # linia polowy
    shapes.append(dict(type="line", x0=50, y0=0, x1=50, y1=100, line=dict(color=line, width=2), layer="above"))
    # kolo srodkowe + punkt
    r_x, r_y = _m2x(9.15), _m2y(9.15)
    shapes.append(circle(50 - r_x, 50 - r_y, 50 + r_x, 50 + r_y))

    # pola karne / bramkowe (lewe i prawe)
    pen_depth, pen_half = _m2x(16.5), _m2y(20.16)
    six_depth, six_half = _m2x(5.5), _m2y(9.16)
    shapes.append(rect(0, 50 - pen_half, pen_depth, 50 + pen_half))
    shapes.append(rect(0, 50 - six_half, six_depth, 50 + six_half))
    shapes.append(rect(100 - pen_depth, 50 - pen_half, 100, 50 + pen_half))
    shapes.append(rect(100 - six_depth, 50 - six_half, 100, 50 + six_half))
    return shapes


def empty_pitch_figure(height=460, title=None):
    fig = go.Figure()
    fig.update_layout(shapes=_pitch_base_shapes())
    fig.update_xaxes(range=[-2, 102], visible=False, fixedrange=True)
    fig.update_yaxes(range=[-2, 102], visible=False, fixedrange=True,
                      scaleanchor="x", scaleratio=PITCH_WID_M / PITCH_LEN_M)
    apply_plotly_theme(fig, height=height, show_legend=False)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    if title:
        fig.update_layout(title=title)
    return fig


ZONE_X_BINS = [(0, 6), (6, 33), (33, 66), (66, 94), (94, 100)]
LANE_Y_BINS = [(0, 20), (20, 37), (37, 63), (63, 80), (80, 100)]


def zone_heatmap_figure(grid: np.ndarray, zone_labels, lane_labels, title=None, height=460,
                         color=COLORS["accent"]):
    """grid ma ksztalt (5 korytarzy, 5 stref) - patrz data_loader.zone_grid_from_marginals."""
    fig = empty_pitch_figure(height=height, title=title)
    vmax = grid.max() if grid.size and grid.max() > 0 else 1
    hover_x, hover_y, hover_text = [], [], []
    for i, (y0, y1) in enumerate(LANE_Y_BINS):
        for j, (x0, x1) in enumerate(ZONE_X_BINS):
            val = grid[i, j]
            alpha = 0.08 + 0.72 * (val / vmax) if vmax > 0 else 0.08
            fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                           fillcolor=hex_to_rgba(color, alpha), line=dict(width=0), layer="below")
            hover_x.append((x0 + x1) / 2)
            hover_y.append((y0 + y1) / 2)
            hover_text.append(f"{zone_labels[j]} / {lane_labels[i]}<br>Dotkniecia: <b>{val:.1f}</b>")
    fig.add_trace(go.Scatter(
        x=hover_x, y=hover_y, mode="markers",
        marker=dict(size=46, color="rgba(0,0,0,0)"),
        hovertext=hover_text, hoverinfo="text", showlegend=False,
    ))
    return fig


def grid_from_events(x, y, nx=24, ny=16):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) == 0:
        return np.zeros((ny, nx)), np.linspace(0, 100, nx), np.linspace(0, 100, ny)
    hist, xedges, yedges = np.histogram2d(x, y, bins=[nx, ny], range=[[0, 100], [0, 100]])
    xcenters = (xedges[:-1] + xedges[1:]) / 2
    ycenters = (yedges[:-1] + yedges[1:]) / 2
    return hist.T, xcenters, ycenters


def event_heatmap_figure(x, y, title=None, height=460, color=COLORS["accent"]):
    fig = empty_pitch_figure(height=height, title=title)
    grid, xc, yc = grid_from_events(x, y)
    if grid.max() > 0:
        fig.add_trace(go.Heatmap(
            x=xc, y=yc, z=grid, zsmooth="best", showscale=False,
            colorscale=[[0, "rgba(0,0,0,0)"], [1, color]],
            opacity=0.82, hovertemplate="Liczba zdarzen w okolicy: %{z}<extra></extra>",
        ))
    # przerysuj linie boiska NAD heatmapa
    for shp in _pitch_base_shapes():
        if shp.get("layer") == "above":
            fig.add_shape(**shp)
    return fig


def shot_map_figure(x, y, xg, is_goal, height=460, title=None):
    fig = empty_pitch_figure(height=height, title=title)
    x, y, xg, is_goal = map(np.asarray, (x, y, xg, is_goal))
    xg_safe = np.nan_to_num(xg, nan=0.05)
    sizes = 10 + 40 * np.clip(xg_safe, 0, 1)
    colors = [COLORS["accent"] if g else COLORS["text_muted"] for g in is_goal]
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="markers",
        marker=dict(size=sizes, color=colors, line=dict(color=COLORS["bg"], width=1.2), opacity=0.9),
        customdata=np.stack([xg_safe, is_goal], axis=-1),
        hovertemplate="xG: %{customdata[0]:.2f}<br>Gol: %{customdata[1]}<extra></extra>",
        showlegend=False,
    ))
    return fig


def radar_chart_figure(categories, series: dict, title=None, height=460):
    """series: {nazwa_serii: [wartosci_0_100, ...]} - te same kategorie dla kazdej serii."""
    fig = go.Figure()
    palette = [COLORS["accent"], COLORS["accent_3"], COLORS["accent_2"], COLORS["accent_4"]]
    for i, (name, values) in enumerate(series.items()):
        vals = list(values) + [values[0]]
        cats = list(categories) + [categories[0]]
        col = palette[i % len(palette)]
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=cats, name=name, fill="toself",
            line=dict(color=col, width=2), fillcolor=hex_to_rgba(col, 0.18),
        ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=COLORS["grid"],
                             color=COLORS["text_muted"], showticklabels=True, tickfont=dict(size=9)),
            angularaxis=dict(gridcolor=COLORS["grid"], color=COLORS["text"], tickfont=dict(size=11)),
        ),
    )
    apply_plotly_theme(fig, height=height, show_legend=len(series) > 1)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    if title:
        fig.update_layout(title=title)
    return fig


def percentile_scale(df, cols, player_row):
    """Zwraca liste wartosci 0-100 (percentyl w obrebie df) dla kazdej kolumny w cols."""
    out = []
    for c in cols:
        if c not in df.columns or df[c].dropna().empty:
            out.append(0)
            continue
        val = player_row.get(c, np.nan)
        if pos_check := (isinstance(val, float) and np.isnan(val)):
            out.append(0)
            continue
        pct = (df[c] <= val).mean() * 100
        out.append(round(float(pct), 1))
    return out
