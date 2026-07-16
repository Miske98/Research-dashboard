import json
import uuid

import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

import dashboard_logic as dl

# ---------------------------------------------------------------------------
# Page config & styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Interactive Research Dashboard",
    layout="wide",
)

FONT_IMPORTS = """
    @import url('https://fonts.cdnfonts.com/css/bookman-old-style');
    @import url('https://fonts.cdnfonts.com/css/cascadia-code');
"""

# ČISTA BELA POZADINA + PASTELNO ZELENI DETALJI
st.markdown(
    f"""
    <style>
    {FONT_IMPORTS}

    /* Čista bela pozadina za celu aplikaciju */
    .stApp {{
        background-color: #FFFFFF;
    }}

    /* Fontovi */
    html, body, [class*="css"] {{
        font-family: 'Bookman Old Style', Georgia, 'Times New Roman', serif;
        color: #2D2A26;
    }}
    h1, h2, h3, h4, h5, h6, p, label, span, div[data-testid="stMarkdownContainer"] {{
        font-family: 'Bookman Old Style', Georgia, 'Times New Roman', serif;
        color: #2D2A26;
    }}
    
    /* Brojevi i tehnički detalji u Cascadia Code */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"],
    .stDataFrame, .stTable, code, pre,
    div[data-baseweb="slider"] div, div[data-baseweb="input"] input,
    div[data-testid="stNumberInput"] input {{
        font-family: 'Cascadia Code', 'Consolas', monospace !important;
    }}

    /* STILIZACIJA SELECTBOX-EVA (Sada imaju uočljivu pastelno-zelenu ivicu po defaultu) */
    div[data-baseweb="select"] {{
        background-color: #FFFFFF !important;
        border: 2px solid #8CA182 !important; /* Pastelna žalfija-zelena */
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.2s ease-in-out;
    }}
    
    /* Kada se pređe mišem ili klikne na selectbox (intenzivnija pastelna nijansa) */
    div[data-baseweb="select"]:hover, div[data-baseweb="select"]:focus-within {{
        border-color: #5B6F53 !important; /* Tamnija pastelno zelena */
        box-shadow: 0 2px 8px rgba(140, 161, 130, 0.3) !important;
    }}

    /* Stilizacija padajućeg menija unutar selectbox-a */
    div[role="listbox"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #8CA182 !important;
    }}

    /* Multiselect tagovi (male loptice za izabrane opcije u selectbox-u) */
    span[data-baseweb="tag"] {{
        background-color: #EBF1E9 !important; /* Nežna pastelno zelena */
        color: #4A5D4E !important;
        border-radius: 4px !important;
        font-weight: 500;
    }}

    /* STILIZACIJA KLIZAČA (SLIDER-A) - da sve prati pastelno zeleni ton */
    /* Aktivni deo trake slidera */
    div[data-testid="stSlider"] div[role="slider"] {{
        background-color: #8CA182 !important;
        border: 2px solid #8CA182 !important;
    }}
    div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div {{
        background: #8CA182 !important;
    }}
    /* Brojevi iznad klizača */
    div[data-testid="stSlider"] div {{
        color: #4A5D4E !important;
    }}

    /* Okviri oko grafikona - čisto bela pozadina, ali sa finom zelenkastom ivicom da ih nežno odvoji */
    div[data-testid="element-container"] > div.stPlotlyChart {{
        background-color: #FFFFFF !important;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
        border: 1px solid #EBF1E9 !important; /* Ekstremno blaga pastelna ivica */
    }}

    /* Sporedne beleške */
    .small-note {{ 
        color: #7D7871; 
        font-size: 0.85rem; 
    }}
    </style>
    """,
    unsafe_allow_html=True,
)
# ---------------------------------------------------------------------------
# Pastelne Plotly Boje (Mekane, akademske, nikako agresivne)
# ---------------------------------------------------------------------------
PLOTLY_FONT = dict(family="Cascadia Code, Consolas, monospace", size=13, color="#2D2A26")
PLOTLY_TITLE_FONT = dict(family="Bookman Old Style, Georgia, serif", size=16, color="#2D2A26")

