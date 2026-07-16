"""
dashboard_logic.py
-------------------
Data-handling logic for the BoNT-A / Post-Stroke Spasticity Research Dashboard.
Kept separate from the Streamlit UI (app.py) so the wide->long transformations
and column-name lookups can be tested independently of Streamlit.

The source dataset ("baza") is in WIDE format: one row per patient (Code),
one column per (measurement x timepoint x sub-dimension) combination.
This module turns a chosen slice of that wide table into a tidy LONG table:

    Code | Timepoint | Value | <patient info columns for hover/tooltip>

which is what Plotly needs for error-bar / spaghetti / boxplot charts.
"""

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIMEPOINTS_FULL = ["Baseline", "6 Weeks", "3 Months", "6 Months", "9 Months", "12 Months"]
TIMEPOINTS_SHORT = ["Baseline", "12 Months"]

SIDES = ["Non Affected", "Affected"]
MUSCLES = ["GM", "TA"]
POSITIONS = ["Max PF", "Max DF", "30 PF"]

# Patient-level fields used for the universal sidebar filters. These are also
# carried along into every long-format table so they can be shown on hover.
PATIENT_INFO_COLS = [
    "Code",
    "Age when stroke",
    "Side of stroke",
    "Earlier BoNT-A treatment in legs",
    "Days between stroke and BoNT-A",
]

# The real column names have a couple of inconsistent spacings around "30 PF"
# vs "30PF" in the source spreadsheet. This set captures every
# (side, muscle, timepoint) combo where the source uses "30PF" (no space)
# instead of the regular "30 PF" (with space). Verified against the actual
# column list.
NO_SPACE_30PF = {
    ("Non Affected", "GM", "9 Months"),
    ("Non Affected", "TA", "9 Months"),
    ("Affected", "GM", "9 Months"),
    ("Affected", "TA", "9 Months"),
    ("Non Affected", "GM", "12 Months"),
}


# ---------------------------------------------------------------------------
# Column-name builders (map logical dimensions -> exact spreadsheet column)
# ---------------------------------------------------------------------------

def swv_col(side: str, muscle: str, timepoint: str, position: str) -> str:
    """Shear Wave Velocity column name."""
    pos = position
    if position == "30 PF" and (side, muscle, timepoint) in NO_SPACE_30PF:
        pos = "30PF"
    return f"{side} {muscle} {timepoint} {pos}"


def vf_col(measure: str, timepoint: str, side: str, muscle: str) -> str:
    """Volume (mm3) / Fat (%) / Fat (mm3) column name."""
    return f"{measure} {timepoint} {side} {muscle}"


def eq5d_col(timepoint: str, lr: str) -> str:
    return f"EQ-5D-5L {timepoint} {lr}"


def mstr_col(timepoint: str, pfdf: str) -> str:
    return f"Muscle strength {timepoint} {pfdf}"


def arom_col(timepoint: str) -> str:
    return f"AROM {timepoint}"


def prom_col(timepoint: str) -> str:
    return f"PROM {timepoint}"


def spast_col(timepoint: str) -> str:
    return f"Spasticity PF {timepoint}"


def mwt_col(timepoint: str) -> str:
    return f"10MWT {timepoint}"


def gas_col(timepoint: str) -> str:
    return f"GAS {timepoint}"


# ---------------------------------------------------------------------------
# Recoding helpers
# ---------------------------------------------------------------------------

def recode_spasticity(series: pd.Series) -> pd.Series:
    """Modified scale values such as '1+' are recoded to 1.5 for plotting."""
    s = series.astype(str).str.strip()
    s = s.replace({"1+": "1.5", "nan": np.nan, "None": np.nan, "": np.nan})
    return pd.to_numeric(s, errors="coerce")


# ---------------------------------------------------------------------------
# Wide -> long melting
# ---------------------------------------------------------------------------

def to_long(df: pd.DataFrame, timepoint_to_col: dict, timepoints_order: list,
            value_name: str = "Value", recode_fn=None) -> pd.DataFrame:
    """
    Build a tidy long dataframe for ONE panel (e.g. one side / one AROM-PROM arm).

    timepoint_to_col: {timepoint_label: source_column_name}
    recode_fn: optional function applied to the raw value Series before
               converting to numeric (used for the spasticity 1+ -> 1.5 recode)
    """
    id_vars = [c for c in PATIENT_INFO_COLS if c in df.columns]
    frames = []
    for tp in timepoints_order:
        col = timepoint_to_col.get(tp)
        if col is None or col not in df.columns:
            continue
        sub = df[id_vars + [col]].copy()
        raw = sub[col]
        if recode_fn is not None:
            raw = recode_fn(raw)
        else:
            raw = pd.to_numeric(raw, errors="coerce")
        sub = sub.drop(columns=[col])
        sub[value_name] = raw
        sub["Timepoint"] = tp
        frames.append(sub)

    if not frames:
        return pd.DataFrame(columns=id_vars + ["Timepoint", value_name])

    long_df = pd.concat(frames, ignore_index=True)
    long_df["Timepoint"] = pd.Categorical(long_df["Timepoint"], categories=timepoints_order, ordered=True)
    long_df = long_df.dropna(subset=[value_name]).reset_index(drop=True)
    return long_df


def summarize(long_df: pd.DataFrame, value_name: str = "Value") -> pd.DataFrame:
    """Mean / SD / N per timepoint, respecting the categorical timepoint order."""
    if long_df.empty:
        return pd.DataFrame(columns=["Timepoint", "mean", "std", "count"])
    g = long_df.groupby("Timepoint", observed=True)[value_name].agg(["mean", "std", "count"]).reset_index()
    g = g.sort_values("Timepoint")
    return g


# ---------------------------------------------------------------------------
# Column maps per category / sub-selection (used directly by the UI)
# ---------------------------------------------------------------------------

def swv_timepoint_map(side: str, muscle: str, position: str) -> dict:
    return {tp: swv_col(side, muscle, tp, position) for tp in TIMEPOINTS_FULL}


def vf_timepoint_map(measure: str, side: str, muscle: str) -> dict:
    return {tp: vf_col(measure, tp, side, muscle) for tp in TIMEPOINTS_SHORT}


def eq5d_timepoint_map(lr: str) -> dict:
    return {tp: eq5d_col(tp, lr) for tp in TIMEPOINTS_SHORT}


def mstr_timepoint_map(pfdf: str) -> dict:
    return {tp: mstr_col(tp, pfdf) for tp in TIMEPOINTS_FULL}


def arom_prom_timepoint_map(kind: str) -> dict:
    fn = arom_col if kind == "AROM" else prom_col
    return {tp: fn(tp) for tp in TIMEPOINTS_FULL}


def spasticity_timepoint_map() -> dict:
    return {tp: spast_col(tp) for tp in TIMEPOINTS_FULL}


def mwt_timepoint_map() -> dict:
    return {tp: mwt_col(tp) for tp in TIMEPOINTS_FULL}


def gas_timepoint_map() -> dict:
    return {tp: gas_col(tp) for tp in TIMEPOINTS_FULL}
