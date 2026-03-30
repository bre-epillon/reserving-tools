import streamlit as st
from services.transactions_importer import TransactionsImporter
from presentation.state.session_state_manager import initialize_session_state
from shared.colored_logging import info, warning, error, debug, success
from shared.utils import get_sidebar
import pandas as pd
import numpy as np
import json
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode


st.set_page_config(page_title="Last Quarter Movements", page_icon="📈", layout="wide")

initialize_session_state()

st.title("Last Quarter Movements")

get_sidebar()


st.write(
    "This page provides an overview of the quarterly movements for each line of business (LoB), both at the claim level and policy level."
)

transactions_importer = TransactionsImporter(st.session_state.transactions_data)
transactions_data = transactions_importer.get_transactions()

# with st.expander("Data Selection Override"):
#     col1, col2 = st.columns(2)
#     with col1:
#         st.selectbox(
#             "Select cutoff date",
#             options=[i for i in range(1, 5)],
#             key="selected_quarter",
#             index=int(st.session_state.get("selected_quarter", 1)) - 1,
#         )
#     with col2:
#         st.selectbox(
#             "Select comparison date",
#             options=[i for i in range(2017, 2027)],
#             key="selected_year",
#             index=int(st.session_state.get("selected_year", 2026)) - 2017,
#         )


# SELECTED_QUARTER = st.session_state.get("selected_quarter", None)
LAST_QUARTER_STR = transactions_importer.get_last_quarter()

last_quarter_data = transactions_importer.get_last_quarter_data()

st.write(f"Data is available up to: **{LAST_QUARTER_STR}**")

COMMENTS_FILE = f"comments_{LAST_QUARTER_STR}.json"
debug(f"Comments file set to: {COMMENTS_FILE}")


# df = df[df["Measure"].isin(["GClmO", "GClmP"])]
with st.expander("Supporting Selection Filters"):
    col1, col2 = st.columns(2)
    with col1:
        lob_selector = st.multiselect(
            "Select LOB (if not selected, all will be selected)",
            options=last_quarter_data["LOB"].unique(),
            key="selected_lob",
            default=last_quarter_data["LOB"].unique(),
        )

    with col2:
        uwy_selector = st.multiselect(
            "Select UWY (if not selected, all will be selected)",
            options=last_quarter_data["UWY"].unique(),
            key="selected_uwy",
            default=last_quarter_data["UWY"].unique(),
        )

# df = df[df["LOB"].isin(lob_selector) & df["UWY"].isin(uwy_selector)]
# # Split data
# df_total = df.copy()

info(
    f"Data filtered for last quarter ({LAST_QUARTER_STR}) has shape: {last_quarter_data.shape}"
)

st.info(
    f"{last_quarter_data.shape[0]} entries have been found in the last quarter movements"
)

# Pivot table for last quarter
result = last_quarter_data.pivot_table(
    index=["LOB", "UWY"],
    columns="Measure",
    values="value",
    aggfunc="sum",
    fill_value=0,
).reset_index()

# # Merge them
# result = pivot_total.merge(
#     pivot_last, on=["LOB", "UWY"], suffixes=("_Total", "_LastMonth"), how="left"
# ).fillna(0)

# # Sum all columns ending with _Total and _LastMonth
# total_cols = [col for col in result.columns if col.endswith("_Total")]
# lastmonth_cols = [col for col in result.columns if col.endswith("_LastMonth")]

# result["Incurred_Total"] = result[total_cols].sum(axis=1)
# result["Incurred_LastMonth"] = result[lastmonth_cols].sum(axis=1)


# Format number columns in thousands with 'k' suffix
def format_thousands_colored(val):
    return val
    if isinstance(val, (int, float, np.integer, np.floating)):
        if val == 0:
            return ""
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
    if col != "UWY":  # Avoid formatting UWY
        debug(f"Formatting column: {col}")
        result_formatted[col] = result_formatted[col].apply(format_thousands_colored)


# =============================================================
# Loading comments and annotations
def load_comments():
    try:
        info(f"Loading comments from '{COMMENTS_FILE}'...")
        with open(COMMENTS_FILE, "r") as f:
            success(f"Comments file '{COMMENTS_FILE}' loaded successfully.")
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


df_comments = (
    pd.DataFrame.from_dict(comments_data[LAST_QUARTER_STR])
    if LAST_QUARTER_STR in comments_data
    else pd.DataFrame(columns=["LOB", "UWY", "Comment"])
)

# =============================================================
# Merge comments with result_formatted using UWY and LOB
merged_result = pd.merge(
    result_formatted,
    df_comments,
    left_on=["LOB", "UWY"],
    right_on=["LOB", "UWY"],
    how="left",
)

