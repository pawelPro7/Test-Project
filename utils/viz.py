"""
Visual components: pitch, zone heatmaps, and radar charts for player comparisons.

Pitch coordinate convention (normalized, independent of the source units):
  x: 0 (own goal line) -> 100 (opponent goal line)
  y: 0 (one touchline)  -> 100 (other touchline)
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

    # turf (subtle mowing stripes)
    n_stripes = 10
    for i in range(n_stripes):
        x0, x1 = i * 100 / n_stripes, (i + 1) * 100 / n_stripes
        fill = "#122016" if i % 2 == 0 else "#132419"
        shapes.append(rect(x0, 0, x1, 100, layer="below", width=0, fill=fill))

    # pitch outline
    shapes.append(rect(0, 0, 100, 100, width=2))
    # halfway line
    shapes.append(dict(type="line", x0=50, y0=0, x1=50, y1=100, line=dict(color=line, width=2), layer="above"))
    # center circle + spot
    r_x, r_y = _m2x(9.15), _m2y(9.15)
    shapes.append(circle(50 - r_x, 50 - r_y, 50 + r_x, 50 + r_y))

    # penalty / goal areas (left and right)
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
    """grid has shape (5 lanes, 5 zones) - see data_loader.zone_grid_from_marginals."""
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
            hover_text.append(f"{zone_labels[j]} / {lane_labels[i]}<br>Touches: <b>{val:.1f}</b>")
    fig.add_trace(go.Scatter(
        x=hover_x, y=hover_y, mode="markers",
        marker=dict(size=46, color="rgba(0,0,0,0)"),
        hovertext=hover_text, hoverinfo="text", showlegend=False,
    ))
    return fig


def radar_chart_figure(categories, series: dict, title=None, height=460, hover_texts: dict = None):
    """series: {series_name: [values_0_100, ...]} - the same categories for each series.
    hover_texts (optional): {series_name: [hover_string, ...]} matching categories 1:1 - when
    given for a series, that trace gets a custom per-vertex hover tooltip instead of the default
    "categoryname = value" hover. The visible vertex markers stay small; a second, invisible
    trace with much larger markers carries the actual hover target, so hovering is easy without
    making the visible dots big (same pattern as the transparent hover markers in
    zone_heatmap_figure).
    """
    fig = go.Figure()
    palette = [COLORS["accent"], COLORS["accent_3"], COLORS["accent_2"], COLORS["accent_4"]]
    for i, (name, values) in enumerate(series.items()):
        vals = list(values) + [values[0]]
        cats = list(categories) + [categories[0]]
        col = palette[i % len(palette)]
        trace_kwargs = dict(
            r=vals, theta=cats, name=name, fill="toself",
            line=dict(color=col, width=2), fillcolor=hex_to_rgba(col, 0.18),
        )
        if hover_texts and name in hover_texts:
            texts = list(hover_texts[name])
            texts = texts + [texts[0]]
            trace_kwargs.update(mode="lines+markers", marker=dict(size=6, color=col))
            fig.add_trace(go.Scatterpolar(**trace_kwargs))
            fig.add_trace(go.Scatterpolar(
                r=vals, theta=cats, mode="markers",
                marker=dict(size=30, color="rgba(0,0,0,0)"),
                hovertext=texts, hoverinfo="text", showlegend=False,
            ))
        else:
            fig.add_trace(go.Scatterpolar(**trace_kwargs))
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
    """Returns a list of 0-100 values (percentile within df) for each column in cols."""
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


def _reverse_if_needed(stat, higher_is_better):
    """For a 'lower is better' metric, flips percentile/zscore so a favorable raw value always
    reads as a high percentile / positive z-score, without touching the raw value itself."""
    if higher_is_better or stat["percentile"] is None:
        return stat
    stat = dict(stat)
    stat["percentile"] = round(100 - stat["percentile"], 1)
    if stat["zscore"] is not None:
        stat["zscore"] = round(-stat["zscore"], 2)
    return stat


def metric_stats(df, cols, player_row, higher_is_better=True):
    """Per column: {raw, percentile, zscore} against df's distribution for that column.

    percentile uses the exact same (series <= val).mean()*100 definition as percentile_scale,
    so radar r-values built from this function's percentiles match percentile_scale exactly.
    zscore is computed against the same comparison population/column as the percentile, using
    that column's own mean/std within df. Any of the three is None when it can't be computed
    (column missing, no data, player's value missing, or zero variance for zscore).
    Pass higher_is_better=False for a metric where a lower raw value is the better outcome (e.g.
    goals conceded) - percentile/zscore are flipped so "better" always reads as higher/positive.
    """
    out = []
    for c in cols:
        if c not in df.columns or df[c].dropna().empty:
            out.append({"raw": None, "percentile": None, "zscore": None})
            continue
        val = player_row.get(c, np.nan)
        if isinstance(val, float) and np.isnan(val):
            out.append({"raw": None, "percentile": None, "zscore": None})
            continue
        series = df[c].dropna()
        pct = round(float((series <= val).mean() * 100), 1)
        std = series.std()
        zscore = round(float((val - series.mean()) / std), 2) if std and std > 0 else None
        out.append(_reverse_if_needed({"raw": float(val), "percentile": pct, "zscore": zscore}, higher_is_better))
    return out


def value_stats(population, player_value, higher_is_better=True):
    """{raw, percentile, zscore} of player_value within an arbitrary pre-built population Series -
    e.g. one per-90 rate per player, rather than one raw value per row. Same percentile/zscore
    definitions as metric_stats, just against a caller-supplied distribution instead of a df column.
    Pass higher_is_better=False for a metric where a lower raw value is the better outcome.
    """
    if (population is None or population.empty or player_value is None
            or (isinstance(player_value, float) and np.isnan(player_value))):
        return {"raw": None, "percentile": None, "zscore": None}
    pct = round(float((population <= player_value).mean() * 100), 1)
    std = population.std()
    zscore = round(float((player_value - population.mean()) / std), 2) if std and std > 0 else None
    return _reverse_if_needed({"raw": float(player_value), "percentile": pct, "zscore": zscore}, higher_is_better)


def player_per90(rows_df, col, minutes_col="PLAYDURATION"):
    """A single player's own per-90 rate over rows_df (their selected match, or all their
    matches): sum(col) / (sum(minutes)/60) * 90 - a ratio of totals, not an average of
    per-match rates, so it's not skewed by short-minute appearances."""
    total_minutes = rows_df[minutes_col].sum()
    if total_minutes <= 0:
        return None
    return float(rows_df[col].sum()) / (total_minutes / 60) * 90