# Kolekcija prelepih pastelnih tonova (žalfija, prigušena plava, breskva, lavanda, pesak...)
SPAGHETTI_PALETTE = [
    "#A8C3BC", # Nežna žalfija
    "#ADC3D1", # Prigušena čelično plava
    "#CFB9A5", # Topli kapućino
    "#D3B5C1", # Prigušena pastelna roze
    "#C4CCD3", # Svetlo siva / magla
    "#B9C0A5", # Maslinasto zelena
    "#E2C2B9", # Nežna terakota / breskva
    "#CBB5D3", # Nežna lavanda
    "#E8D5B7", # Boja peska
    "#A5B8C0"  # Svetla plavo-siva
]


# ---------------------------------------------------------------------------
# Data loading & Configuration
# ---------------------------------------------------------------------------

LOCAL_FILE_DEFAULT = "C:/Users/Administrator/Desktop/Gigs/Jelena Simic/Arc_normalized.xlsx"


GSHEET_URL_DEFAULT = "https://docs.google.com/spreadsheets/d/1NGbN5Cm274KToPHbb9v74XQp0QbBeFgRGpa9Xs6OnA4/edit?usp=sharing"


@st.cache_data(show_spinner="Loading data...")
def load_local_excel(file) -> pd.DataFrame:
    return pd.read_excel(file)


@st.cache_data(show_spinner="Loading data from Google Sheets...")
def load_google_sheet(sheet_url: str, worksheet_name: str = None) -> pd.DataFrame:
    import gspread
    from google.oauth2.service_account import Credentials
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    
    if "gcp_service_account" not in st.secrets:
        st.error(
            "GCP Service Account secrets are missing! "
            "Please add your service account JSON configuration to your Streamlit Secrets."
        )
        st.stop()
        
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    ws = sheet.worksheet(worksheet_name) if worksheet_name else sheet.sheet1
    records = ws.get_all_records()
    return pd.DataFrame(records)


def get_data() -> pd.DataFrame:
        try:
            return load_google_sheet(GSHEET_URL_DEFAULT)
        except Exception as e:
            st.error(f"Failed to connect to Google Sheets: {e}")
            st.info("Make sure you shared your Google Sheet with the client email found inside your service account JSON file.")
            st.stop()


baza = get_data()
baza = baza[~baza["Code"].isin([12, 14, 24, 26, 27])]

# Basic sanity check / friendly column-name trimming
baza.columns = [str(c).strip() for c in baza.columns]

TOTAL_N = baza["Code"].nunique() if "Code" in baza.columns else len(baza)

# ---------------------------------------------------------------------------
# Sidebar — universal patient filters
# ---------------------------------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.header("Patient filters")


# Earlier BoNT-A treatment in legs (Yes / No, both selectable at once)
if "Earlier BoNT-A treatment in legs" in baza.columns:
    earlier_options = sorted([s for s in baza["Earlier BoNT-A treatment in legs"].dropna().unique()])
    earlier_sel = st.sidebar.multiselect(
        "Earlier BoNT-A treatment in legs", earlier_options, default=earlier_options
    )
else:
    earlier_sel = None

# Age when stroke — double-ended slider
if "Age when stroke" in baza.columns and baza["Age when stroke"].notna().any():
    age_min = int(np.floor(baza["Age when stroke"].min()))
    age_max = int(np.ceil(baza["Age when stroke"].max()))
    if age_min == age_max:
        age_max += 1
    age_range = st.sidebar.slider("Age at stroke (years)", age_min, age_max, (age_min, age_max))
else:
    age_range = None

# Days between stroke and BoNT-A — unlocked only if "Yes" is among selected
days_col = "Days between stroke and BoNT-A"
yes_selected = True

if days_col in baza.columns and baza[days_col].notna().any():
    days_min = int(np.floor(baza[days_col].min(skipna=True)))
    days_max = int(np.ceil(baza[days_col].max(skipna=True)))
    if days_min == days_max:
        days_max += 1
    days_range = st.sidebar.slider(
        "Days between stroke and BoNT-A",
        days_min, days_max, (days_min, days_max)
    )
else:
    days_range = None

st.sidebar.markdown(
    f'<p class="small-note">Total patients in dataset: {TOTAL_N}</p>',
    unsafe_allow_html=True,
)

# --- Apply universal filters ---
filtered = baza.copy()