merged_result[["GClmO", "GClmP", "GGWP"]] = merged_result[
    ["GClmO", "GClmP", "GGWP"]
].map(lambda x: int(x) if isinstance(x, (int, float)) else x)

merged_result_2 = pd.merge(
    result,
    df_comments,
    left_on=["LOB", "UWY"],
    right_on=["LOB", "UWY"],
    how="left",
)

st.dataframe(
    merged_result[["LOB", "UWY", "GClmO", "GClmP", "GGWP", "Comment"]],
    width="stretch",
)

# st.write(merged_result.to_html(escape=False, index=False), unsafe_allow_html=True)

# Section for adding/editing comments per LOB and UWY
st.write("### Add or Edit Comments")

# Prepare a dict to collect new/edited comments
updated_comments = comments_data.copy()
quarter_key = (
    LAST_QUARTER_STR.strftime("%YQ%q")
    if hasattr(LAST_QUARTER_STR, "strftime")
    else str(LAST_QUARTER_STR)
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
        with open(COMMENTS_FILE, "w") as f:
            debug(f"Saving comments into `{COMMENTS_FILE}`: {updated_comments}")
            json.dump(updated_comments, f, indent=2)
        success("Comments saved successfully.")
    except Exception as e:
        error(f"Failed to save comments: {e}")

gb = GridOptionsBuilder.from_dataframe(result)

# 3. Write your formatting logic in JavaScript (JsCode)
# This perfectly mimics your format_thousands_colored Python function
number_formatter = JsCode("""
function(params) {
    if (params.value === null || params.value === undefined || params.value === 0) {
        return "";
    }
    return (params.value / 1000).toLocaleString('en-US', {
        minimumFractionDigits: 1, 
        maximumFractionDigits: 1
    }) + "k";
}
""")

# 2. Javascript for purely setting the CSS styling
color_style = JsCode("""
function(params) {
    if (params.value === null || params.value === undefined || params.value === 0) {
        return null; // Default style
    }
    if (params.value >= 0) {
        return {'color': 'green'};
    } else {
        return {'color': 'red'};
    }
}
""")

columns_to_format = [
    "GBrok",
    "GClmO",
    "GClmP",
    "GDed",
    "GGWP",
    "GPrmB",
    "GPrmR",
    "Gbrok",
]

# 3. Apply BOTH the formatter and the style to your columns
for col in columns_to_format:
    gb.configure_column(col, valueFormatter=number_formatter, cellStyle=color_style)

gridOptions = gb.build()

# 4. Render the grid
AgGrid(
    result,
    gridOptions=gridOptions,
    allow_unsafe_jscode=True,
    height=600,
)


st.write("### Imported Data Summary")
toggle_button = st.checkbox(
    "Toggle data selection for last quarter", value=False, key="toggle_last_quarter"
)

if toggle_button:
    df = transactions_importer.data[
        (
            transactions_importer.data["Measure"].isin(
                ["GClmO", "GClmP", "GGWP", "GPrmB"]
            )
        )
        & (transactions_importer.data["date"] > LAST_QUARTER_STR)
    ]
else:
    df = transactions_importer.data[
        transactions_importer.data["Measure"].isin(["GClmO", "GClmP", "GGWP", "GPrmB"])
    ]

st.write("## Policy Level Summary")
policy_pivotdata = df.pivot_table(
    index=["PolicyReference", "LOB", "UWY"],
    columns="Measure",
    values="value",
    aggfunc="sum",
    fill_value=0,
).reset_index()

gb = GridOptionsBuilder.from_dataframe(policy_pivotdata)
gb.configure_default_column(filter=True)

for col in ["GClmO", "GClmP", "GGWP", "GPrmB"]:
    gb.configure_column(col, valueFormatter=number_formatter, cellStyle=color_style)

gridOptions = gb.build()

# 4. Render the grid
AgGrid(
    policy_pivotdata,
    gridOptions=gridOptions,
    allow_unsafe_jscode=True,
    height=600,
)

st.write("## Claim Level Summary")
claim_pivotdata = df.pivot_table(
    index=["ClaimReference", "LOB", "UWY"],
    columns="Measure",
    values="value",
    aggfunc="sum",
    fill_value=0,
).reset_index()

gb = GridOptionsBuilder.from_dataframe(claim_pivotdata)
gb.configure_default_column(filter=True)

for col in ["GClmO", "GClmP", "GGWP", "GPrmB"]:
    gb.configure_column(col, valueFormatter=number_formatter, cellStyle=color_style)

gridOptions = gb.build()

# 4. Render the grid
AgGrid(
    claim_pivotdata,
    gridOptions=gridOptions,
    allow_unsafe_jscode=True,
    height=600,
)