def population_per90(df, col, minutes_col="PLAYDURATION", min_total_minutes=0):
    """One row per player (grouped by 'playerName'): sum(col)/sum(minutes)*90 across their
    full history in df. minutes_col is assumed to be in SECONDS (this app's PLAYDURATION
    convention); min_total_minutes is in MINUTES and excludes players whose total minutes in
    df fall below that floor, so a handful of substitute-appearance minutes can't produce an
    extreme, misleading per-90 outlier in the comparison population."""
    sums = df.groupby("playerName")[col].sum()
    total_minutes = df.groupby("playerName")[minutes_col].sum() / 60
    valid = total_minutes >= max(min_total_minutes, 1e-9)
    return sums[valid] / total_minutes[valid] * 90


def ordinal(n):
    n = int(round(n))
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def fmt_zscore(z):
    if z is None:
        return "N/A"
    sign = "+" if z >= 0 else "−"
    return f"{sign}{abs(z):.2f}"


def radar_hover_text(stat, value_fmt, player_name=None):
    """Builds the standard 'Player value / Percentile / Z-score' hover string for one radar
    axis. Pass player_name to prefix it with the player's name (for multi-player radars where
    the tooltip needs to identify whose point it is)."""
    raw_str = value_fmt(stat["raw"]) if stat["raw"] is not None else "N/A"
    pct_str = f"{ordinal(stat['percentile'])} percentile" if stat["percentile"] is not None else "N/A"
    z_str = fmt_zscore(stat["zscore"]) if stat["percentile"] is not None else "N/A"
    prefix = f"{player_name}<br>" if player_name else ""
    return f"{prefix}Player value: {raw_str}<br>Percentile: {pct_str}<br>Z-score: {z_str}"
