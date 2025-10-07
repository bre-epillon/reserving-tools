import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.narratives import USAGE, DETAILS, NAVIGATION, DISCLAIMER
from shared.colored_logging import info, warning, error, debug, success
import pandas as pd
import numpy as np
import json

st.set_page_config(page_title="Last Quarter Movements", page_icon="📈", layout="wide")

initialize_session_state()

st.title("Last Quarter Movements")
st.sidebar.title("Navigation")
st.sidebar.markdown(NAVIGATION)

st.sidebar.title("Usage Instructions")
st.sidebar.markdown(USAGE)

st.sidebar.title("Details")
st.sidebar.markdown(DETAILS)

st.sidebar.title("Disclaimer")
st.sidebar.markdown(DISCLAIMER)


st.write(
    "This page provides an overview of the quarterly movements for each line of business (LoB), both at the claim level and policy level."
)

df = st.session_state.transactions_data.copy()

df.drop(columns=["LOB"], inplace=True)
df.rename(columns={"Final LOB": "LOB"}, inplace=True)

df["date"] = pd.to_datetime(df["CutOffDate"])
df = df[df["Measure"].isin(["GClmO", "GClmP"])]

last_quarter = df["date"].max().to_period("Q")
mask_last_quarter = df["date"].dt.to_period("Q") == last_quarter

st.write(f"Data is available up to: **{last_quarter}**")


with st.expander("Supporting Selection Filters"):
    col1, col2 = st.columns(2)
    with col1:
        lob_selector = st.multiselect(
            "Select LOB (if not selected, all will be selected)",
            options=df["LOB"].unique(),
            key="selected_lob",
            default=df["LOB"].unique(),
        )

    with col2:
        uwy_selector = st.multiselect(
            "Select UWY (if not selected, all will be selected)",
            options=df["UWY"].unique(),
            key="selected_uwy",
            default=df["UWY"].unique(),
        )


df = df[df["LOB"].isin(lob_selector) & df["UWY"].isin(uwy_selector)]
# Split data
df_total = df.copy()

df_last_quarter = df.loc[mask_last_quarter].copy()


# Pivot table for totals
pivot_total = df_total.pivot_table(
    index=["LOB", "UWY"],
    columns="Measure",
    values="value",
    aggfunc="sum",
    fill_value=0,
).reset_index()

# Pivot table for last month
pivot_last = df_last_quarter.pivot_table(
    index=["LOB", "UWY"],
    columns="Measure",
    values="value",
    aggfunc="sum",
    fill_value=0,
).reset_index()

# Merge them
result = pivot_total.merge(
    pivot_last, on=["LOB", "UWY"], suffixes=("_Total", "_LastMonth"), how="left"
).fillna(0)

# Sum all columns ending with _Total and _LastMonth
total_cols = [col for col in result.columns if col.endswith("_Total")]
lastmonth_cols = [col for col in result.columns if col.endswith("_LastMonth")]

result["Incurred_Total"] = result[total_cols].sum(axis=1)
result["Incurred_LastMonth"] = result[lastmonth_cols].sum(axis=1)


# Format number columns in thousands with 'k' suffix
def format_thousands_colored(val):
    if isinstance(val, (int, float, np.integer, np.floating)):
        color = "green" if val >= 0 else "red"
        return f'<span style="color:{color}">{val / 1000:,.1f}k</span>'
    return val


def format_thousands(val):
    if isinstance(val, (int, float, np.integer, np.floating)):
        return f"{val / 1000:,.1f}k"
    return val


number_cols = result.select_dtypes(include=[np.number]).columns
result_formatted = result.copy()
for col in number_cols:
    if col != "UWY":  # Avoid formatting UWY which is year
        if col.endswith("_Total"):
            result_formatted[col] = result_formatted[col].apply(format_thousands)
        elif col.endswith("_LastMonth"):
            result_formatted[col] = result_formatted[col].apply(
                format_thousands_colored
            )


# =============================================================
# Loading comments and annotations
def load_comments():
    COMMENTS_FILE = "comments.json"
    try:
        with open(COMMENTS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        warning(f"Comments file '{COMMENTS_FILE}' not found. Returning empty comments.")
        return {}
    except json.JSONDecodeError:
        error(
            f"Comments file '{COMMENTS_FILE}' contains invalid JSON. Returning empty comments."
        )
        return {}


comments_data = load_comments()

df_comments = pd.DataFrame.from_dict(comments_data["2025Q3"])
# =============================================================
# Merge comments with result_formatted using UWY and LOB
merged_result = pd.merge(
    result_formatted,
    df_comments,
    left_on=["LOB", "UWY"],
    right_on=["LOB", "UWY"],
    how="left",
)


st.write(merged_result.to_html(escape=False, index=False), unsafe_allow_html=True)

# Section for adding/editing comments per LOB and UWY
st.write("### Add or Edit Comments")

# Prepare a dict to collect new/edited comments
updated_comments = comments_data.copy()
quarter_key = (
    last_quarter.strftime("%YQ%q")
    if hasattr(last_quarter, "strftime")
    else str(last_quarter)
)

if quarter_key not in updated_comments:
    updated_comments[quarter_key] = {}

# For each row in the result, show a text_area for comments
for idx, row in result[["LOB", "UWY"]].iterrows():
    lob = row["LOB"]
    uwy = row["UWY"]
    comment_key = f"{lob}_{uwy}"
    # Get existing comment if any
    existing_comment = ""
    if quarter_key in comments_data:
        for entry in comments_data[quarter_key]:
            if entry.get("LOB") == lob and entry.get("UWY") == uwy:
                existing_comment = entry.get("Comment", "")
                break

    comment = st.text_area(
        f"Comment for LOB: {lob}, UWY: {uwy}",
        value=existing_comment,
        key=f"comment_{lob}_{uwy}",
        height=60,
    )

    # Store in updated_comments
    if quarter_key not in updated_comments:
        updated_comments[quarter_key] = []
    # Remove any existing entry for this LOB/UWY
    updated_comments[quarter_key] = [
        entry
        for entry in updated_comments[quarter_key]
        if not (entry.get("LOB") == lob and entry.get("UWY") == uwy)
    ]
    # Add the new/edited comment
    updated_comments[quarter_key].append({"LOB": lob, "UWY": uwy, "Comment": comment})

# Save button
if st.button("Save Comments"):
    try:
        info("Saving comments...")
        with open("comments.json", "w") as f:
            debug("Saving comments into `comments.json`")
            json.dump(updated_comments, f, indent=2)
        success("Comments saved successfully.")
    except Exception as e:
        error(f"Failed to save comments: {e}")