if earlier_sel is not None:
    filtered = filtered[filtered["Earlier BoNT-A treatment in legs"].isin(earlier_sel)]

if age_range is not None:
    filtered = filtered[filtered["Age when stroke"].between(age_range[0], age_range[1])]

if days_range is not None and yes_selected:
    # Keep rows within the day range, but never drop patients who simply
    # don't have a value here (e.g. "No" earlier treatment).
    mask = filtered[days_col].between(days_range[0], days_range[1]) | filtered[days_col].isna()
    filtered = filtered[mask]

N_FILTERED = filtered["Code"].nunique() if "Code" in filtered.columns else len(filtered)

st.sidebar.markdown(
    f'<p class="small-note">Patients matching filters: <b>{N_FILTERED}</b></p>',
    unsafe_allow_html=True,
)

if N_FILTERED == 0:
    st.warning("No patients match the current filters. Please widen the filter criteria in the sidebar.")
    st.stop()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("BoNT-A Spasticity Research Dashboard")
st.caption(
    f"{N_FILTERED} patients selected"
)

# ---------------------------------------------------------------------------
# Helper: hover template + color mapping for the individual line plots
# ---------------------------------------------------------------------------

HOVER_TEMPLATE = (
    "<b>Patient %{customdata[0]}</b><br>"
    "Timepoint: %{x}<br>"
    "Value: %{y}<br>"
    "Age at stroke: %{customdata[1]} years<br>"
    "Earlier BoNT-A in legs: %{customdata[3]}<br>"
    "Stroke → BoNT-A: %{customdata[4]} days"
    "<extra></extra>"
)
CUSTOMDATA_COLS = ["Code", "Age when stroke", "Side of stroke",
                    "Earlier BoNT-A treatment in legs", "Days between stroke and BoNT-A"]

SPAGHETTI_PALETTE = px.colors.qualitative.Dark24 + px.colors.qualitative.Light24


def build_color_map(codes):
    """Consistent color per patient Code, shared across linked panels."""
    codes = sorted(set(str(c) for c in codes))
    return {code: SPAGHETTI_PALETTE[i % len(SPAGHETTI_PALETTE)] for i, code in enumerate(codes)}


def make_error_bar_fig(long_df, value_name, title):
    summary = dl.summarize(long_df, value_name)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=summary["Timepoint"].astype(str),
        y=summary["mean"],
        error_y=dict(type="data", array=summary["std"].fillna(0), visible=True, thickness=1.5, width=6),
        mode="markers+lines",
        marker=dict(size=10, color="#2E5EAA"),
        line=dict(color="#2E5EAA", width=2),
        name="Mean ± SD",
        customdata=summary["count"],
        hovertemplate="Timepoint: %{x}<br>Mean: %{y:.2f}<br>n = %{customdata}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=PLOTLY_TITLE_FONT),
        xaxis_title="Timepoint", yaxis_title=value_name,
        font=PLOTLY_FONT, height=380, margin=dict(t=50, b=40),
    )
    return fig


def _spaghetti_figure(long_df, value_name, title, color_map, timepoints_order):
    """Builds a go.Figure with one trace per patient (trace name = Code),
    so that hover events expose the patient code and traces can be
    highlighted/dimmed individually via Plotly.restyle in the browser."""
    cd_cols = [c for c in CUSTOMDATA_COLS if c in long_df.columns]
    fig = go.Figure()
    for code, sub in long_df.groupby("Code", observed=True):
        sub = sub.sort_values("Timepoint")
        customdata = sub[cd_cols].astype(object).values.tolist() if cd_cols else None
        color = color_map.get(str(code), "#888888")
        fig.add_trace(go.Scatter(
            x=sub["Timepoint"].astype(str),
            y=sub[value_name],
            mode="lines+markers",
            name=str(code),
            line=dict(color=color, width=1.5),
            marker=dict(color=color, size=6),
            opacity=0.85,
            customdata=customdata,
            hovertemplate=HOVER_TEMPLATE,
            showlegend=False,
        ))
    fig.update_layout(
        title=dict(text=title, font=PLOTLY_TITLE_FONT),
        xaxis=dict(
            title="Timepoint",
            categoryorder="array",
            categoryarray=[str(t) for t in timepoints_order],
        ),
        yaxis_title=value_name,
        font=PLOTLY_FONT, height=380, margin=dict(t=50, b=40),
        hovermode="closest",
    )
    return fig


