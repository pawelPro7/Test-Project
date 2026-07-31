"""
Tozsamosc wizualna aplikacji: "stadion noca / kartka meczowa".

Paleta:
  tlo (murawa po zmroku)       #0C1712
  tlo karty                    #142219
  tlo karty (hover/elevated)   #1B3024
  linia (kreda boiska)         #E9E4D6
  tekst przygaszony            #93A796
  akcent glowny (tablica wynikow) #F2B705
  akcent drugi (czerwona kartka)  #E2543D
  akcent trzeci (reflektory)      #4FA3D1

Typografia:
  naglowki -> Oswald (skondensowany, "stadionowy")
  tekst    -> Work Sans
  liczby / staty -> IBM Plex Mono (efekt "tabeli meczowej")
"""
import streamlit as st

COLORS = {
    "bg": "#0C1712",
    "bg_card": "#142219",
    "bg_card_hover": "#1B3024",
    "bg_sidebar": "#0A140F",
    "line": "#E9E4D6",
    "text": "#ECE9DF",
    "text_muted": "#93A796",
    "accent": "#F2B705",       # zloty / tablica wynikow
    "accent_2": "#E2543D",     # koralowo-czerwony
    "accent_3": "#4FA3D1",     # reflektory
    "accent_4": "#6FCF97",     # trawiasta ziel (pozytywne wartosci)
    "grid": "#24382C",
    "border": "#243528",
}

CHART_SEQUENCE = [COLORS["accent"], COLORS["accent_3"], COLORS["accent_2"],
                   COLORS["accent_4"], "#B48EAD", "#E0A96D"]

FONT_DISPLAY = "'Oswald', sans-serif"
FONT_BODY = "'Work Sans', sans-serif"
FONT_MONO = "'IBM Plex Mono', monospace"


def inject_global_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Work+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: {FONT_BODY};
    }}

    .stApp {{
        background:
            radial-gradient(circle at 15% 0%, #14261A 0%, transparent 45%),
            radial-gradient(circle at 100% 20%, #12241a 0%, transparent 40%),
            {COLORS["bg"]};
        color: {COLORS["text"]};
    }}

    h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        font-family: {FONT_DISPLAY};
        letter-spacing: 0.02em;
        color: {COLORS["text"]};
        font-weight: 600;
    }}

    [data-testid="stSidebar"] {{
        background: {COLORS["bg_sidebar"]};
        border-right: 1px solid {COLORS["border"]};
    }}
    [data-testid="stSidebar"] * {{
        color: {COLORS["text"]} !important;
    }}
    [data-testid="stSidebarNav"] a span {{
        font-family: {FONT_DISPLAY};
        letter-spacing: 0.03em;
        font-size: 0.95rem;
    }}

    [data-testid="stMetric"] {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-left: 3px solid {COLORS["accent"]};
        border-radius: 8px;
        padding: 14px 16px 10px 16px;
    }}
    [data-testid="stMetricValue"] {{
        font-family: {FONT_MONO};
        color: {COLORS["accent"]};
    }}
    [data-testid="stMetricLabel"] {{
        color: {COLORS["text_muted"]};
        font-family: {FONT_BODY};
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.06em;
    }}

    .stButton>button, .stDownloadButton>button {{
        font-family: {FONT_DISPLAY};
        letter-spacing: 0.03em;
        background: {COLORS["bg_card"]};
        color: {COLORS["text"]};
        border: 1px solid {COLORS["accent"]};
        border-radius: 6px;
        transition: all 0.15s ease;
    }}
    .stButton>button:hover, .stDownloadButton>button:hover {{
        background: {COLORS["accent"]};
        color: {COLORS["bg"]};
        border-color: {COLORS["accent"]};
    }}

    div[data-baseweb="select"] > div, .stTextInput input, .stMultiSelect > div > div {{
        background-color: {COLORS["bg_card"]} !important;
        border-color: {COLORS["border"]} !important;
        border-radius: 6px !important;
        color: {COLORS["text"]} !important;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        overflow: hidden;
    }}

    hr {{
        border-color: {COLORS["border"]};
    }}

    /* ---- wlasne komponenty ---- */
    .pitch-eyebrow {{
        font-family: {FONT_DISPLAY};
        color: {COLORS["accent"]};
        text-transform: uppercase;
        letter-spacing: 0.18em;
        font-size: 0.78rem;
        margin-bottom: 2px;
    }}
    .pitch-title {{
        font-family: {FONT_DISPLAY};
        font-size: 2.1rem;
        font-weight: 600;
        color: {COLORS["text"]};
        margin: 0 0 2px 0;
        line-height: 1.15;
    }}
    .pitch-subtitle {{
        color: {COLORS["text_muted"]};
        font-size: 0.98rem;
        max-width: 720px;
    }}
    .kpi-card {{
        background: linear-gradient(160deg, {COLORS["bg_card"]} 0%, {COLORS["bg_card_hover"]} 130%);
        border: 1px solid {COLORS["border"]};
        border-radius: 10px;
        padding: 16px 18px;
        height: 100%;
    }}
    .kpi-card .kpi-label {{
        text-transform: uppercase;
        letter-spacing: 0.07em;
        font-size: 0.7rem;
        color: {COLORS["text_muted"]};
        margin-bottom: 6px;
    }}
    .kpi-card .kpi-value {{
        font-family: {FONT_MONO};
        font-size: 1.9rem;
        color: {COLORS["accent"]};
        font-weight: 600;
        line-height: 1;
    }}
    .kpi-card .kpi-sub {{
        color: {COLORS["text_muted"]};
        font-size: 0.78rem;
        margin-top: 6px;
    }}
    .player-card {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 20px 22px;
    }}
    .player-card .name {{
        font-family: {FONT_DISPLAY};
        font-size: 1.6rem;
        color: {COLORS["text"]};
    }}
    .player-card .meta {{
        color: {COLORS["text_muted"]};
        font-size: 0.85rem;
        font-family: {FONT_MONO};
    }}
    .tag {{
        display: inline-block;
        font-family: {FONT_MONO};
        font-size: 0.72rem;
        color: {COLORS["accent"]};
        border: 1px solid {COLORS["accent"]};
        border-radius: 20px;
        padding: 2px 10px;
        margin-right: 6px;
    }}
    .section-divider {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 8px 0 14px 0;
    }}
    .section-divider .line {{
        flex: 1;
        height: 1px;
        background: repeating-linear-gradient(90deg, {COLORS["border"]} 0 6px, transparent 6px 10px);
    }}
    .section-divider .label {{
        font-family: {FONT_DISPLAY};
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.85rem;
        color: {COLORS["text_muted"]};
        white-space: nowrap;
    }}
    .data-pill {{
        font-family: {FONT_MONO};
        font-size: 0.72rem;
        padding: 3px 10px;
        border-radius: 20px;
        border: 1px solid {COLORS["border"]};
        color: {COLORS["text_muted"]};
        display: inline-block;
        margin: 2px 6px 2px 0;
    }}
    .data-pill.ok {{ color: {COLORS["accent_4"]}; border-color: {COLORS["accent_4"]}; }}
    .data-pill.warn {{ color: {COLORS["accent_2"]}; border-color: {COLORS["accent_2"]}; }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)