def make_box_fig(long_df, value_name, title):
    fig = px.box(long_df, x="Timepoint", y=value_name, points="all")
    fig.update_traces(marker=dict(size=5, opacity=0.6), boxmean=True)
    fig.update_layout(
        title=dict(text=title, font=PLOTLY_TITLE_FONT),
        xaxis_title="Timepoint", yaxis_title=value_name,
        font=PLOTLY_FONT, height=380, margin=dict(t=50, b=40),
    )
    return fig


def render_linked_line_charts(panels, height=380):
    """
    panels: list of (title, go.Figure) tuples — 1 (single) or 2 (side-by-side).
    Renders every figure inside ONE html component so that
    hovering a patient's line in any panel highlights that same patient's
    line in ALL panels, and dims every other line/point.
    """
    div_ids = [f"plotlydiv_{uuid.uuid4().hex[:8]}" for _ in panels]
    fig_jsons = [pio.to_json(fig) for _, fig in panels]
    titles = [t for t, _ in panels]

    divs_html = "".join(
        f'''
        <div style="flex:1; min-width:0;">
            <div class="panel-title">{titles[i]}</div>
            <div id="{div_ids[i]}" style="width:100%; height:{height}px;"></div>
        </div>
        '''
        for i in range(len(panels))
    )

    newplot_calls = "\n".join(
        f"var fig{i} = {fig_jsons[i]};\n"
        f"Plotly.newPlot('{div_ids[i]}', fig{i}.data, fig{i}.layout, {{responsive:true, displaylogo:false}});"
        for i in range(len(panels))
    )

    div_ids_js = json.dumps(div_ids)

    html = f"""
    <style>
        {FONT_IMPORTS}
        body {{ margin:0; font-family: 'Bookman Old Style', Georgia, serif; }}
        .row {{ display:flex; gap:20px; width:100%; }}
        .panel-title {{
            font-family: 'Bookman Old Style', Georgia, serif;
            font-size: 15px; font-weight: bold; margin-bottom: 4px;
        }}
    </style>
    <div class="row">{divs_html}</div>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <script>
    {newplot_calls}

    var allDivIds = {div_ids_js};

    function highlightCode(code) {{
        allDivIds.forEach(function(id) {{
            var gd = document.getElementById(id);
            if (!gd || !gd.data) return;
            var opacities = gd.data.map(function(tr) {{ return tr.name === code ? 1 : 0.06; }});
            var widths = gd.data.map(function(tr) {{ return tr.name === code ? 3.5 : 1; }});
            var sizes = gd.data.map(function(tr) {{ return tr.name === code ? 9 : 6; }});
            Plotly.restyle(id, {{'opacity': opacities, 'line.width': widths, 'marker.size': sizes}});
        }});
    }}

    function resetHighlight() {{
        allDivIds.forEach(function(id) {{
            var gd = document.getElementById(id);
            if (!gd || !gd.data) return;
            var opacities = gd.data.map(function() {{ return 0.85; }});
            var widths = gd.data.map(function() {{ return 1.5; }});
            var sizes = gd.data.map(function() {{ return 6; }});
            Plotly.restyle(id, {{'opacity': opacities, 'line.width': widths, 'marker.size': sizes}});
        }});
    }}

    allDivIds.forEach(function(id) {{
        var gd = document.getElementById(id);
        gd.on('plotly_hover', function(evt) {{
            if (evt.points && evt.points.length > 0) {{
                highlightCode(evt.points[0].data.name);
            }}
        }});
        gd.on('plotly_unhover', function(evt) {{
            resetHighlight();
        }});
    }});
    </script>
    """
    components.html(html, height=height + 55, scrolling=False)


def render_measurement(value_name, panels, plot_types, timepoints_order):
    """
    Unified renderer for one measurement.
    panels: list of (title, long_df) — length 1 (no split) or 2 (e.g.
    Affected / Non-Affected, Left / Right, PF / DF, AROM / PROM).
    """
    non_empty = [(t, d) for t, d in panels if not d.empty]
    if not non_empty:
        st.info("No data available for the current filters.")
        return

    n_cols = len(panels)

    # Patient-count captions
    cols = st.columns(n_cols, gap="large") if n_cols > 1 else [st.container()]
    for (title, df), col in zip(panels, cols):
        with col:
            n_patients = df["Code"].nunique() if not df.empty else 0
            st.markdown(
                f"**{title}**  \n<span class='small-note'>n = {n_patients} patients contributing data</span>",
                unsafe_allow_html=True,
            )

    if "Error Bars" in plot_types:
        cols = st.columns(n_cols, gap="large") if n_cols > 1 else [st.container()]
        for (title, df), col in zip(panels, cols):
            with col:
                if df.empty:
                    st.info(f"No data for '{title}'.")
                else:
                    st.plotly_chart(make_error_bar_fig(df, value_name, "Mean ± SD over time"), width='stretch', config={'scrollZoom': False})

    if "Individual Line Plot" in plot_types:
        all_codes = set()
        for _, df in panels:
            if not df.empty:
                all_codes.update(df["Code"].astype(str).unique())
        color_map = build_color_map(all_codes)

        figs = []
        for title, df in panels:
            if df.empty:
                continue
            fig_title = "Individual patient trajectories" if n_cols == 1 else f"Individual patient trajectories — {title}"
            fig = _spaghetti_figure(df, value_name, fig_title, color_map, timepoints_order)
            figs.append((title, fig))

        if figs:
            render_linked_line_charts(figs)
            st.markdown(
                "<span class='small-note'>Hover over a patient's line to highlight it and dim the rest</span>",
                unsafe_allow_html=True)

    if "Boxplot" in plot_types:
        cols = st.columns(n_cols, gap="large") if n_cols > 1 else [st.container()]
        for (title, df), col in zip(panels, cols):
            with col:
                if df.empty:
                    st.info(f"No data for '{title}'.")
                else:
                    st.plotly_chart(make_box_fig(df, value_name, "Distribution by timepoint"), width='stretch', config={'scrollZoom': False})


# ---------------------------------------------------------------------------
# Main — category & sub-filter selection
# ---------------------------------------------------------------------------

st.markdown("### Choose what to analyze")

CATEGORIES = [
    "Shear Wave Velocity",
    "Muscle Strength",
    "Range of Motion",
    "Spasticity",
    "10 Meter Walk Test",
    "GAS",
    "Muscle Volume (mm³)",
    "Fat Volume (mm³)",
    "Fat Percentage (%)"
]

col_a, col_b, col_c = st.columns([2, 1, 2])
with col_a:
    category = st.selectbox("Measurements", CATEGORIES)