def pitch_watermark_svg(height=180, opacity=0.16):
    """Cienka kreda boiska jako dekoracyjne tlo naglowka - motyw przewodni aplikacji."""
    c = COLORS["line"]
    return f"""
    <div style="position:relative; height:{height}px; margin-bottom:-{height}px; opacity:{opacity}; pointer-events:none;">
      <svg viewBox="0 0 1000 {height}" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:{height}px;">
        <line x1="500" y1="0" x2="500" y2="{height}" stroke="{c}" stroke-width="2"/>
        <circle cx="500" cy="{height/2}" r="70" fill="none" stroke="{c}" stroke-width="2"/>
        <circle cx="500" cy="{height/2}" r="3" fill="{c}"/>
        <rect x="0" y="{height*0.18}" width="90" height="{height*0.64}" fill="none" stroke="{c}" stroke-width="2"/>
        <rect x="910" y="{height*0.18}" width="90" height="{height*0.64}" fill="none" stroke="{c}" stroke-width="2"/>
      </svg>
    </div>
    """


def page_header(eyebrow: str, title: str, subtitle: str = ""):
    st.markdown(pitch_watermark_svg(140, 0.14), unsafe_allow_html=True)
    st.markdown(f"""
    <div>
      <div class="pitch-eyebrow">{eyebrow}</div>
      <div class="pitch-title">{title}</div>
      <div class="pitch-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")


def section_divider(label: str):
    st.markdown(f"""
    <div class="section-divider">
        <div class="label">{label}</div>
        <div class="line"></div>
    </div>
    """, unsafe_allow_html=True)


def kpi_card(label: str, value: str, sub: str = ""):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """


def apply_plotly_theme(fig, height=420, show_legend=True):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_BODY, color=COLORS["text"], size=13),
        title_font=dict(family=FONT_DISPLAY, color=COLORS["text"], size=18),
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=show_legend,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["text_muted"])),
        colorway=CHART_SEQUENCE,
        hoverlabel=dict(bgcolor=COLORS["bg_card_hover"], font=dict(family=FONT_BODY, color=COLORS["text"])),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"], color=COLORS["text_muted"])
    fig.update_yaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"], color=COLORS["text_muted"])
    return fig