with col_c:
    plot_types = st.multiselect(
        "Chart types",
        ["Error Bars", "Individual Line Plot", "Boxplot"],
        default=["Error Bars", "Individual Line Plot", "Boxplot"],
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Category-specific rendering
# ---------------------------------------------------------------------------

if not plot_types:
    st.info("Select at least one chart type above to see results.")
    st.stop()


elif category == "Shear Wave Velocity":
    c1, c2 = st.columns(2)
    with c1:
        muscle = st.selectbox("Muscle", dl.MUSCLES, format_func=lambda m: "Gastrocnemius Medialis (GM)" if m == "GM" else "Tibialis Anterior (TA)")
    with c2:
        position = st.selectbox("Measurement position", dl.POSITIONS)
    value_name = "SWV (m/s)"
    non_aff_long = dl.to_long(filtered, dl.swv_timepoint_map("Non Affected", muscle, position), dl.TIMEPOINTS_FULL, value_name)
    aff_long = dl.to_long(filtered, dl.swv_timepoint_map("Affected", muscle, position), dl.TIMEPOINTS_FULL, value_name)
    render_measurement(value_name, [("Non-affected side", non_aff_long), ("Affected side", aff_long)], plot_types, dl.TIMEPOINTS_FULL)

elif category == "Muscle Strength":
    value_name = "Muscle strength"
    pf_long = dl.to_long(filtered, dl.mstr_timepoint_map("PF"), dl.TIMEPOINTS_FULL, value_name)
    df_long = dl.to_long(filtered, dl.mstr_timepoint_map("DF"), dl.TIMEPOINTS_FULL, value_name)
    render_measurement(value_name, [("Plantarflexion (PF)", pf_long), ("Dorsiflexion (DF)", df_long)], plot_types, dl.TIMEPOINTS_FULL)

elif category == "Range of Motion":
    value_name = "Range of Motion (°)"
    arom_long = dl.to_long(filtered, dl.arom_prom_timepoint_map("AROM"), dl.TIMEPOINTS_FULL, value_name)
    prom_long = dl.to_long(filtered, dl.arom_prom_timepoint_map("PROM"), dl.TIMEPOINTS_FULL, value_name)
    render_measurement(value_name, [("Active ROM (AROM)", arom_long), ("Passive ROM (PROM)", prom_long)], plot_types, dl.TIMEPOINTS_FULL)

elif category == "Spasticity":
    st.caption("Grade '1+' is recoded to 1.5 for numerical display and plotting.")
    value_name = "Modified Heckmatt Scale"
    long_df = dl.to_long(filtered, dl.spasticity_timepoint_map(), dl.TIMEPOINTS_FULL, value_name)
    render_measurement(value_name, [("Spasticity (Plantarflexors)", long_df)], plot_types, dl.TIMEPOINTS_FULL)

elif category == "10 Meter Walk Test":
    value_name = "10MWT (m/s)"
    long_df = dl.to_long(filtered, dl.mwt_timepoint_map(), dl.TIMEPOINTS_FULL, value_name)
    render_measurement(value_name, [("10 Meter Walk Test", long_df)], plot_types, dl.TIMEPOINTS_FULL)

elif category == "GAS":
    value_name = "GAS score"
    long_df = dl.to_long(filtered, dl.gas_timepoint_map(), dl.TIMEPOINTS_FULL, value_name)
    render_measurement(value_name, [("Goal Attainment Scaling", long_df)], plot_types, dl.TIMEPOINTS_FULL)

elif category == "Muscle Volume (mm³)":
    muscle = st.selectbox("Muscle", dl.MUSCLES, format_func=lambda m: "Gastrocnemius Medialis (GM)" if m == "GM" else "Tibialis Anterior (TA)")
    value_name = "Volume (mm³)"
    non_aff_long = dl.to_long(filtered, dl.vf_timepoint_map("Volume (mm3)", "Non Affected", muscle), dl.TIMEPOINTS_SHORT, value_name)
    aff_long = dl.to_long(filtered, dl.vf_timepoint_map("Volume (mm3)", "Affected", muscle), dl.TIMEPOINTS_SHORT, value_name)
    render_measurement(value_name, [("Non-affected side", non_aff_long), ("Affected side", aff_long)], plot_types, dl.TIMEPOINTS_SHORT)

elif category == "Fat Percentage (%)":
    muscle = st.selectbox("Muscle", dl.MUSCLES, format_func=lambda m: "Gastrocnemius Medialis (GM)" if m == "GM" else "Tibialis Anterior (TA)")
    value_name = "Fat (%)"
    non_aff_long = dl.to_long(filtered, dl.vf_timepoint_map("Fat (%)", "Non Affected", muscle), dl.TIMEPOINTS_SHORT, value_name)
    aff_long = dl.to_long(filtered, dl.vf_timepoint_map("Fat (%)", "Affected", muscle), dl.TIMEPOINTS_SHORT, value_name)
    render_measurement(value_name, [("Non-affected side", non_aff_long), ("Affected side", aff_long)], plot_types, dl.TIMEPOINTS_SHORT)

elif category == "Fat Volume (mm³)":
    muscle = st.selectbox("Muscle", dl.MUSCLES, format_func=lambda m: "Gastrocnemius Medialis (GM)" if m == "GM" else "Tibialis Anterior (TA)")
    value_name = "Fat (mm³)"
    non_aff_long = dl.to_long(filtered, dl.vf_timepoint_map("Fat (mm3)", "Non Affected", muscle), dl.TIMEPOINTS_SHORT, value_name)
    aff_long = dl.to_long(filtered, dl.vf_timepoint_map("Fat (mm3)", "Affected", muscle), dl.TIMEPOINTS_SHORT, value_name)
    render_measurement(value_name, [("Non-affected side", non_aff_long), ("Affected side", aff_long)], plot_types, dl.TIMEPOINTS_SHORT)
